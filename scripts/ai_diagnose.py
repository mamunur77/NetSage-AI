#!/usr/bin/env python3
"""
NetSage AI - runs every case in data/cases.csv through the Groq API using
the structured prompt in prompts/diagnose_prompt.md, and writes
outputs/ai_responses.csv.

Requires: GROQ_API_KEY environment variable, `pip install groq`

Free-tier models available on Groq (no credit card required):
  - llama-3.3-70b-versatile         ← DEFAULT (best JSON output, 128k ctx)
  - llama-3.1-8b-instant            (fastest, lighter, 128k ctx)
  - llama3-70b-8192                 (solid all-rounder, 8k ctx)
  - llama3-8b-8192                  (fast, lightweight, 8k ctx)
  - gemma2-9b-it                    (Google Gemma 2, 8k ctx)
  - llama-4-scout-17b-16e-instruct  (Llama 4 Scout, 131k ctx)
  - qwen-qwq-32b                    (strong reasoning, 131k ctx)
  - deepseek-r1-distill-llama-70b   (reasoning model, 128k ctx)

Note: Free tier has rate limits (~30 RPM). If you hit a rate limit, increase
SLEEP_BETWEEN_CALLS or switch to a lighter model.
"""
import csv
import json
import os
import sys
import time
from pathlib import Path

try:
    from groq import Groq
except ImportError:
    print("Run: pip install groq", file=sys.stderr)
    raise

# ── Paths (resolved relative to this script, works from any cwd) ─────────────
ROOT        = Path(__file__).parent.parent
CASES_CSV   = ROOT / "data" / "cases.csv"
OUTPUT_CSV  = ROOT / "outputs" / "ai_responses.csv"
# ─────────────────────────────────────────────────────────────────────────────

# ── Model selection ───────────────────────────────────────────────────────────
MODEL = "openai/gpt-oss-20b"
SLEEP_BETWEEN_CALLS = 1   # seconds; set to 0 on a paid tier
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are NetSage AI, a network-troubleshooting assistant for Cisco-style lab
networks (Packet Tracer topologies: routers, switches, VLANs, DHCP, DNS,
routing, ACLs, NAT, wireless).

You will be given a symptom description, a topology note, and raw
show-command / config output evidence.

Your job is ONLY to propose a diagnosis. You never claim a fix has been
applied. A human reviewer always approves, edits, or rejects your answer
before any change is made in the lab.

Rules:
1. Base your root cause ONLY on evidence present in the show-command output
   you were given. Do not invent interface names, IPs, or commands that
   were not shown or that are not standard next steps.
2. If the evidence is ambiguous or insufficient to be sure, set confidence
   to "low" or "medium" and say in "evidence" what additional show command
   would confirm it.
3. Quote or closely reference the specific line(s) of evidence that support
   your root cause -- don't just assert a conclusion.
4. Return ONLY valid JSON. No markdown fences, no prose before or after.

