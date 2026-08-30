"""
NetSage AI — Network Intelligence Console
==========================================
Unified AI-Assisted Network Troubleshooting Console & Responsible AI Gate

Features:
  - 🌐 Console: Case-by-case interactive console matching Cisco VIP project standard
  - 📊 Dashboard: Aggregate analytics & Plotly charts
  - 🔍 Live Diagnose: On-demand AI diagnosis for raw show commands
  - 📋 Directory: Searchable database of all 50 troubleshooting cases
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
CASES_CSV = DATA_DIR / "cases.csv"
SAMPLE_AI_CSV = DATA_DIR / "sample_ai_responses.csv"
LIVE_AI_CSV = OUTPUT_DIR / "ai_responses.csv"
REVIEW_CSV = DATA_DIR / "review_log.csv"

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NetSage AI — Network Intelligence Console",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0b0e17 0%, #121829 50%, #1a2238 100%);
        color: #e2e8f0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #0f1423;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    /* Hero Banner */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        position: relative;
    }
    .hero-kicker {
        color: #818cf8;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 6px;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.95rem;
        max-width: 800px;
    }
    .status-online {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 12px;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #22c55e;
        border-radius: 50%;
    }

    /* Metric Box Grid */
    .metric-grid-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-grid-label {
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .metric-grid-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
    }

    /* Diagnosis Root Cause Box */
    .root-cause-box {
        background: rgba(34, 197, 94, 0.08);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 12px;
        padding: 20px;
        color: #86efac;
        font-size: 1.05rem;
        font-weight: 500;
        margin-bottom: 16px;
    }

    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 24px 0 12px 0;
    }
    .section-number {
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.8rem;
    }

    /* Badge styles */
    .badge-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-critical { background: rgba(239,68,68,0.25); color: #fca5a5; }
    .badge-high { background: rgba(239,68,68,0.2); color: #fca5a5; }
    .badge-medium { background: rgba(251,191,36,0.2); color: #fcd34d; }
    .badge-low { background: rgba(34,197,94,0.2); color: #86efac; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 8px 18px;
        border: 1px solid rgba(255,255,255,0.08);
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99,102,241,0.25) !important;
        border-color: rgba(99,102,241,0.5) !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Data Loaders ──────────────────────────────────────────────────────────────
@st.cache_data
def load_cases():
    if CASES_CSV.exists():
        return pd.read_csv(CASES_CSV)
    return pd.DataFrame()


@st.cache_data
def load_ai_responses():
    if LIVE_AI_CSV.exists():
        return pd.read_csv(LIVE_AI_CSV)
    elif SAMPLE_AI_CSV.exists():
        return pd.read_csv(SAMPLE_AI_CSV)
    return pd.DataFrame()


def load_review():
    if REVIEW_CSV.exists():
        return pd.read_csv(REVIEW_CSV)
    return pd.DataFrame()


def save_review_entry(case_id, verdict, corrected_root_cause, notes, reviewer="Network Admin"):
    """Update or insert a human review entry into review_log.csv."""
    df = load_review()
    if df.empty:
        df = pd.DataFrame(columns=["case_id", "ai_root_cause", "ai_confidence", "human_verdict", "corrected_root_cause", "reviewer_notes"])

    ai_df = load_ai_responses()
    ai_root = "N/A"
    ai_conf = "high"
    if not ai_df.empty and "case_id" in ai_df.columns:
        match = ai_df[ai_df["case_id"] == case_id]
        if not match.empty:
            ai_root = match.iloc[0].get("root_cause", "N/A")
            ai_conf = match.iloc[0].get("confidence", "high")

    if case_id in df["case_id"].values:
        df.loc[df["case_id"] == case_id, "human_verdict"] = verdict
        df.loc[df["case_id"] == case_id, "corrected_root_cause"] = corrected_root_cause
        df.loc[df["case_id"] == case_id, "reviewer_notes"] = notes
    else:
        new_row = {
            "case_id": case_id,
            "ai_root_cause": ai_root,
            "ai_confidence": ai_conf,
            "human_verdict": verdict,
            "corrected_root_cause": corrected_root_cause,
            "reviewer_notes": notes,
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(REVIEW_CSV, index=False)
    st.cache_data.clear()


def add_live_case_to_database(symptom: str, show_output: str, ai_result: dict) -> str:
    """Save a live diagnosis into cases.csv, ai_responses.csv, and review_log.csv so it appears across all pages."""
    c_df = load_cases()
    existing_live = [str(cid) for cid in c_df["case_id"].values if str(cid).startswith("LIVE-")]
    live_count = len(existing_live) + 1
    new_cid = f"LIVE-{live_count:03d}"

    # 1. Append to cases.csv
    new_case = {
        "case_id": new_cid,
        "category": "Live-Query",
        "symptom": symptom,
        "topology_note": "On-demand diagnosis from web console",
        "show_output": show_output,
        "expected_fault": ai_result.get("root_cause", "N/A"),
        "osi_layer": ai_result.get("osi_layer", "Layer 3"),
        "concept_tag": "live-query",
        "severity": "High",
    }
    c_df = pd.concat([c_df, pd.DataFrame([new_case])], ignore_index=True)
    c_df.to_csv(CASES_CSV, index=False)

    # 2. Append to sample_ai_responses.csv (and ai_responses.csv if exists)
    ai_row = {
        "case_id": new_cid,
        "root_cause": ai_result.get("root_cause", "N/A"),
        "osi_layer": ai_result.get("osi_layer", "Layer 3"),
        "confidence": ai_result.get("confidence", "high"),
        "evidence": ai_result.get("evidence", "N/A"),
        "next_command": ai_result.get("next_command", "N/A"),
        "fix_steps": json.dumps(ai_result.get("fix_steps", [])),
    }
    if SAMPLE_AI_CSV.exists():
        ai_sample = pd.read_csv(SAMPLE_AI_CSV)
        ai_sample = pd.concat([ai_sample, pd.DataFrame([ai_row])], ignore_index=True)
        ai_sample.to_csv(SAMPLE_AI_CSV, index=False)

    if LIVE_AI_CSV.exists():
        ai_live = pd.read_csv(LIVE_AI_CSV)
        ai_live = pd.concat([ai_live, pd.DataFrame([ai_row])], ignore_index=True)
        ai_live.to_csv(LIVE_AI_CSV, index=False)

    # 3. Append to review_log.csv
    save_review_entry(
        new_cid,
        "Pending",
        "",
        f"Live query submitted: {symptom[:50]}...",
        reviewer="Network Admin"
    )

    st.cache_data.clear()
    return new_cid


# ── Groq API Call ─────────────────────────────────────────────────────────────
def get_api_key():
    """Get API key safely without crashing on missing local secrets."""
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key

    env_path = ROOT / ".env"
    if env_path.exists():
        for line in open(env_path, "r", encoding="utf-8"):
            if line.strip().startswith("GROQ_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key

    return None


SYSTEM_PROMPT = """You are NetSage AI, a network-troubleshooting assistant for Cisco-style lab
networks (routers, switches, VLANs, DHCP, DNS, routing, ACLs, NAT, wireless, STP, EtherChannel, HSRP, IPv6, QoS).

