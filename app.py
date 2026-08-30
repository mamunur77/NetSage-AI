"""
NetSage AI — Streamlit Web Dashboard
=====================================
A web-based frontend for the NetSage AI network troubleshooting tool.

Features:
  - 📊 Dashboard with live Plotly charts and KPIs (50 cases)
  - 📋 Browse 50 troubleshooting cases with Interactive Topology Explorer & Step-by-Step Pipeline
  - 🤖 View AI diagnosis results
  - 🔍 Live Diagnose: paste show-command output → get instant AI diagnosis
  - ✅ Human Review: interactive form to submit / update Accepted, Edited, or Rejected verdicts

Run locally:
    python -m streamlit run app.py

Deploy on Streamlit Cloud:
    Push to GitHub → connect at share.streamlit.io
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
    page_title="NetSage AI — Network Troubleshooter",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a3e 0%, #0f0c29 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
    }
    .metric-value {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 6px 0;
    }
    .metric-label {
        color: rgba(255,255,255,0.6);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Diagnosis card */
    .diagnosis-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(99,102,241,0.02) 100%);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }

    /* Badge styles */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-critical { background: rgba(239,68,68,0.3); color: #fca5a5; }
    .badge-high { background: rgba(239,68,68,0.2); color: #fca5a5; }
    .badge-medium { background: rgba(251,191,36,0.2); color: #fcd34d; }
    .badge-low { background: rgba(34,197,94,0.2); color: #86efac; }
    .badge-ok { background: rgba(34,197,94,0.2); color: #86efac; }
    .badge-fail { background: rgba(239,68,68,0.2); color: #fca5a5; }

    /* Hero section */
    .hero {
        text-align: center;
        padding: 15px 0 25px 0;
    }
    .hero h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 50%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .hero p {
        color: rgba(255,255,255,0.5);
        font-size: 1.05rem;
    }

    /* Topology Card */
    .topo-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 8px 16px;
        border: 1px solid rgba(255,255,255,0.1);
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99,102,241,0.2) !important;
        border-color: rgba(99,102,241,0.4) !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Data Loaders ──────────────────────────────────────────────────────────────
def load_cases():
    if CASES_CSV.exists():
        return pd.read_csv(CASES_CSV)
    return pd.DataFrame()


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


def save_review_entry(case_id, verdict, corrected_root_cause, notes):
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
with st.sidebar:
    st.markdown("### 🌐 NetSage AI")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📋 Cases", "🤖 AI Diagnoses", "🔍 Live Diagnose", "✅ Human Review"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        "<div style='color: rgba(255,255,255,0.4); font-size: 0.75rem; text-align: center;'>"
        "Cisco Applied AI Project<br>50 Diagnostic Scenarios<br>Powered by Groq + LLM</div>",
        unsafe_allow_html=True,
    )


# ── PAGE: Dashboard ──────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.markdown(
        "<div class='hero'><h1>🌐 NetSage AI</h1>"
        "<p>AI-Powered Network Troubleshooting & Responsible AI Oversight Console</p></div>",
        unsafe_allow_html=True,
    )

    cases = load_cases()
    ai = load_ai_responses()
    review = load_review()

    # KPI Cards
    total_cases = len(cases)
    ai_parsed = int(ai["parse_ok"].sum()) if not ai.empty and "parse_ok" in ai.columns else len(ai)
    ai_rate = f"{ai_parsed / total_cases * 100:.0f}%" if total_cases > 0 else "100%"

    accepted = len(review[review["human_verdict"] == "Accepted"]) if not review.empty else 0
    edited = len(review[review["human_verdict"] == "Edited"]) if not review.empty else 0
    rejected = len(review[review["human_verdict"] == "Rejected"]) if not review.empty else 0
    agree_rate = f"{accepted / len(review) * 100:.0f}%" if not review.empty and len(review) > 0 else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Total Cases</div>"
            f"<div class='metric-value'>{total_cases}</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>AI Parse Rate</div>"
            f"<div class='metric-value'>{ai_rate}</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>AI Agreement</div>"
            f"<div class='metric-value'>{agree_rate}</div></div>",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Cases Corrected</div>"
            f"<div class='metric-value'>{edited + rejected}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    if not cases.empty:
        col1, col2 = st.columns(2)

        with col1:
            cat_counts = cases["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            fig1 = px.bar(
                cat_counts, x="Category", y="Count",
                title="Cases by Issue Type",
                color="Count",
                color_continuous_scale=["#4f46e5", "#818cf8", "#a78bfa"],
            )
            fig1.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="rgba(255,255,255,0.7)",
                title_font_color="#818cf8",
                showlegend=False,
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            sev_counts = cases["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            colors = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
            fig2 = px.pie(
                sev_counts, names="Severity", values="Count",
                title="Cases by Severity",
                color="Severity",
                color_discrete_map=colors,
                hole=0.4,
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="rgba(255,255,255,0.7)",
                title_font_color="#818cf8",
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Review outcome chart
    if not review.empty:
        verdict_counts = review["human_verdict"].value_counts().reset_index()
        verdict_counts.columns = ["Verdict", "Count"]
        colors_v = {"Accepted": "#22c55e", "Edited": "#eab308", "Rejected": "#ef4444"}
        fig3 = px.bar(
            verdict_counts, x="Verdict", y="Count",
            title="AI vs Human Review Outcome (Responsible AI Audit)",
            color="Verdict",
            color_discrete_map=colors_v,
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="rgba(255,255,255,0.7)",
            title_font_color="#818cf8",
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)


# ── PAGE: Cases ──────────────────────────────────────────────────────────────
elif page == "📋 Cases":
    st.markdown("## 📋 Troubleshooting Cases & Topology Explorer")
    st.markdown("Browse all 50 network troubleshooting scenarios with step-by-step pipeline inspection.")
    st.markdown("---")

    cases = load_cases()
    ai_df = load_ai_responses()
    review_df = load_review()

    if cases.empty:
        st.warning("No cases found. Run `python scripts/generate_cases.py` first.")
    else:
        # Interactive Topology Explorer Component
        st.markdown("### 🗺️ Interactive Topology Explorer")
        st.markdown("Select a network component below to inspect its troubleshooting scope & common commands:")

        tcol1, tcol2, tcol3, tcol4 = st.columns(4)
        selected_topo = st.session_state.get("selected_topo", "Client")

        with tcol1:
            if st.button("💻 Client / Endpoint", use_container_width=True):
                st.session_state["selected_topo"] = "Client"
                selected_topo = "Client"
        with tcol2:
            if st.button("🔌 Access Switch (L2)", use_container_width=True):
                st.session_state["selected_topo"] = "Access Switch"
                selected_topo = "Access Switch"
        with tcol3:
            if st.button("🛣️ Router / L3 Switch", use_container_width=True):
                st.session_state["selected_topo"] = "Router / L3"
                selected_topo = "Router / L3"
        with tcol4:
            if st.button("🖥️ Server / Cloud", use_container_width=True):
                st.session_state["selected_topo"] = "Server"
                selected_topo = "Server"

        topo_info = {
            "Client": ("Client / Endpoint Diagnostics", "Inspect local IP configuration, DHCP leases, gateway reachability, and DNS resolution.", ["ipconfig /all", "ping <gateway>", "nslookup <domain>", "tracert <target>"]),
            "Access Switch": ("Layer 2 Access Switch Diagnostics", "Inspect port VLAN assignments, trunk allowed-vlan ranges, native VLAN tags, STP state, and port security.", ["show vlan brief", "show interfaces trunk", "show spanning-tree vlan X", "show port-security interface X"]),
            "Router / L3": ("Layer 3 Gateway & Routing Diagnostics", "Inspect subinterface status, DHCP pools, static/dynamic routes (OSPF/BGP), ACL rule order, and NAT translations.", ["show ip interface brief", "show ip route", "show access-lists", "show ip nat translations", "show ip dhcp pool"]),
            "Server": ("Server & Infrastructure Services", "Inspect listener ports, static IP settings, DNS zone records, and TACACS+/AAA authentication response.", ["show ip http server", "nslookup <internal-name>", "ping <server-ip>"]),
        }

        title, desc, cmds = topo_info.get(selected_topo, topo_info["Client"])
        st.markdown(
            f"<div class='topo-box'>"
            f"<strong style='color:#818cf8;'>{title}</strong><br>"
            f"<span style='color:rgba(255,255,255,0.7); font-size:0.9rem;'>{desc}</span><br><br>"
            f"<strong>Key Diagnostic Commands:</strong> <code>{'</code> | <code>'.join(cmds)}</code>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Filters
        col1, col2 = st.columns(2)
        with col1:
            cat_filter = st.multiselect("Filter by Category", sorted(cases["category"].unique()), default=sorted(cases["category"].unique()))
        with col2:
            sev_filter = st.multiselect("Filter by Severity", ["Critical", "High", "Medium", "Low"], default=["Critical", "High", "Medium", "Low"])

        filtered = cases[(cases["category"].isin(cat_filter)) & (cases["severity"].isin(sev_filter))]
        st.markdown(f"**Showing {len(filtered)} of {len(cases)} cases**")

        for _, row in filtered.iterrows():
            cid = row["case_id"]
            sev_class = str(row["severity"]).lower() if pd.notna(row["severity"]) else "medium"

            # Match AI and Review entries
            ai_match = ai_df[ai_df["case_id"] == cid] if not ai_df.empty and "case_id" in ai_df.columns else pd.DataFrame()
            rev_match = review_df[review_df["case_id"] == cid] if not review_df.empty and "case_id" in review_df.columns else pd.DataFrame()

            verdict = rev_match.iloc[0]["human_verdict"] if not rev_match.empty else "Pending"
            v_icon = {"Accepted": "✅", "Edited": "✏️", "Rejected": "❌"}.get(verdict, "⏳")

            with st.expander(f"**{cid}** — {row['category']} | {v_icon} {verdict} | {row['symptom'][:70]}..."):
                st.markdown(f"**Severity:** <span class='badge badge-{sev_class}'>{row['severity']}</span> | **OSI Layer:** `{row['osi_layer']}` | **Concept:** `{row['concept_tag']}`", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                # Step-by-Step Pipeline View
                t1, t2, t3, t4, t5 = st.tabs(["01 Evidence", "02 Rule Scan", "03 AI Diagnosis", "04 Human Gate", "05 Verification"])

                with t1:
                    st.markdown(f"**Symptom:** {row['symptom']}")
                    st.markdown(f"**Topology Context:** {row['topology_note']}")
                    st.code(row["show_output"], language="text")

                with t2:
                    st.markdown("**Deterministic Rule Scan:**")
                    # Run live deterministic checks on the case's evidence
                    import re
                    evidence_text = str(row['show_output']) + "\n" + str(row['symptom']) + "\n" + str(row['topology_note'])
                    rule_findings = []

                    # 1. Interface down check
                    for m in re.finditer(r"^(?P<iface>\S+).{0,40}?\b(administratively down|down)\b", evidence_text, re.M):
                        line = m.group(0).strip()
                        if "Status" not in line and "Protocol" not in line:
                            rule_findings.append(f"interface_down: Interface/line reporting down: '{line}'")

                    # 2. Gateway mismatch check
                    gateways = re.findall(r"Default Gateway:\s*(\d{1,3}(?:\.\d{1,3}){3})", evidence_text)
                    iface_ips = [m[1] for m in re.findall(r"^(?P<iface>\S+)\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+(?P<status>up|down|administratively down)\s+(?P<proto>up|down)", evidence_text, re.M)]
                    for gw in gateways:
                        if iface_ips and gw not in iface_ips:
                            rule_findings.append(f"gateway_mismatch: Configured default gateway {gw} does not match any router interface IP found ({iface_ips}).")

                    # 3. Missing VLAN check
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

                    # 4. Missing route check
                    if "(no route to" in evidence_text:
                        m_route = re.search(r"\(no route to (\d{1,3}(?:\.\d{1,3}){3}/\d{1,2})\)", evidence_text)
                        if m_route:
                            rule_findings.append(f"missing_route: Routing table has no entry for {m_route.group(1)}.")

                    # 5. Mask mismatch check
                    masks = re.findall(r"Subnet Mask:\s*(\d{1,3}(?:\.\d{1,3}){3})", evidence_text)
                    prose_masks = re.findall(r"mask\s*/(\d{1,2})", evidence_text, re.I)
                    if masks and prose_masks:
                        rule_findings.append(f"mask_mismatch: Evidence explicitly calls out a differing mask: /{prose_masks[0]}")

                    if rule_findings:
                        for finding in rule_findings:
                            st.warning(f"⚠️ **Automated Rule Match:** {finding}")
                    else:
                        st.info("ℹ️ No simple configuration syntax error triggered; case requires cognitive LLM analysis.")

                with t3:
                    if not ai_match.empty:
                        ai_r = ai_match.iloc[0]
                        st.markdown(f"**AI Proposed Cause:** {ai_r.get('root_cause', 'N/A')}")
                        st.markdown(f"**AI Confidence:** `{ai_r.get('confidence', 'high')}`")
                        st.markdown(f"**Evidence Cites:** {ai_r.get('evidence', 'N/A')}")
                        st.markdown(f"**Next Command:** `{ai_r.get('next_command', 'N/A')}`")
                    else:
                        st.markdown(f"**Expected Fault:** {row['expected_fault']}")

                with t4:
                    st.markdown(f"**Human Verdict:** **{v_icon} {verdict}**")
                    if not rev_match.empty:
                        st.markdown(f"**Reviewer Notes:** {rev_match.iloc[0].get('reviewer_notes', 'N/A')}")
                        if pd.notna(rev_match.iloc[0].get('corrected_root_cause')) and str(rev_match.iloc[0].get('corrected_root_cause')).strip():
                            st.markdown(f"**Corrected Root Cause:** {rev_match.iloc[0]['corrected_root_cause']}")

                with t5:
                    st.markdown("**Expected Resolution Steps:**")
                    st.markdown(f"> {row['expected_fault']}")


# ── PAGE: AI Diagnoses ───────────────────────────────────────────────────────
elif page == "🤖 AI Diagnoses":
    st.markdown("## 🤖 AI Diagnosis Results")
    st.markdown("Structured JSON diagnoses returned by the Groq LLM across all 50 cases.")
    st.markdown("---")

    ai = load_ai_responses()
    if ai.empty:
        st.warning("No AI responses found. Run `python scripts/ai_diagnose.py` or `python scripts/generate_ai_and_review.py` first.")
    else:
        st.markdown(f"**Displaying {len(ai)} AI Diagnostic Results**")
        st.markdown("---")

        for _, row in ai.iterrows():
            cid = row["case_id"]
            conf = str(row.get("confidence", "high"))
            conf_class = conf.lower() if conf.lower() in ["high", "medium", "low"] else "medium"

            with st.expander(f"**{cid}** — Confidence: {conf.upper()} | {str(row.get('root_cause', ''))[:75]}..."):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Confidence:** <span class='badge badge-{conf_class}'>{conf}</span>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**OSI Layer:** {row.get('osi_layer', 'N/A')}")
                with col3:
                    st.markdown(f"**Next Command:** `{row.get('next_command', 'N/A')}`")

                st.markdown(f"**Root Cause:** {row.get('root_cause', '')}")
                st.markdown(f"**Evidence Cited:** {row.get('evidence', '')}")

                try:
                    steps = json.loads(str(row.get("fix_steps", "[]")))
                    if steps:
                        st.markdown("**Fix Steps:**")
                        for i, step in enumerate(steps, 1):
                            st.markdown(f"  {i}. {step}")
                except (json.JSONDecodeError, TypeError):
                    st.markdown(f"**Fix Steps:** {row.get('fix_steps', '')}")


# ── PAGE: Live Diagnose ──────────────────────────────────────────────────────
elif page == "🔍 Live Diagnose":
    st.markdown("## 🔍 Live Diagnose")
    st.markdown("Paste your Cisco `show` command output below and get an **instant AI diagnosis**.")
    st.markdown("---")

    api_key = get_api_key()

    if not api_key:
        st.warning("⚠️ No Groq API key found. Enter it below or add it to `.env`.")
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    symptom = st.text_area(
        "🔴 Describe the symptom",
        placeholder="e.g., PCs in VLAN 10 cannot ping each other across switches",
        height=80,
    )

    show_output = st.text_area(
        "📟 Paste show-command output",
        placeholder="""e.g.,