Respond with exactly this schema:
{
  "case_id": "<string, echo the case id given>",
  "root_cause": "<one sentence, specific fault>",
  "osi_layer": "<e.g. Layer 2, Layer 3, Layer 3/4, Layer 7>",
  "confidence": "<low | medium | high>",
  "evidence": "<1-3 sentences citing the specific show-output lines that support the root cause>",
  "next_command": "<the single next show/debug command a human should run to confirm, or 'none - evidence sufficient'>",
  "fix_steps": ["<step 1>", "<step 2>", "..."]
}"""

FEWSHOT = [
    {"role": "user", "content": (
        "Case ID: EX01\nCategory: Gateway\nSymptom: PC has a valid IP in the "
        "correct subnet but cannot ping anything outside its own subnet, "
        "including the gateway.\nTopology note: PC 192.168.1.50/24, Router "
        "G0/0 configured as gateway.\n\nEvidence:\nPC> ipconfig\nIP Address: "
        "192.168.1.50\nSubnet Mask: 255.255.255.0\nDefault Gateway: "
        "192.168.1.254\n\nR1# show ip interface brief\nInterface   "
        "IP-Address     Status   Protocol\nG0/0        192.168.1.1    up     "
        "  up\n\nReturn the JSON diagnosis now."
    )},
    {"role": "assistant", "content": json.dumps({
        "case_id": "EX01",
        "root_cause": "PC's configured default gateway (192.168.1.254) does not match the router's actual interface IP (192.168.1.1).",
        "osi_layer": "Layer 3",
        "confidence": "high",
        "evidence": "ipconfig shows Default Gateway 192.168.1.254, but 'show ip interface brief' shows G0/0 is actually 192.168.1.1 and up/up.",
        "next_command": "none - evidence sufficient",
        "fix_steps": [
            "Correct the PC's default gateway (static or DHCP scope) to 192.168.1.1",
            "Re-test connectivity to the gateway and beyond with ping 192.168.1.1",
        ],
    })},
    {"role": "user", "content": (
        "Case ID: EX02\nCategory: ACL\nSymptom: PCs in the Finance VLAN cannot "
        "reach the payroll server even though routing and DHCP are confirmed "
        "working.\nTopology note: R1 G0/2 (Finance gateway) has an inbound ACL "
        "applied.\n\nEvidence:\nR1# show access-lists\nExtended IP access list "
        "FINANCE-IN\n 10 deny ip any host 192.168.50.10\n 20 permit ip any any "
        "(0 matches)\n\nR1# show run interface g0/2\ninterface GigabitEthernet0/2\n"
        " ip access-group FINANCE-IN in\n\nReturn the JSON diagnosis now."
    )},
    {"role": "assistant", "content": json.dumps({
        "case_id": "EX02",
        "root_cause": "ACL FINANCE-IN, applied inbound on G0/2, explicitly denies all traffic to the payroll server before the permit-any line is reached.",
        "osi_layer": "Layer 3/4",
        "confidence": "high",
        "evidence": "Line 10 of FINANCE-IN is 'deny ip any host 192.168.50.10', which sits above line 20's permit-any and is processed first.",
        "next_command": "show access-lists FINANCE-IN",
        "fix_steps": [
            "Remove or reorder the deny statement for host 192.168.50.10",
            "Re-apply/verify ACL FINANCE-IN on G0/2 inbound",
            "Confirm Finance PCs can reach the payroll server",
        ],
    })},
    {"role": "user", "content": (
        "Case ID: EX03\nCategory: DNS\nSymptom: Users can ping IP addresses on "
        "the internet but cannot browse to any website by name.\nTopology note: "
        "PCs on 172.16.1.0/24, expected DNS server 172.16.1.5 (internal) or "
        "8.8.8.8 (external).\n\nEvidence:\nPC> ipconfig /all\nDNS Servers: "
        "172.16.1.99\n\nReturn the JSON diagnosis now."
    )},
    {"role": "assistant", "content": json.dumps({
        "case_id": "EX03",
        "root_cause": "PC is pointed at DNS server 172.16.1.99, which is not the documented internal (172.16.1.5) or external (8.8.8.8) DNS server.",
        "osi_layer": "Layer 7",
        "confidence": "medium",
        "evidence": "The only evidence given is the client's configured DNS server, 172.16.1.99, which doesn't match either known-good DNS server.",
        "next_command": "ping 172.16.1.99 and nslookup www.example.com 172.16.1.99",
        "fix_steps": [
            "Verify whether 172.16.1.99 is a valid, reachable DNS server or a misconfiguration",
            "If invalid, correct DHCP scope option 6 / static client config to 172.16.1.5",
            "Re-test name resolution with nslookup",
        ],
    })},
]


def build_user_message(row: dict) -> str:
    return (
        f"Case ID: {row['case_id']}\n"
        f"Category: {row['category']}\n"
        f"Symptom: {row['symptom']}\n"
        f"Topology note: {row['topology_note']}\n\n"
        f"Evidence:\n{row['show_output']}\n\n"
        f"Return the JSON diagnosis now."
    )


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    
    # Try reading from a local .env file manually
    env_path = ROOT / ".env"
    if not api_key and env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GROQ_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass

    # If still not found, ask the user to paste it interactively
    if not api_key:
        print("Groq API Key not found in environment variables or .env file.")
        api_key = input("Please paste your Groq API Key (starts with gsk_): ").strip()
        if not api_key:
            print("Error: No API key provided. Exiting.", file=sys.stderr)
            sys.exit(1)

    client = Groq(api_key=api_key)

    with open(CASES_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    out_fields = ["case_id", "root_cause", "osi_layer", "confidence",
                  "evidence", "next_command", "fix_steps", "parse_ok", "raw_response"]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=out_fields)
        writer.writeheader()

        for i, row in enumerate(rows):
            messages = FEWSHOT + [{"role": "user", "content": build_user_message(row)}]

            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    max_tokens=1000,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                text = resp.choices[0].message.content or ""

                try:
                    data = json.loads(text)
                    parse_ok = True
                except json.JSONDecodeError:
                    data = {}
                    parse_ok = False

            except Exception as e:
                print(f"{row['case_id']}: API ERROR — {e}", file=sys.stderr)
                data = {}
                text = f"ERROR: {e}"
                parse_ok = False

            writer.writerow({
                "case_id":     row["case_id"],
                "root_cause":  data.get("root_cause", ""),
                "osi_layer":   data.get("osi_layer", ""),
                "confidence":  data.get("confidence", ""),
                "evidence":    data.get("evidence", ""),
                "next_command": data.get("next_command", ""),
                "fix_steps":   json.dumps(data.get("fix_steps", [])),
                "parse_ok":    parse_ok,
                "raw_response": text,
            })

            status = "OK" if parse_ok else "PARSE FAILURE"
            print(f"[{i+1:02d}/{len(rows)}] {row['case_id']}: {status}")

            if SLEEP_BETWEEN_CALLS > 0 and i < len(rows) - 1:
                time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"\nDone -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
