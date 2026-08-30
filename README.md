# NetSage AI

An AI-assisted troubleshooting helper for Cisco-style / Packet Tracer lab
networks, built for the Cisco "Applied AI + Network Troubleshooting" project.
The AI proposes a diagnosis; a human always reviews it before anything is
treated as fixed.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

🌐 **Live Web Dashboard:** [Deploy on Streamlit Cloud](https://share.streamlit.io/) (See the [Streamlit Deployment Guide](docs/STREAMLIT_DEPLOYMENT.md) to launch your own version in minutes!)

---

## Project Structure

```
CISCO/
├── README.md
├── requirements.txt          ← pip dependencies (groq, openpyxl)
├── .env.example              ← API key template — copy to .env
│
├── data/                     ← all input & generated data
│   ├── cases.csv             ← 30 troubleshooting cases
│   ├── review_log.csv        ← human oversight log
│   └── sample_ai_responses.csv ← pre-generated demo AI output
│
├── outputs/                  ← generated artifacts
│   ├── dashboard.xlsx        ← Excel dashboard with charts
│   ├── ai_responses.csv      ← written by ai_diagnose.py (live run)
│   └── rule_checker_sample_output.txt
│
├── prompts/
│   └── diagnose_prompt.md    ← system prompt + JSON schema + few-shot examples
│
├── docs/
│   └── responsible_ai_log.md ← 6 corrected cases, patterns, retro notes
│
└── scripts/
    ├── ai_diagnose.py        ← calls Groq API, writes outputs/ai_responses.csv
    ├── rule_checker.py       ← deterministic checks (no API key needed)
    ├── build_dashboard.py    ← generates outputs/dashboard.xlsx
    ├── generate_cases.py     ← regenerates data/cases.csv (edit if needed)
    └── generate_ai_and_review.py ← regenerates demo data/sample_ai_responses.csv
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Groq API key
Get a free key (no credit card) at https://console.groq.com/keys
```powershell
# PowerShell
$env:GROQ_API_KEY = "gsk_your_key_here"
```

### 3. Run the deterministic rule checker (no API key needed)
```bash
python scripts/rule_checker.py
```

### 4. Run the live AI diagnosis
```bash
python scripts/ai_diagnose.py
# → writes outputs/ai_responses.csv
```

### 5. Fill in the human review
Open `data/review_log.csv` and log **Accepted / Edited / Rejected** for each case,
comparing `ai_responses.csv` against the `expected_fault` column in `data/cases.csv`.

### 6. Rebuild the dashboard
```bash
python scripts/build_dashboard.py
# → writes outputs/dashboard.xlsx
```

---

## How the Pipeline Works

```
data/cases.csv (30 cases)
    │
    ├──► scripts/rule_checker.py ──────────────────────► Console output (deterministic flags)
    │
    └──► scripts/ai_diagnose.py ──► Groq API ──► outputs/ai_responses.csv
                                                          │
                                                          ▼
                                               Human Review (data/review_log.csv)
                                                          │
                                                 ┌────────┴────────┐
                                              Accepted        Edited/Rejected
                                                 └────────┬────────┘
                                                          ▼
                                                docs/responsible_ai_log.md
                                                          │
                                                          ▼
                                               scripts/build_dashboard.py
                                                          │
                                                          ▼
                                               outputs/dashboard.xlsx
```

---

## What's in the Data

| File | Rows | Description |
|---|---|---|
| `data/cases.csv` | 30 | Troubleshooting cases across VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless |
| `data/review_log.csv` | 30 | Accepted/Edited/Rejected verdicts + reviewer notes |
| `data/sample_ai_responses.csv` | 30 | Pre-generated demo output (used without an API key) |

**AI performance (demo run):** 80% Accepted · 16.7% Edited · 3.3% Rejected

---

## Demo Video Outline (5–10 min)

1. **Broken case** (30 s): show one Packet Tracer lab with the symptom (e.g. C006 — VLAN 40 has no gateway).
2. **Rule checker** (1 min): run `python scripts/rule_checker.py`, point out the deterministic finding.
3. **AI diagnosis** (1–2 min): show the JSON response — root cause, confidence, evidence, next command, fix steps.
4. **Human review** (1–2 min): walk through one corrected case (e.g. C023) to show Edited/Rejected.
5. **Fix + verification** (1–2 min): apply the fix in Packet Tracer, re-run `show ip interface brief`.
6. **Dashboard** (30 s): show `outputs/dashboard.xlsx` — issue-type spread, severity mix, 80% agreement rate.

---

## Free-Tier Groq Models (set in `scripts/ai_diagnose.py`)

| Model ID | Notes |
|---|---|
| `llama-3.3-70b-versatile` | **Default** — best JSON output, 128k ctx |
| `llama-3.1-8b-instant` | Fastest option |
| `gemma2-9b-it` | Lightweight alternative |
| `llama-4-scout-17b-16e-instruct` | Llama 4, 131k ctx |
| `qwen-qwq-32b` | Strong reasoning |
| `deepseek-r1-distill-llama-70b` | Reasoning model |