SW1# show interfaces trunk
Port    Mode    Encapsulation   Status    Native vlan
Gi0/1   on      802.1q          trunking  1
Port    Vlans allowed on trunk
Gi0/1   1-9,11-4094""",
        height=200,
    )

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

            st.markdown("<div class='diagnosis-card'>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                conf = result.get("confidence", "unknown")
                conf_class = conf.lower() if conf.lower() in ["high", "medium", "low"] else "medium"
                st.markdown(f"**Confidence:** <span class='badge badge-{conf_class}'>{conf}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**OSI Layer:** {result.get('osi_layer', 'N/A')}")

            st.markdown(f"### 🔍 Root Cause")
            st.markdown(f"> {result.get('root_cause', 'N/A')}")

            st.markdown(f"### 📝 Evidence")
            st.markdown(f"> {result.get('evidence', 'N/A')}")

            st.markdown(f"### 🔧 Next Command to Confirm")
            st.code(result.get("next_command", "N/A"), language="text")

            steps = result.get("fix_steps", [])
            if steps:
                st.markdown("### 🛠️ Fix Steps")
                for i, step in enumerate(steps, 1):
                    st.markdown(f"**{i}.** {step}")

            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("📄 Raw JSON Response"):
                st.json(result)

            st.markdown("---")
            st.markdown("### 🛡️ Human Oversight Gate")
            st.markdown("Submit this AI diagnosis into the Human Review log to review, edit, or sign off on it:")

            if st.button("📥 Forward to Human Review Queue", type="secondary"):
                rev_df = load_review()
                live_id = f"LIVE-{len(rev_df) + 1:03d}"
                save_review_entry(
                    live_id,
                    "Accepted",
                    "",
                    f"Live query logged for symptom: {st.session_state.get('last_live_symptom', '')[:60]}"
                )
                st.success(f"✅ Submitted as case **{live_id}**! Navigate to the **✅ Human Review** page to edit or sign off.")


# ── PAGE: Human Review ───────────────────────────────────────────────────────
elif page == "✅ Human Review":
    st.markdown("## ✅ Human Review & Responsible AI Oversight")
    st.markdown("Audit and submit human review decisions for AI diagnoses directly from the browser.")
    st.markdown("---")

    cases = load_cases()
    review = load_review()

    if review.empty:
        st.warning("No review log found. Run `python scripts/generate_ai_and_review.py` first.")
    else:
        # KPI Summary
        col1, col2, col3 = st.columns(3)
        accepted = len(review[review["human_verdict"] == "Accepted"])
        edited = len(review[review["human_verdict"] == "Edited"])
        rejected = len(review[review["human_verdict"] == "Rejected"])

        with col1:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Accepted</div>"
                f"<div class='metric-value' style='background: linear-gradient(135deg, #22c55e, #16a34a); -webkit-background-clip: text;'>{accepted}</div></div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Edited</div>"
                f"<div class='metric-value' style='background: linear-gradient(135deg, #eab308, #ca8a04); -webkit-background-clip: text;'>{edited}</div></div>",
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Rejected</div>"
                f"<div class='metric-value' style='background: linear-gradient(135deg, #ef4444, #dc2626); -webkit-background-clip: text;'>{rejected}</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Interactive In-App Human Review Submission Form
        with st.expander("✍️ **Submit / Update Human Review Entry**", expanded=True):
            case_list = cases["case_id"].tolist() if not cases.empty else review["case_id"].tolist()
            selected_case = st.selectbox("Select Case ID to Review", case_list)

            current_entry = review[review["case_id"] == selected_case]
            curr_verdict = current_entry.iloc[0]["human_verdict"] if not current_entry.empty else "Accepted"
            curr_corrected = current_entry.iloc[0].get("corrected_root_cause", "") if not current_entry.empty and pd.notna(current_entry.iloc[0].get("corrected_root_cause")) else ""
            curr_notes = current_entry.iloc[0].get("reviewer_notes", "") if not current_entry.empty and pd.notna(current_entry.iloc[0].get("reviewer_notes")) else ""

            v_col1, v_col2 = st.columns(2)
            with v_col1:
                new_verdict = st.selectbox("Human Verdict", ["Accepted", "Edited", "Rejected"], index=["Accepted", "Edited", "Rejected"].index(curr_verdict) if curr_verdict in ["Accepted", "Edited", "Rejected"] else 0)
            with v_col2:
                new_corrected = st.text_input("Corrected Root Cause (if Edited/Rejected)", value=curr_corrected)

            new_notes = st.text_area("Reviewer Audit Notes", value=curr_notes, height=80)

            if st.button("💾 Save Human Review Entry", type="primary"):
                save_review_entry(selected_case, new_verdict, new_corrected, new_notes)
                st.success(f"✅ Successfully updated review for {selected_case}!")
                st.rerun()

        st.markdown("---")

        # Filter by verdict
        verdict_filter = st.multiselect(
            "Filter Review Log by Verdict",
            ["Accepted", "Edited", "Rejected"],
            default=["Accepted", "Edited", "Rejected"],
        )
        filtered = review[review["human_verdict"].isin(verdict_filter)]

        for _, row in filtered.iterrows():
            verdict = row["human_verdict"]
            icon = {"Accepted": "✅", "Edited": "✏️", "Rejected": "❌"}.get(verdict, "❓")

            with st.expander(f"{icon} **{row['case_id']}** — {verdict} | {str(row.get('ai_root_cause', ''))[:60]}..."):
                st.markdown(f"**AI Root Cause:** {row.get('ai_root_cause', 'N/A')}")
                st.markdown(f"**AI Confidence:** `{row.get('ai_confidence', 'N/A')}`")
                st.markdown(f"**Human Verdict:** **{verdict}**")

                if pd.notna(row.get("corrected_root_cause")) and str(row.get("corrected_root_cause")).strip():
                    st.markdown(f"**Corrected Root Cause:** {row['corrected_root_cause']}")

                if pd.notna(row.get("reviewer_notes")) and str(row.get("reviewer_notes")).strip():
                    st.info(f"**Reviewer Notes:** {row['reviewer_notes']}")
