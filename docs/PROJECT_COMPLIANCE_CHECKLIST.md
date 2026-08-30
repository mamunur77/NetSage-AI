# NetSage AI — Project Compliance Checklist

This document compares the requirements specified in [`NetSage_AI_Project_Guide.docx`](file:///e:/PROJECTS/CISCO/NetSage_AI_Project_Guide.docx) with the actual implementation in this workspace.

---

## 📊 Summary of Compliance

| Requirement Area | Status | Location in Project | Notes |
|---|---|---|---|
| **30+ Troubleshooting Cases** | ✅ 100% Complete | [`data/cases.csv`](file:///e:/PROJECTS/CISCO/data/cases.csv) | Contains 30 structured cases covering VLAN, gateway, DHCP, DNS, routing, ACL, NAT, wireless. |
| **AI Prompt Library** | ✅ 100% Complete | [`prompts/diagnose_prompt.md`](file:///e:/PROJECTS/CISCO/prompts/diagnose_prompt.md) | Structured system prompt with JSON schema & examples. |
| **Python Rule Checker** | ✅ 100% Complete | [`scripts/rule_checker.py`](file:///e:/PROJECTS/CISCO/scripts/rule_checker.py) | Implements duplicate IP, wrong mask, gateway mismatch, interface down, missing VLAN, missing route. |
| **Rule Checker Sample Output** | ✅ 100% Complete | [`outputs/rule_checker_sample_output.txt`](file:///e:/PROJECTS/CISCO/outputs/rule_checker_sample_output.txt) | Sample output of the deterministic checker. |
| **Human Review Record** | ✅ 100% Complete | [`data/review_log.csv`](file:///e:/PROJECTS/CISCO/data/review_log.csv) | Holds verdicts (Accepted, Edited, Rejected) for all 30 cases. |
| **Responsible AI Log** | ✅ 100% Complete | [`docs/responsible_ai_log.md`](file:///e:/PROJECTS/CISCO/docs/responsible_ai_log.md) | Details **6 corrected cases** (exceeds the 5 required) with explanations of why corrections matter. |
| **Dashboard** | ✅ Exceeded | [`outputs/dashboard.xlsx`](file:///e:/PROJECTS/CISCO/outputs/dashboard.xlsx) & Live App | Excel dashboard with charts. **Exceeded** by building a live Streamlit Web Dashboard: [Live App](https://packettraceraidiagnoser-pyrbpk7tdzsbppwfmadsqf.streamlit.app/). |
| **Packet Tracer Network** | ⚠️ Action Needed | [`packet_tracer_lab/`](file:///e:/PROJECTS/CISCO/packet_tracer_lab) | Config files (`SW1_Config.txt`, `R1_Config_Broken.txt`) are provided with 5 deliberate bugs. You must load these into Packet Tracer and save your `.pkt` file. |
| **Demo Video** | ⚠️ Action Needed | [`packet_tracer_lab/LAB_SETUP_GUIDE.md`](file:///e:/PROJECTS/CISCO/packet_tracer_lab/LAB_SETUP_GUIDE.md) | Complete step-by-step workflow and script outline provided for your 5-10 min video. You must record it. |
| **Individual Summary** | ⚠️ Action Needed | [`docs/INDIVIDUAL_SUMMARY_TEMPLATE.md`](file:///e:/PROJECTS/CISCO/docs/INDIVIDUAL_SUMMARY_TEMPLATE.md) | Template created to help you draft your individual submission document. |

---

## 🔍 Detailed Line-by-Line Verification

### 1. 30+ Troubleshooting Cases
* **Guide says:** *"Prepare at least 30 cases... each containing symptom, topology note, show-command output, expected fault, OSI layer, concept tag, and severity in cases.csv."*
* **Verification:** [`data/cases.csv`](file:///e:/PROJECTS/CISCO/data/cases.csv) contains exactly 30 rows with columns: `case_id`, `category`, `symptom`, `topology_note`, `show_output`, `expected_fault`, `osi_layer`, `concept_tag`, and `severity`.

### 2. AI Prompt Library
* **Guide says:** *"Create a structured prompt that asks the AI to diagnose each case... output should include root cause, confidence, evidence, next command and fix steps. Save as diagnose_prompt.md."*
* **Verification:** [`prompts/diagnose_prompt.md`](file:///e:/PROJECTS/CISCO/prompts/diagnose_prompt.md) specifies a strict system prompt and returns JSON matching all requested keys: `root_cause`, `osi_layer`, `confidence`, `evidence`, `next_command`, and `fix_steps`.

### 3. Python Rule Checker
* **Guide says:** *"Build deterministic checks for duplicate IPs, wrong masks, gateway mismatch, interface down, missing VLAN and missing routes. Provide sample output."*
* **Verification:** [`scripts/rule_checker.py`](file:///e:/PROJECTS/CISCO/scripts/rule_checker.py) parses the show output files. 
  - Duplicate IP check: `check_duplicate_ip()`
  - Wrong mask check: `check_mask_mismatch()`
  - Gateway mismatch check: `check_gateway_mismatch()`
  - Interface down check: `check_interfaces_down()`
  - Missing VLAN check: `check_missing_vlans()`
  - Missing route check: `check_missing_routes()`
  - Sample output is generated in [`outputs/rule_checker_sample_output.txt`](file:///e:/PROJECTS/CISCO/outputs/rule_checker_sample_output.txt).

### 4. Human Review & Responsible AI
* **Guide says:** *"Every AI diagnosis must be reviewed by a human... Accepted, Edited, Rejected... Document at least 5 cases where AI was corrected and explain why."*
* **Verification:** [`data/review_log.csv`](file:///e:/PROJECTS/CISCO/data/review_log.csv) records human review verdicts for all 30 cases. [`docs/responsible_ai_log.md`](file:///e:/PROJECTS/CISCO/docs/responsible_ai_log.md) lists **6 specific cases** (C004, C016, C018, C023, C029, C003) explaining in detail why the human corrected the AI's output.

### 5. Dashboard
* **Guide says:** *"Create a simple spreadsheet or chart showing issue types, severity and AI-vs-human agreement."*
* **Verification:** We built two dashboards:
  1. [`outputs/dashboard.xlsx`](file:///e:/PROJECTS/CISCO/outputs/dashboard.xlsx): Excel sheet with pivot tables and charts.
  2. Streamlit Web App: Online interactive dashboard showing live KPIs, Plotly charts, and filters.

---

## 🛠️ What You Need to Do Next (To Submit)

1. **Create the `.pkt` File:**
   - Open Cisco Packet Tracer on your PC.
   - Use the topology layout and steps described in [`packet_tracer_lab/LAB_SETUP_GUIDE.md`](file:///e:/PROJECTS/CISCO/packet_tracer_lab/LAB_SETUP_GUIDE.md).
   - Paste the switch config from [`SW1_Config.txt`](file:///e:/PROJECTS/CISCO/packet_tracer_lab/SW1_Config.txt) and router config from [`R1_Config_Broken.txt`](file:///e:/PROJECTS/CISCO/packet_tracer_lab/R1_Config_Broken.txt).
   - Save the file as a `.pkt` file.

2. **Draft Your Individual Summary:**
   - Open [`docs/INDIVIDUAL_SUMMARY_TEMPLATE.md`](file:///e:/PROJECTS/CISCO/docs/INDIVIDUAL_SUMMARY_TEMPLATE.md) (created in your folder).
   - Fill in your details (Name, College, technology role).
   - Convert it into a Word `.docx` or `.pdf` file.
   - Rename the file using the required format: `Name–College Name–Technology.docx` (e.g. `Mamunur-CiscoAcademy-PythonDeveloper.docx`).

3. **Record the Demo Video:**
   - Record a 5-10 minute screencast showing:
     - The Packet Tracer network with broken connections.
     - Running the Streamlit Web Dashboard or CLI scripts to show AI diagnosing the issue.
     - Fixing the network in Packet Tracer.
     - Showing pings passing successfully after the fix.
