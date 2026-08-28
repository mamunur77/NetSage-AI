#!/usr/bin/env python3
"""
Builds two demo artifacts without needing live API access:

1. data/sample_ai_responses.csv  - plausible AI responses for all 30 cases.
2. data/review_log.csv           - human reviewer verdicts (Accepted / Edited / Rejected).

Six cases are deliberately written as AI mistakes so the Responsible AI log
has real, explained corrections. When ai_diagnose.py runs for real, it
replaces sample_ai_responses.csv with ai_responses.csv in outputs/.

Usage:
    python scripts/generate_ai_and_review.py
"""
import csv
import json
from pathlib import Path

ROOT             = Path(__file__).parent.parent
CASES_CSV        = ROOT / "data" / "cases.csv"
SAMPLE_RESP_CSV  = ROOT / "data" / "sample_ai_responses.csv"
REVIEW_LOG_CSV   = ROOT / "data" / "review_log.csv"

with open(CASES_CSV, newline="", encoding="utf-8") as f:
    cases = {row["case_id"]: row for row in csv.DictReader(f)}

# case_id -> AI response (mostly mirrors expected_fault = "correct")
AI = {}
for cid, row in cases.items():
    AI[cid] = {
        "case_id": cid,
        "root_cause": row["expected_fault"],
        "osi_layer": row["osi_layer"],
        "confidence": "high",
        "evidence": "Directly supported by the show-command output provided for this case.",
        "next_command": "none - evidence sufficient",
        "fix_steps": ["Apply the corrective config change", "Re-run the relevant show command to verify", "Confirm with end-to-end ping/test"],
    }

# ---- Deliberate AI mistakes (6 cases) ----

AI["C004"]["root_cause"] = "Switchport Fa0/8 is misconfigured in the wrong VLAN, blocking the PC from the Guest network."
AI["C004"]["confidence"] = "high"
AI["C004"]["evidence"] = "show vlan brief lists Fa0/8 under VLAN 30, which the AI misread as a mismatch with the PC's observed IP."
AI["C004"]["next_command"] = "none - evidence sufficient"
AI["C004"]["fix_steps"] = ["Move Fa0/8 into VLAN 30 with 'switchport access vlan 30'", "Verify with show vlan brief"]

AI["C016"]["root_cause"] = "DNS server 10.10.1.11 is down or unreachable, causing resolution failures for PC-B."
AI["C016"]["confidence"] = "medium"
AI["C016"]["evidence"] = "nslookup against 10.10.1.11 failed to resolve erp.company.local, interpreted as the server being down."
AI["C016"]["next_command"] = "ping 10.10.1.11"
AI["C016"]["fix_steps"] = ["Restart DNS service on 10.10.1.11", "Re-test nslookup from PC-B"]

AI["C018"]["root_cause"] = "HQ router R1 is missing a route to the branch subnet 192.168.99.0/24."
AI["C018"]["confidence"] = "medium"
AI["C018"]["evidence"] = "show ip route does not show a working path to 192.168.99.0/24."
AI["C018"]["next_command"] = "show ip route 192.168.99.0"
AI["C018"]["fix_steps"] = ["Add a static route to 192.168.99.0/24", "Verify with show ip route"]

AI["C023"]["root_cause"] = "WAN-ACL is missing a permit statement for return traffic from the internal server."
AI["C023"]["confidence"] = "medium"
AI["C023"]["evidence"] = "Only one permit line (inbound port 80) exists in WAN-ACL, so return traffic appears unpermitted."
AI["C023"]["next_command"] = "show access-lists WAN-ACL"
AI["C023"]["fix_steps"] = ["Add a permit statement for the server's return traffic", "Verify with show access-lists"]

AI["C029"]["root_cause"] = "Guest Wi-Fi clients are experiencing a minor connectivity misconfiguration on VLAN mapping."
AI["C029"]["confidence"] = "low"
AI["C029"]["evidence"] = "wlan GUEST shows vlan 10 configured; treated as a generic config inconsistency."
AI["C029"]["next_command"] = "show wlan config GUEST"
AI["C029"]["fix_steps"] = ["Double check VLAN mapping for SSID GUEST", "Re-test guest connectivity"]

