# NetSage AI

**AI-Assisted Network Troubleshooting Console with Mandatory Human Review**

Built for the Cisco "Applied AI + Network Troubleshooting" VIP Internship Project.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://packettraceraidiagnoser-pyrbpk7tdzsbppwfmadsqf.streamlit.app/)

🌐 **Live Web Console:** [packettraceraidiagnoser.streamlit.app](https://packettraceraidiagnoser-pyrbpk7tdzsbppwfmadsqf.streamlit.app/)

---

## What is NetSage AI?

NetSage AI is a network troubleshooting console that helps engineers diagnose Cisco lab network faults using a **three-tier hybrid architecture**:

1. **Tier 1 — Deterministic Rule Checker:** A fast Python regex engine (`scripts/rule_checker.py`) that instantly scans show-command evidence for obvious configuration errors (interface down, missing VLAN, gateway mismatch) with zero API cost.

2. **Tier 2 — Cognitive AI Diagnosis:** A Large Language Model backend (Groq API) that analyzes complex multi-device logic problems (OSPF area mismatch, HSRP split-brain, ACL rule ordering) and returns structured JSON with root cause, confidence, evidence, next command, and fix steps.

3. **Tier 3 — Gated Human Oversight:** A mandatory human review gate where a network administrator must **Approve**, **Edit**, or **Reject** every AI diagnosis before verification fix steps are unlocked. The AI never autonomously modifies a network device.

---

## How It Works — 5-Step Gated Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 01 Evidence  │───▶│ 02 Rule Scan│───▶│03 AI Diagnosis│───▶│04 Human Gate │───▶│05 Verification│
│              │    │             │    │              │    │   (Required) │    │   (Locked)   │
│ Symptom +    │    │ Deterministic│   │ Groq LLM     │    │ Accept/Edit/ │    │ Unlocked only│
│ Show-command │    │ regex checks│    │ JSON output  │    │ Reject       │    │ after human  │
│ evidence     │    │ (no API)    │    │              │    │              │    │ approval     │
└─────────────┘    └─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Step-by-Step:
1. **01 Evidence:** Displays the observed symptom, topology context, raw Cisco CLI output, and an Interactive Topology Explorer (Client → Switch → Router → Server).
2. **02 Rule Scan:** Runs deterministic Python regex checks for interface down, missing VLANs, gateway mismatches, duplicate IPs, and missing routes — instant results, no API needed.
3. **03 AI Diagnosis:** Sends the symptom + evidence to the Groq LLM API. Returns structured JSON: `root_cause`, `confidence`, `osi_layer`, `evidence`, `next_command`, and `fix_steps`.
4. **04 Human Gate:** Tab 05 remains **🔒 Locked** until a human reviewer selects a verdict (Accepted/Edited/Rejected), enters reviewer notes, and clicks **Save Human Review**.
5. **05 Verification:** Once approved, Tab 05 **unlocks** and displays the verified resolution instructions and CLI verification commands.

---

## Key Features

| Feature | Description |
|---|---|
| **50 Diagnostic Cases** | Covers VLAN, Routing, DHCP, DNS, ACL, NAT, STP, EtherChannel, HSRP, IPv6, Wireless, Security, QoS |
| **Interactive Topology Explorer** | Click-through scope explorer (Client → Access Switch → Router/L3 → Server) |
| **Live AI Diagnosis** | On-demand Groq API diagnosis from pasted show-command output |
| **Gated Human Review** | Verification locked until human reviewer approves the AI output |
| **Live Case Persistence** | Live diagnoses auto-saved as new cases (LIVE-001, LIVE-002...) across all pages |
| **Responsible AI Audit** | 9 human-corrected cases documented with engineering rationales |
| **Excel Dashboard** | Native pivot charts in `outputs/dashboard.xlsx` via openpyxl |
| **Streamlit Cloud Deployment** | Public URL with automatic GitHub sync |

---

## Project Structure

```
CISCO/
├── app.py                        ← Streamlit web console (main application)
├── README.md                     ← This file
├── requirements.txt              ← pip dependencies (groq, openpyxl, streamlit, plotly)
├── .env.example                  ← API key template — copy to .env
├── NetSage_AI_Project_Report.docx ← Complete project report (Word document)
│
├── data/                         ← All input & generated data
│   ├── cases.csv                 ← 50 troubleshooting cases (ground truth)
│   ├── review_log.csv            ← Human oversight audit log (Accepted/Edited/Rejected)
│   └── sample_ai_responses.csv   ← Pre-generated AI output (works without API key)
│
├── outputs/                      ← Generated artifacts
│   ├── dashboard.xlsx            ← Excel dashboard with native pivot charts
│   ├── ai_responses.csv          ← Written by ai_diagnose.py (live API run)
│   └── rule_checker_sample_output.txt
│
├── prompts/
│   └── diagnose_prompt.md        ← System prompt + JSON schema + few-shot examples
│
├── docs/
│   ├── responsible_ai_log.md     ← 9 corrected cases with engineering rationales
│   ├── PROJECT_COMPLIANCE_CHECKLIST.md
│   ├── INDIVIDUAL_SUMMARY_TEMPLATE.md
│   └── STREAMLIT_DEPLOYMENT.md
│
├── scripts/
│   ├── ai_diagnose.py            ← Calls Groq API → outputs/ai_responses.csv
│   ├── rule_checker.py           ← Deterministic checks (no API key needed)
│   ├── build_dashboard.py        ← Generates outputs/dashboard.xlsx
│   ├── generate_cases.py         ← Regenerates data/cases.csv (50 cases)
│   ├── generate_ai_and_review.py ← Regenerates demo data files
│   └── generate_docx_report.py   ← Generates project report (.docx)
│
└── packet_tracer_lab/
    ├── LAB_SETUP_GUIDE.md        ← Step-by-step Packet Tracer setup instructions
    ├── SW1_Config.txt            ← Switch config with 2 deliberate bugs
    ├── R1_Config_Broken.txt      ← Router config with 3 deliberate bugs
    └── R1_Config_Working.txt     ← Clean router config (reference)
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Groq API key
Get a free key (no credit card) at https://console.groq.com/keys
```bash
# Create .env file
echo GROQ_API_KEY=gsk_your_key_here > .env
```

### 3. Run the deterministic rule checker (no API key needed)
```bash
python scripts/rule_checker.py
```

### 4. Run the AI diagnosis pipeline (requires Groq API key)
```bash
python scripts/ai_diagnose.py
```

### 5. Launch the Streamlit Web Console
```bash
python -m streamlit run app.py
```

### 6. Build the Excel dashboard
```bash
python scripts/build_dashboard.py
# → writes outputs/dashboard.xlsx
```

---

## System Architecture

```
                    ┌───────────────────────────────────────────┐
                    │         data/cases.csv (50 cases)         │
                    └──────────────┬────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
          ┌─────────────┐  ┌────────────┐  ┌───────────────┐
          │ Rule Checker │  │ AI Diagnose│  │ Streamlit App │
          │  (Tier 1)    │  │  (Tier 2)  │  │  (Frontend)   │
          │ Deterministic│  │  Groq LLM  │  │  5-Step Tabs  │
          │ Python regex │  │  JSON API  │  │  + Live Diag  │
          └──────┬───────┘  └─────┬──────┘  └───────┬───────┘
                 │                │                  │
                 ▼                ▼                  ▼
          Console Output   ai_responses.csv    Web Dashboard
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  Human Review Gate (Tier 3)  │
                    │  Accept / Edit / Reject      │
                    │  → data/review_log.csv       │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
          responsible_ai_log  dashboard.xlsx  Verification
              (9 cases)      (pivot charts)   (Unlocked)
```

---

## Diagnostic Case Categories

| Category | Cases | Example Concepts |
|---|---|---|
| VLAN & Trunking | C001–C004, C045, C050 | Trunk pruning, unassigned ports, native VLAN mismatch, dot1Q tag |
| Gateway & Routing | C005–C008, C017–C020, C046, C049 | Gateway mismatch, subinterface shutdown, OSPF, static routes, BGP |
| DHCP & DNS | C009–C016 | Pool exhaustion, subnet mask mismatch, missing helper, DNS unreachable |
| ACL & Security | C021–C024, C040–C042, C048 | Implicit deny, rule ordering, port security, SSH, AAA |
| NAT & HA | C025–C027, C036–C037, C047 | Missing NAT inside/outside, HSRP preempt, split-brain |
| STP & EtherChannel | C031–C035 | Root bridge priority, BPDU Guard, LACP mismatch |
| IPv6 & Wireless & QoS | C028–C030, C038–C039, C043–C044 | WPA2 PSK, SSID VLAN, IPv6 unicast-routing, LLQ, CoS |

---

## Responsible AI — Human Oversight Results

| Verdict | Count | Rate | Description |
|---|---|---|---|
| **Accepted** | 41 | 82% | AI root cause matched the known-correct ground truth fault |
| **Edited** | 6 | 12% | AI identified the general fault domain but was imprecise; human corrected |
| **Rejected** | 3 | 6% | AI root cause was substantively wrong; human replaced it entirely |

**9 correction cases documented in [`docs/responsible_ai_log.md`](docs/responsible_ai_log.md)** with detailed engineering rationales for each human override.

---

## Packet Tracer Lab (5 Embedded Bugs)

The `packet_tracer_lab/` folder contains ready-to-paste configuration scripts for building a Cisco Packet Tracer topology with **5 deliberate network faults**:

| Bug | Case | Device | What's Wrong |
|---|---|---|---|
| 1 | C006 | R1 | `G0/0.40` is `shutdown` — VLAN 40 gateway unreachable |
| 2 | C010 | R1 | DHCP pool uses `/25` instead of `/24` — wrong subnet mask |
| 3 | C013 | R1 | DNS server points to `172.16.1.99` (unreachable) |
| 4 | C002 | SW1 | `Fa0/16` left in VLAN 1 (should be VLAN 20) |
| 5 | C001 | SW1 | VLAN 10 NOT in trunk allowed list |

See [`packet_tracer_lab/LAB_SETUP_GUIDE.md`](packet_tracer_lab/LAB_SETUP_GUIDE.md) for step-by-step build instructions.

---

## Deterministic Rule Checker

The rule checker (`scripts/rule_checker.py`) performs 6 automated checks **without any AI or API key**:

| Check | What It Detects |
|---|---|
| Duplicate IP | Repeated IPv4 addresses in show-command output |
| Subnet mismatch | Host not belonging to expected network |
| Gateway mismatch | Default gateway not in host's subnet |
| Interface status | Down or administratively down interfaces |
| VLAN existence | Missing VLANs in trunk or VLAN database |
| Route existence | Missing destination routes in routing table |

---

## Free-Tier Groq Models

| Model ID | Notes |
|---|---|
| `openai/gpt-oss-20b` | Current default in app.py |
| `llama-3.3-70b-versatile` | Best JSON output, 128k context |
| `llama-3.1-8b-instant` | Fastest option |
| `gemma2-9b-it` | Lightweight alternative |
| `llama-4-scout-17b-16e-instruct` | Llama 4, 131k context |

---

## Technologies Used

- **Python 3** — Core programming language
- **Streamlit** — Web application framework (deployed on Streamlit Cloud)
- **Plotly Express** — Interactive data visualization charts
- **Groq SDK** — LLM API integration for AI diagnosis
- **Openpyxl & Pandas** — Excel dashboard generation and data processing
- **Git & GitHub** — Version control and CI/CD deployment pipeline

---

## License

This project was developed as part of the Cisco VIP Internship evaluation.
