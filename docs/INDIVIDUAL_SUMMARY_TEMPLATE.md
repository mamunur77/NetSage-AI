# NetSage AI — Individual Student Summary Template
### Format: Name–College Name–Technology

> [!NOTE]
> Copy this template into a Word document (`.docx`), fill in the bracketed placeholders `[like this]`, and save it using the naming format: `YourName–YourCollege–PythonDeveloper.docx`.

---

# INDIVIDUAL SUMMARY REPORT
**Technology Domain: Python Web Developer & AI Integration**

## 1. Project Details
- **Project Title:** NetSage AI: Responsible AI Network Troubleshooter
- **Team Name:** NetSage Team
- **Team Members:**
  1. `[Your Name]` (Python Web Developer & AI Integration)
  2. `[Partner 1]` (Packet Tracer / Network Topology Creator)
  3. `[Partner 2]` (AI Prompt Design & Fine-tuning)
  4. `[Partner 3]` (Responsible AI Log & QA)
- **Submission Date:** August 2026

---

## 2. Project Objective
The goal of this project is to build an AI-assisted network troubleshooting helper for Cisco lab environments (Packet Tracer). It resolves network issues by scanning router/switch CLI configurations and show-command outputs, running deterministic checks, and utilizing a Large Language Model (LLM) to diagnose root causes and suggest fix commands. Crucially, it integrates a "Human-in-the-Loop" responsible AI review pipeline, ensuring all AI diagnoses are approved or corrected by a network administrator before execution.

---

## 3. Overview of the Complete System
NetSage AI processes troubleshooting cases through the following pipeline:
1. **Network Lab Simulation:** A physical network is built in Cisco Packet Tracer containing deliberately introduced faults (VLAN mismatch, bad subnet mask, interface shutdowns, static route issues).
2. **Evidence Collection:** Engineers run show commands (e.g. `show running-config`, `show ip interface brief`) and dump the output logs.
3. **Deterministic Filtering (Python Rule Checker):** A Python script scans the outputs for obvious errors (duplicate IPs, down links, default gateway inconsistencies) instantly.
4. **Cognitive AI Diagnosis (Groq LLM):** The symptom and logs are passed to the Groq API utilizing an optimized LLM system prompt. The AI returns a structured JSON object containing root cause, confidence, evidence, next command, and repair steps.
5. **Responsible AI Review Logs:** A human reviewer inspects the JSON, signs off, or manually edits the responses.
6. **Web Dashboard:** An interactive Streamlit app displays metric charts (issue distribution, severity, agreement rates), allows browsing cases, and contains a "Live Diagnose" workspace for network administrators.

---

## 4. Your Specific Contribution (Python Web Developer & AI Integration)
As the primary **Python Developer & AI Integration Engineer**, my individual contributions to this group project were:
- **Streamlit Web Application:** Developed the entire interactive web frontend (`app.py`) featuring an analytics dashboard (utilizing Plotly charts), a Case Browser, and a Live Diagnose interface.
- **API Pipeline & Fallback Handling:** Wrote the core script `scripts/ai_diagnose.py` integrating the Groq LLM API. Programmed parsing routines to handle LLM schema validation errors, standardizing all output to strict JSON formatting.
- **Deterministic Engine:** Built `scripts/rule_checker.py` using Python's regular expressions (`re`) to parse text configurations and instantly flag duplicate IPs, gateway mismatches, and route omissions.
- **Excel Report Builder:** Programmed `scripts/build_dashboard.py` using `openpyxl` to compile data into an Excel spreadsheet containing pivots and tables.
- **Cloud Deployment:** Deployed the frontend live on Streamlit Cloud for public access.

---

## 5. Tools & Technologies Used
- **Programming Language:** Python 3
- **Web App Framework:** Streamlit (deployed on Streamlit Cloud)
- **Data Visualization:** Plotly Express
- **API Integration:** Groq SDK (hosted LLaMA & GPT model backends)
- **Excel Automation:** Openpyxl & Pandas
- **Version Control:** Git & GitHub

---

## 6. Challenges Faced & Solutions

### Challenge 1: LLM JSON Output Formatting Errors
* **The Problem:** The AI model would occasionally return explanations or markdown wrappers (like ` ```json `) instead of pure raw JSON, causing parsing to fail.
* **The Solution:** I implemented standard regular expression parsing to strip markdown fences and automatically fall back to standard text completions if the JSON payload was malformed, extracting the valid brace-enclosed strings.

### Challenge 2: Local secrets vs Cloud secrets in Streamlit
* **The Problem:** Accessing `st.secrets` locally without a local `secrets.toml` file would raise a critical `StreamlitSecretNotFoundError` and crash the application.
* **The Solution:** I added a try-except statement inside the key-loader function to silently catch the exception, allowing the app to check for environment variables (`.env`) or fallback to interactive manual key input.

---

## 7. Results & Outcomes
- **100% Parsing Accuracy:** The AI pipeline successfully parsed and logged all 30 test cases.
- **80% AI Agreement:** The human review confirmed the AI was fully correct in 24 cases, required editing in 5 cases, and was rejected in 1 case.
- **Interactive UI:** Project diagnostics can now be done via a cloud-based web interface, making network troubleshooting fast and accessible.