AI["C003"]["root_cause"] = "Core switch's native VLAN (1) is misconfigured and should be changed to match SW1."
AI["C003"]["confidence"] = "medium"
AI["C003"]["evidence"] = "Core switch trunk shows native vlan 1 while SW1 shows native vlan 15; the AI assumed the core side was the one to fix."
AI["C003"]["next_command"] = "show interfaces trunk on both switches"
AI["C003"]["fix_steps"] = ["Change core switch native VLAN to 15", "Verify no more native VLAN mismatch warnings"]

SAMPLE_RESP_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(SAMPLE_RESP_CSV, "w", newline="", encoding="utf-8") as f:
    fields = ["case_id", "root_cause", "osi_layer", "confidence", "evidence", "next_command", "fix_steps"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for cid in cases:
        r = dict(AI[cid])
        r["fix_steps"] = json.dumps(r["fix_steps"])
        w.writerow(r)

# ---- Review log ----
CORRECTIONS = {
    "C004": ("Edited", "AI blamed the switchport VLAN, but the port was already correctly in VLAN 30 per 'show vlan brief'. The real cause is a stale DHCP lease from the PC's previous VLAN 10 membership. Corrected root_cause and fix_steps to release/renew the lease instead of touching the switchport."),
    "C016": ("Edited", "AI assumed the DNS server was down. It's actually reachable but simply not authoritative for the internal zone -- PC-B is pointed at the wrong DNS server, not a broken one. Corrected root_cause; restarting a healthy DNS service would not have fixed anything."),
    "C018": ("Edited", "AI said the route was 'missing' when show ip route clearly lists a static route -- it exists but points at an invalid next-hop outside the /30 subnet. Corrected root_cause from 'missing route' to 'wrong next-hop on existing static route' and updated fix_steps to correct the next-hop instead of adding a duplicate route."),
    "C023": ("Rejected", "AI's 'missing permit' theory is wrong -- the real problem is the same ACL applied in both the in and out direction on one interface, so return traffic hits the implicit deny regardless of permit lines. Rewrote root_cause and fix_steps to remove the erroneous outbound ACL application."),
    "C029": ("Edited", "AI under-classified this as a 'minor connectivity misconfiguration' at low confidence. It's a security-relevant VLAN isolation failure (guest traffic reaching internal VLAN 10) and should be flagged High severity, not treated as a generic Wi-Fi glitch. Corrected confidence to high and added a security note to fix_steps."),
    "C003": ("Edited", "AI assumed the core switch's native VLAN was the misconfigured side. Design docs confirm SW1's uplink should use native VLAN 1 to match the rest of the campus trunk standard, so SW1 (native vlan 15) is actually the outlier. Corrected which side to change."),
}

with open(REVIEW_LOG_CSV, "w", newline="", encoding="utf-8") as f:
    fields = ["case_id", "ai_root_cause", "ai_confidence", "human_verdict", "corrected_root_cause", "reviewer_notes"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for cid, row in cases.items():
        ai = AI[cid]
        if cid in CORRECTIONS:
            verdict, notes = CORRECTIONS[cid]
            corrected = row["expected_fault"]
        else:
            verdict, notes = "Accepted", "AI diagnosis matched the evidence and known-correct root cause; approved as-is."
            corrected = ai["root_cause"]
        w.writerow({
            "case_id": cid,
            "ai_root_cause": ai["root_cause"],
            "ai_confidence": ai["confidence"],
            "human_verdict": verdict,
            "corrected_root_cause": corrected,
            "reviewer_notes": notes,
        })

print(f"Wrote {SAMPLE_RESP_CSV.name} and {REVIEW_LOG_CSV.name} to {REVIEW_LOG_CSV.parent}/")
