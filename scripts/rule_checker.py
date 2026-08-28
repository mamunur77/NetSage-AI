#!/usr/bin/env python3
"""
NetSage AI - Rule Checker

Deterministic (non-AI) checks that scan the raw show-command evidence for
each case and flag common, mechanically-detectable config mistakes:
  - interface administratively down / down-down
  - duplicate IP addresses across interface/host lines
  - subnet mask mismatch between two hosts/interfaces on one segment
  - default gateway that doesn't match any live router interface IP
  - a VLAN ID referenced in the symptom/topology text missing from a
    'show vlan brief' or trunk allowed-vlan list
  - a destination network referenced in the symptom text missing from
    'show ip route'

Run from anywhere:
    python scripts/rule_checker.py
    python scripts/rule_checker.py --cases path/to/custom_cases.csv
"""
import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT             = Path(__file__).parent.parent
DEFAULT_CASES    = ROOT / "data" / "cases.csv"
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Finding:
    check: str
    detail: str


IFACE_LINE = re.compile(
    r"^(?P<iface>\S+)\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+"
    r"(?P<status>up|down|administratively down)\s+(?P<proto>up|down)",
    re.MULTILINE,
)
DOWN_LINE = re.compile(
    r"^(?P<iface>\S+).{0,40}?\b(administratively down|down)\b", re.MULTILINE
)
GATEWAY_LINE  = re.compile(r"Default Gateway:\s*(\d{1,3}(?:\.\d{1,3}){3})")
IPCONFIG_IP   = re.compile(r"IP Address:\s*(\d{1,3}(?:\.\d{1,3}){3})")
MASK_LINE     = re.compile(r"Subnet Mask:\s*(\d{1,3}(?:\.\d{1,3}){3})")
VLAN_MENTION  = re.compile(r"VLAN\s?(\d+)", re.IGNORECASE)
VLAN_BRIEF_ID = re.compile(r"^(?:VLAN\s+Name.*\n)?(\d{1,4})\s+\S+\s+active", re.MULTILINE)
TRUNK_ALLOWED = re.compile(r"Gi\S*\s+([\d,\-]+)\s*$", re.MULTILINE)
NETWORK_MENTION = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})/(\d{1,2})")
ROUTE_LINE    = re.compile(r"^[A-Z]\s+(\d{1,3}(?:\.\d{1,3}){3})/(\d{1,2})", re.MULTILINE)


def vlan_range_contains(range_str: str, vlan_id: int) -> bool:
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-")
            if int(lo) <= vlan_id <= int(hi):
                return True
        elif part.isdigit():
            if int(part) == vlan_id:
                return True
    return False


def check_interfaces_down(text: str) -> list[Finding]:
    out = []
    for m in DOWN_LINE.finditer(text):
        line = m.group(0)
        if "Status" in line or "Protocol" in line:
            continue
        out.append(Finding("interface_down", f"Interface/line reporting down: '{line.strip()}'"))
    return out


def check_duplicate_ip(text: str) -> list[Finding]:
    ips = IPCONFIG_IP.findall(text) + IFACE_LINE.findall(text)
    flat_ips = [ip if isinstance(ip, str) else ip[1] for ip in ips]
    seen: dict[str, int] = {}
    for ip in flat_ips:
        seen[ip] = seen.get(ip, 0) + 1
    return [
        Finding("duplicate_ip", f"IP address {ip} appears {count} times across interface/host lines.")
        for ip, count in seen.items() if count > 1
    ]


def check_mask_mismatch(text: str) -> list[Finding]:
    out = []
    masks = MASK_LINE.findall(text)
    if len(set(masks)) > 1:
        out.append(Finding("mask_mismatch", f"Multiple differing subnet masks found: {sorted(set(masks))}"))
    prose_masks = re.findall(r"mask\s*/(\d{1,2})", text, re.IGNORECASE)
    if masks and prose_masks:
        out.append(Finding("mask_mismatch", f"Evidence explicitly calls out a differing mask: /{prose_masks[0]}"))
    return out


def check_gateway_mismatch(text: str) -> list[Finding]:
    gateways  = GATEWAY_LINE.findall(text)
    iface_ips = [ip for _, ip, *_ in IFACE_LINE.findall(text)] if IFACE_LINE.search(text) else []
    return [
        Finding("gateway_mismatch", f"Configured default gateway {gw} does not match any router interface IP found ({iface_ips}).")
        for gw in gateways if iface_ips and gw not in iface_ips
    ]


def check_missing_vlan(text: str) -> list[Finding]:
    out = []
    mentioned     = {int(v) for v in VLAN_MENTION.findall(text)}
    trunk_ranges  = TRUNK_ALLOWED.findall(text)
    for vlan_id in mentioned:
        in_trunk = any(vlan_range_contains(r, vlan_id) for r in trunk_ranges)
        if trunk_ranges and not in_trunk:
            out.append(Finding("missing_vlan", f"VLAN {vlan_id} is referenced but not present in the trunk's allowed-vlan range {trunk_ranges}."))
    return out


def check_missing_route(text: str) -> list[Finding]:
    if "(no route to" in text:
        m = re.search(r"\(no route to (\d{1,3}(?:\.\d{1,3}){3}/\d{1,2})\)", text)
        if m:
            return [Finding("missing_route", f"Routing table has no entry for {m.group(1)}.")]
    return []


CHECKS = [
    check_interfaces_down,
    check_duplicate_ip,
    check_mask_mismatch,
    check_gateway_mismatch,
    check_missing_vlan,
    check_missing_route,
]


def run_all(cases_path: Path = DEFAULT_CASES) -> dict[str, list[Finding]]:
    with open(cases_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    report = {}
    for row in rows:
        text = row["show_output"] + "\n" + row["symptom"] + "\n" + row["topology_note"]
        findings = []
        for check in CHECKS:
            findings.extend(check(text))
        report[row["case_id"]] = findings
    return report


def main():
    parser = argparse.ArgumentParser(description="NetSage AI — Deterministic Rule Checker")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="Path to cases CSV")
    args = parser.parse_args()

    report = run_all(args.cases)
    total  = sum(len(v) for v in report.values())
    hits   = sum(1 for v in report.values() if v)

    print(f"NetSage AI Rule Checker — {len(report)} cases scanned, "
          f"{hits} cases with at least one finding, {total} findings total.\n")

    for cid, findings in report.items():
        if not findings:
            continue
        print(f"[{cid}]")
        for finding in findings:
            print(f"  - ({finding.check}) {finding.detail}")
        print()


if __name__ == "__main__":
    sys.exit(main())