You will be given a symptom description and raw show-command / config output evidence.

Your job is ONLY to propose a diagnosis. You never claim a fix has been applied.
A human reviewer always approves, edits, or rejects your answer before any change is made.

Return ONLY valid JSON with this exact schema:
{
  "root_cause": "<one sentence, specific fault>",
  "osi_layer": "<e.g. Layer 2, Layer 3, Layer 3/4, Layer 7>",
  "confidence": "<low | medium | high>",
  "evidence": "<1-3 sentences citing the specific show-output lines>",
  "next_command": "<the single next show/debug command a human should run to confirm>",
  "fix_steps": ["<step 1>", "<step 2>", "..."]
}"""


def diagnose_live(symptom: str, show_output: str, api_key: str) -> dict:
    """Call Groq API for a live diagnosis."""
    try:
        from groq import Groq
    except ImportError:
        return {"error": "groq package not installed. Run: pip install groq"}

    client = Groq(api_key=api_key)
    user_msg = f"Symptom: {symptom}\n\nEvidence:\n{show_output}\n\nReturn the JSON diagnosis now."

    try:
        resp = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content or ""

        cleaned = text.strip()
        if cleaned.startswith("```"):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

        return json.loads(cleaned)

    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response as JSON", "raw": text}
    except Exception as e:
        return {"error": str(e)}


# ── Sidebar ───────────────────────────────────────────────────────────────────
cases_df = load_cases()
ai_df = load_ai_responses()
review_df = load_review()

with st.sidebar:
    st.markdown("### 🌐 NetSage AI")
    st.markdown("##### Network Intelligence Console")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🌐 Console", "📊 Dashboard", "🔍 Live Diagnose", "📋 Case Directory"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    if page == "🌐 Console" and not cases_df.empty:
        st.markdown("##### CASE SELECTOR")
        case_options = [f"{row['case_id']} · {row['category']} · {row['concept_tag']}" for _, row in cases_df.iterrows()]
        selected_case_str = st.selectbox("Select Diagnostic Case", case_options, label_visibility="collapsed")
        selected_cid = selected_case_str.split(" · ")[0]

        # Case Metadata Badges on Sidebar
        selected_case_row = cases_df[cases_df["case_id"] == selected_cid].iloc[0]
        sev = str(selected_case_row["severity"]).upper()
        sev_cls = str(selected_case_row["severity"]).lower()
        osi = selected_case_row["osi_layer"]
        concept = selected_case_row["concept_tag"]

        st.markdown(f"<span class='badge-tag badge-{sev_cls}'>{sev} SEVERITY</span>", unsafe_allow_html=True)
        st.markdown(f"**OSI:** {osi}")
        st.markdown(f"**Concept:** `{concept}`")
    else:
        selected_cid = "C001"

    st.markdown("---")
    st.markdown(
        "<div style='color: rgba(255,255,255,0.4); font-size: 0.72rem; text-align: center;'>"
        "Cisco VIP Internship · Evaluation Layer<br>"
        "50 Diagnostic Scenarios · Lab-Oriented Prototype</div>",
        unsafe_allow_html=True,
    )


# ── PAGE 1: CONSOLE (Single-Case Intelligence Console matching Friend's UI) ────
if page == "🌐 Console":

    # Hero Banner
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-kicker">Cisco VIP Internship · Network Intelligence</div>
            <div class="hero-title">NetSage AI</div>
            <div class="hero-subtitle">
                AI-assisted network troubleshooting console combining structured evidence, deterministic checks,
                explainable diagnosis, and a human approval gate.
            </div>
            <div class="status-online">
                <div class="status-dot"></div>
                LOCAL DIAGNOSTIC CONSOLE · ONLINE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not cases_df.empty:
        c_row = cases_df[cases_df["case_id"] == selected_cid].iloc[0]
        ai_match = ai_df[ai_df["case_id"] == selected_cid] if not ai_df.empty and "case_id" in ai_df.columns else pd.DataFrame()
        rev_match = review_df[review_df["case_id"] == selected_cid] if not review_df.empty and "case_id" in review_df.columns else pd.DataFrame()

        # 5 Top Metric Cards
        c1, c2, c3, c4, c5 = st.columns(5)
        case_idx = cases_df[cases_df["case_id"] == selected_cid].index[0] + 1
        conf_val = ai_match.iloc[0].get("confidence", "High").capitalize() if not ai_match.empty else "High"

        with c1:
            st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>CASE</div><div class='metric-grid-value'>{selected_cid}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>SEVERITY</div><div class='metric-grid-value'>{c_row['severity']}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>OSI</div><div class='metric-grid-value'>{c_row['osi_layer']}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>AI CONFIDENCE</div><div class='metric-grid-value'>{conf_val}</div></div>", unsafe_allow_html=True)
        with c5:
            st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>CASE INDEX</div><div class='metric-grid-value'>{case_idx:02d}/50</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Step-by-Step Pipeline Tabs
        t1, t2, t3, t4, t5 = st.tabs([
            "01 Evidence",
            "02 Rule Scan",
            "03 AI Diagnosis",
            "04 Human Gate",
            "05 Verification",
        ])

        # TAB 1: EVIDENCE
        with t1:
            st.markdown("<div class='section-header'><span class='section-number'>01</span> Troubleshooting Evidence</div>", unsafe_allow_html=True)

            # Interactive Topology Explorer
            st.markdown("##### 🗺️ Interactive Topology Explorer")
            tcol1, tcol2, tcol3, tcol4 = st.columns(4)
            selected_topo = st.session_state.get("console_topo", "Client")

            with tcol1:
                if st.button("💻 Client", use_container_width=True):
                    st.session_state["console_topo"] = "Client"
                    selected_topo = "Client"
            with tcol2:
                if st.button("🔌 Access Switch", use_container_width=True):
                    st.session_state["console_topo"] = "Access Switch"
                    selected_topo = "Access Switch"
            with tcol3:
                if st.button("🛣️ Router / L3", use_container_width=True):
                    st.session_state["console_topo"] = "Router / L3"
                    selected_topo = "Router / L3"
            with tcol4:
                if st.button("🖥️ Server", use_container_width=True):
                    st.session_state["console_topo"] = "Server"
                    selected_topo = "Server"

            topo_info = {
                "Client": ("Client Endpoint Scope", "Start with local addressing, ARP, interface and gateway reachability."),
                "Access Switch": ("Access Switch Scope (Layer 2)", "Inspect port VLAN assignments, trunk allowed-vlan ranges, and STP state."),
                "Router / L3": ("Router / Gateway Scope (Layer 3)", "Inspect subinterface status, IP routing table, ACLs, NAT, and DHCP pools."),
                "Server": ("Server & Infrastructure Services Scope", "Inspect listener ports, static IP configuration, and service availability."),
            }
            t_title, t_desc = topo_info.get(selected_topo, topo_info["Client"])
            st.info(f"**Selected:** `{selected_topo}` — {t_desc}")

            st.markdown("<br>", unsafe_allow_html=True)
            col_sym, col_show = st.columns([1, 1])
            with col_sym:
                st.markdown("##### OBSERVED SYMPTOM")
                st.markdown(f"> {c_row['symptom']}")
                st.markdown(f"**Topology Context:** {c_row['topology_note']}")
            with col_show:
                st.markdown("##### CISCO SHOW-COMMAND EVIDENCE")
                st.code(c_row["show_output"], language="text")

        # TAB 2: RULE SCAN
        with t2:
            st.markdown("<div class='section-header'><span class='section-number'>02</span> Deterministic Rule Evidence</div>", unsafe_allow_html=True)
            import re
            evidence_text = str(c_row['show_output']) + "\n" + str(c_row['symptom']) + "\n" + str(c_row['topology_note'])
            rule_findings = []

            for m in re.finditer(r"^(?P<iface>\S+).{0,40}?\b(administratively down|down)\b", evidence_text, re.M):
                line = m.group(0).strip()
                if "Status" not in line and "Protocol" not in line:
                    rule_findings.append(f"interface_down: Interface/line reporting down: '{line}'")

            gateways = re.findall(r"Default Gateway:\s*(\d{1,3}(?:\.\d{1,3}){3})", evidence_text)
            iface_ips = [m[1] for m in re.findall(r"^(?P<iface>\S+)\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+(?P<status>up|down|administratively down)\s+(?P<proto>up|down)", evidence_text, re.M)]
            for gw in gateways:
                if iface_ips and gw not in iface_ips:
                    rule_findings.append(f"gateway_mismatch: Configured default gateway {gw} does not match any router interface IP found ({iface_ips}).")

            mentioned = {int(v) for v in re.findall(r"VLAN\s?(\d+)", evidence_text, re.I)}
            trunks = re.findall(r"Gi\S*\s+([\d,\-]+)\s*$", evidence_text, re.M)
            for vid in mentioned:
                if trunks:
                    in_trunk = False
                    for t_str in trunks:
                        for part in t_str.split(","):
                            part = part.strip()
                            if "-" in part:
                                lo, hi = part.split("-")
                                if int(lo) <= vid <= int(hi):
                                    in_trunk = True
                            elif part.isdigit() and int(part) == vid:
                                in_trunk = True
                    if not in_trunk:
                        rule_findings.append(f"missing_vlan: VLAN {vid} is referenced but omitted from trunk allowed-vlan range {trunks}.")

            if "(no route to" in evidence_text:
                m_route = re.search(r"\(no route to (\d{1,3}(?:\.\d{1,3}){3}/\d{1,2})\)", evidence_text)
                if m_route:
                    rule_findings.append(f"missing_route: Routing table has no entry for {m_route.group(1)}.")

            masks = re.findall(r"Subnet Mask:\s*(\d{1,3}(?:\.\d{1,3}){3})", evidence_text)
            prose_masks = re.findall(r"mask\s*/(\d{1,2})", evidence_text, re.I)
            if masks and prose_masks:
                rule_findings.append(f"mask_mismatch: Evidence explicitly calls out a differing mask: /{prose_masks[0]}")

            if rule_findings:
                for finding in rule_findings:
                    st.warning(f"⚠️ **Automated Rule Scan:** {finding}")
            else:
                st.info("ℹ️ **Evidence Scan · INFO:** No lightweight rule indicator triggered. Case requires cognitive LLM diagnosis.")
            st.caption("The complete deterministic implementation is available in `scripts/rule_checker.py`.")

        # TAB 3: AI DIAGNOSIS
        with t3:
            st.markdown("<div class='section-header'><span class='section-number'>03</span> NetSage AI Diagnosis</div>", unsafe_allow_html=True)
            if not ai_match.empty:
                ai_r = ai_match.iloc[0]
                st.markdown(f"<div class='root-cause-box'><strong>ROOT CAUSE:</strong><br>{ai_r.get('root_cause', 'N/A')}</div>", unsafe_allow_html=True)

                col_e1, col_e2 = st.columns([2, 1])
                with col_e1:
                    st.markdown(f"**EVIDENCE USED:**")
                    st.markdown(f"> {ai_r.get('evidence', 'N/A')}")
                    st.markdown(f"**NEXT COMMAND TO CONFIRM:**")
                    st.code(ai_r.get("next_command", "N/A"), language="text")
                with col_e2:
                    st.markdown(f"**Confidence:** `{ai_r.get('confidence', 'high')}`")
                    st.markdown(f"**OSI Layer:** `{ai_r.get('osi_layer', 'N/A')}`")

                try:
                    steps = json.loads(str(ai_r.get("fix_steps", "[]")))
                    if steps:
                        st.markdown("**FIX STEPS:**")
                        for i, step in enumerate(steps, 1):
                            st.markdown(f"  {i}. {step}")
                except Exception:
                    pass
            else:
                st.markdown(f"<div class='root-cause-box'><strong>EXPECTED FAULT:</strong><br>{c_row['expected_fault']}</div>", unsafe_allow_html=True)

        # TAB 4: HUMAN GATE (Matching Friend's Interactive Review Form)
        with t4:
            st.markdown("<div class='section-header'><span class='section-number'>04</span> Human Review Gate</div>", unsafe_allow_html=True)
            st.caption("The AI does not autonomously modify network devices. A reviewer makes the final decision before any corrective action.")

            curr_verdict = rev_match.iloc[0]["human_verdict"] if not rev_match.empty else "Pending"
            curr_corrected = rev_match.iloc[0].get("corrected_root_cause", "") if not rev_match.empty and pd.notna(rev_match.iloc[0].get("corrected_root_cause")) else ""
            curr_notes = rev_match.iloc[0].get("reviewer_notes", "") if not rev_match.empty and pd.notna(rev_match.iloc[0].get("reviewer_notes")) else ""

            verdict_opts = ["Pending", "Accepted", "Edited", "Rejected"]
            v_idx = verdict_opts.index(curr_verdict) if curr_verdict in verdict_opts else 0

            new_verdict = st.selectbox("Decision", verdict_opts, index=v_idx, key=f"v_select_{selected_cid}")
            new_notes = st.text_area("Reviewer notes", value=curr_notes, placeholder="Explain the decision, correction, or verification.", key=f"v_notes_{selected_cid}", height=90)
            new_corrected = st.text_input("Corrected Root Cause (if Edited/Rejected)", value=curr_corrected, key=f"v_corr_{selected_cid}")
            reviewer_name = st.text_input("Reviewer Name", value="Network Administrator", key=f"v_name_{selected_cid}")

            if st.button("Save Human Review", type="primary", key=f"save_btn_{selected_cid}"):
                save_review_entry(selected_cid, new_verdict, new_corrected, new_notes, reviewer_name)
                st.success(f"✅ Saved Human Review for case {selected_cid}!")
                st.rerun()

        # TAB 5: VERIFICATION
        with t5:
            st.markdown("<div class='section-header'><span class='section-number'>05</span> Reference & Verification</div>", unsafe_allow_html=True)
            st.markdown(f"**Known Correct Ground Truth Fault:**")
            st.markdown(f"> {c_row['expected_fault']}")
            st.markdown("**Verification Commands:**")
            st.code("show ip interface brief\nshow vlan brief\nshow ip route\nping <target>", language="text")


# ── PAGE 2: DASHBOARD ────────────────────────────────────────────────────────
elif page == "📊 Dashboard":
    st.markdown("## 📊 Executive & Responsible AI Dashboard")
    st.markdown("Aggregate analytics, AI accuracy metrics, and human oversight statistics.")
    st.markdown("---")

    # KPI Summary Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    total_len = len(cases_df)
    reviewed_df = review_df[review_df["human_verdict"] != "Pending"] if not review_df.empty else pd.DataFrame()
    n_reviewed = len(reviewed_df)
    n_accepted = len(review_df[review_df["human_verdict"] == "Accepted"]) if not review_df.empty else 0
    n_edited = len(review_df[review_df["human_verdict"] == "Edited"]) if not review_df.empty else 0
    n_rejected = len(review_df[review_df["human_verdict"] == "Rejected"]) if not review_df.empty else 0
    agree_pct = f"{(n_accepted / n_reviewed * 100):.1f}%" if n_reviewed > 0 else "N/A"

    with c1:
        st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>TOTAL CASES</div><div class='metric-grid-value'>{total_len}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>REVIEWED</div><div class='metric-grid-value'>{n_reviewed}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>ACCEPTED</div><div class='metric-grid-value' style='color:#4ade80;'>{n_accepted}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>EDITED/REJECTED</div><div class='metric-grid-value' style='color:#fcd34d;'>{n_edited + n_rejected}</div></div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='metric-grid-card'><div class='metric-grid-label'>AI-HUMAN AGREEMENT</div><div class='metric-grid-value'>{agree_pct}</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cat_counts = cases_df["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig1 = px.bar(cat_counts, x="Category", y="Count", title="Cases by Issue Type", color="Count", color_continuous_scale=["#4f46e5", "#818cf8", "#a78bfa"])
        fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="rgba(255,255,255,0.7)", title_font_color="#818cf8", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        sev_counts = cases_df["severity"].value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]
        colors = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
        fig2 = px.pie(sev_counts, names="Severity", values="Count", title="Cases by Severity", color="Severity", color_discrete_map=colors, hole=0.4)
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="rgba(255,255,255,0.7)", title_font_color="#818cf8")
        st.plotly_chart(fig2, use_container_width=True)

    if not review_df.empty:
        v_counts = review_df["human_verdict"].value_counts().reset_index()
        v_counts.columns = ["Verdict", "Count"]
        colors_v = {"Accepted": "#22c55e", "Edited": "#eab308", "Rejected": "#ef4444", "Pending": "#94a3b8"}
        fig3 = px.bar(v_counts, x="Verdict", y="Count", title="AI vs Human Review Outcome", color="Verdict", color_discrete_map=colors_v)
        fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="rgba(255,255,255,0.7)", title_font_color="#818cf8", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)


# ── PAGE 3: LIVE DIAGNOSE ────────────────────────────────────────────────────
elif page == "🔍 Live Diagnose":
    st.markdown("## 🔍 Live Diagnose")
    st.markdown("Paste your Cisco `show` command output below and get an **instant AI diagnosis**.")
    st.markdown("---")

    api_key = get_api_key()
    if not api_key:
        st.warning("⚠️ No Groq API key found. Enter it below or add it to `.env`.")
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    symptom = st.text_area("🔴 Describe the symptom", placeholder="e.g., PCs in VLAN 10 cannot ping each other across switches", height=80)
    show_output = st.text_area("📟 Paste show-command output", placeholder="e.g.,\nSW1# show interfaces trunk\n...", height=200)

    if st.button("🚀 Diagnose Now", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please provide a Groq API key.")
        elif not symptom.strip():
            st.error("Please describe the symptom.")
        elif not show_output.strip():
            st.error("Please paste the show-command output.")
        else:
            with st.spinner("🧠 AI is analyzing the evidence..."):
                st.session_state["last_live_result"] = diagnose_live(symptom, show_output, api_key)
                st.session_state["last_live_symptom"] = symptom
                st.session_state["last_live_show"] = show_output

    if "last_live_result" in st.session_state and st.session_state["last_live_result"]:
        result = st.session_state["last_live_result"]
        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.success("✅ Diagnosis complete!")
            st.markdown(f"<div class='root-cause-box'><strong>ROOT CAUSE:</strong><br>{result.get('root_cause', 'N/A')}</div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Confidence:** `{result.get('confidence', 'N/A')}`")
                st.markdown(f"**Evidence:** {result.get('evidence', 'N/A')}")
            with col2:
                st.markdown(f"**OSI Layer:** `{result.get('osi_layer', 'N/A')}`")
                st.markdown(f"**Next Command:** `{result.get('next_command', 'N/A')}`")

            steps = result.get("fix_steps", [])
            if steps:
                st.markdown("**Fix Steps:**")
                for i, step in enumerate(steps, 1):
                    st.markdown(f"  {i}. {step}")

            st.markdown("---")
            if st.button("📥 Forward to Human Review Queue"):
                new_cid = add_live_case_to_database(
                    st.session_state.get('last_live_symptom', ''),
                    st.session_state.get('last_live_show', ''),
                    result
                )
                st.success(f"✅ Submitted as case **{new_cid}**! Select **{new_cid}** in the **CASE SELECTOR** on `🌐 Console` or view it in the **📋 Case Directory** to audit and sign off.")


# ── PAGE 4: CASE DIRECTORY ───────────────────────────────────────────────────
elif page == "📋 Case Directory":
    st.markdown("## 📋 Diagnostic Case Directory")
    st.markdown("Full searchable index of all 50 troubleshooting scenarios in `data/cases.csv`.")
    st.markdown("---")

    if not cases_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            cat_f = st.multiselect("Filter Category", sorted(cases_df["category"].unique()), default=sorted(cases_df["category"].unique()))
        with col2:
            sev_f = st.multiselect("Filter Severity", ["Critical", "High", "Medium", "Low"], default=["Critical", "High", "Medium", "Low"])

        filt = cases_df[(cases_df["category"].isin(cat_f)) & (cases_df["severity"].isin(sev_f))]
        st.markdown(f"**Showing {len(filt)} of {len(cases_df)} cases**")

        st.dataframe(
            filt[["case_id", "category", "severity", "osi_layer", "concept_tag", "symptom", "expected_fault"]],
            use_container_width=True,
            hide_index=True,
        )
