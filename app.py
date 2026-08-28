"""
NetSage AI — Streamlit Web Dashboard
=====================================
A web-based frontend for the NetSage AI network troubleshooting tool.

Features:
  - 📊 Dashboard with live charts and KPIs
  - 📋 Browse all 30 troubleshooting cases
  - 🤖 View AI diagnosis results
  - 🔍 Live Diagnose: paste show-command output → get instant AI diagnosis
  - ✅ Human Review: accept / edit / reject AI answers

Run locally:
    streamlit run app.py

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
AI_RESPONSES_CSV = OUTPUT_DIR / "ai_responses.csv"
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
        padding: 24px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 8px 0;
    }
    .metric-label {
        color: rgba(255,255,255,0.6);
        font-size: 0.85rem;
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
    .diagnosis-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #818cf8;
        margin-bottom: 12px;
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
    .badge-high { background: rgba(239,68,68,0.2); color: #fca5a5; }
    .badge-medium { background: rgba(251,191,36,0.2); color: #fcd34d; }
    .badge-low { background: rgba(34,197,94,0.2); color: #86efac; }
    .badge-ok { background: rgba(34,197,94,0.2); color: #86efac; }
    .badge-fail { background: rgba(239,68,68,0.2); color: #fca5a5; }

    /* Hero section */
    .hero {
        text-align: center;
        padding: 20px 0 30px 0;
    }
    .hero h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 50%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .hero p {
        color: rgba(255,255,255,0.5);
        font-size: 1.1rem;
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
        padding: 8px 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99,102,241,0.2) !important;
        border-color: rgba(99,102,241,0.4) !important;
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
    if AI_RESPONSES_CSV.exists():
        return pd.read_csv(AI_RESPONSES_CSV)
    return pd.DataFrame()


@st.cache_data
def load_review():
    if REVIEW_CSV.exists():
        return pd.read_csv(REVIEW_CSV)
    return pd.DataFrame()


# ── Groq API Call ─────────────────────────────────────────────────────────────
def get_api_key():
    """Get API key from Streamlit secrets, .env file, or sidebar input."""
    # 1. Check Streamlit secrets (for cloud deployment)
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass  # secrets.toml doesn't exist locally, that's fine

    # 2. Check environment variable
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key

    # 3. Check .env file
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in open(env_path, "r", encoding="utf-8"):
            if line.strip().startswith("GROQ_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key

    return None


SYSTEM_PROMPT = """You are NetSage AI, a network-troubleshooting assistant for Cisco-style lab
networks (Packet Tracer topologies: routers, switches, VLANs, DHCP, DNS,
routing, ACLs, NAT, wireless).

You will be given a symptom description and raw show-command / config output evidence.

Your job is ONLY to propose a diagnosis. You never claim a fix has been applied.
A human reviewer always approves, edits, or rejects your answer before any change is made.

Rules:
1. Base your root cause ONLY on evidence present in the show-command output.
2. If the evidence is ambiguous, set confidence to "low" or "medium".
3. Quote the specific line(s) of evidence that support your root cause.
4. Return ONLY valid JSON. No markdown fences, no prose before or after.

Respond with exactly this schema:
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

        # Clean up markdown fences if present
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
        "Cisco Applied AI Project<br>Powered by Groq + LLM</div>",
        unsafe_allow_html=True,
    )


# ── PAGE: Dashboard ──────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.markdown(
        "<div class='hero'><h1>🌐 NetSage AI</h1>"
        "<p>AI-Powered Network Troubleshooting Dashboard</p></div>",
        unsafe_allow_html=True,
    )

    cases = load_cases()
    ai = load_ai_responses()
    review = load_review()

    # KPI Cards
    total_cases = len(cases)
    ai_parsed = int(ai["parse_ok"].sum()) if not ai.empty and "parse_ok" in ai.columns else 0
    ai_rate = f"{ai_parsed / total_cases * 100:.0f}%" if total_cases > 0 else "N/A"

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
            title="AI vs Human Review Outcome",
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
    st.markdown("## 📋 Troubleshooting Cases")
    st.markdown("All 30 network troubleshooting scenarios from the case database.")
    st.markdown("---")

    cases = load_cases()
    if cases.empty:
        st.warning("No cases found. Run `python scripts/generate_cases.py` first.")
    else:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            cat_filter = st.multiselect("Filter by Category", cases["category"].unique(), default=cases["category"].unique())
        with col2:
            sev_filter = st.multiselect("Filter by Severity", cases["severity"].unique(), default=cases["severity"].unique())

        filtered = cases[(cases["category"].isin(cat_filter)) & (cases["severity"].isin(sev_filter))]
        st.markdown(f"**Showing {len(filtered)} of {len(cases)} cases**")

        for _, row in filtered.iterrows():
            sev_class = row["severity"].lower() if pd.notna(row["severity"]) else "medium"
            with st.expander(f"**{row['case_id']}** — {row['category']} | {row['symptom'][:80]}..."):
                st.markdown(f"**Severity:** <span class='badge badge-{sev_class}'>{row['severity']}</span>", unsafe_allow_html=True)
                st.markdown(f"**OSI Layer:** {row['osi_layer']}")
                st.markdown(f"**Symptom:** {row['symptom']}")
                st.markdown(f"**Topology:** {row['topology_note']}")
                st.code(row["show_output"], language="text")
                st.markdown(f"**Expected Fault:** {row['expected_fault']}")


# ── PAGE: AI Diagnoses ───────────────────────────────────────────────────────
elif page == "🤖 AI Diagnoses":
    st.markdown("## 🤖 AI Diagnosis Results")
    st.markdown("Structured JSON diagnoses returned by the Groq LLM for each case.")
    st.markdown("---")

    ai = load_ai_responses()
    if ai.empty:
        st.warning("No AI responses found. Run `python scripts/ai_diagnose.py` first.")
    else:
        success_count = int(ai["parse_ok"].sum()) if "parse_ok" in ai.columns else 0
        fail_count = len(ai) - success_count
        st.markdown(f"**✅ {success_count} successful** | **❌ {fail_count} failed** out of {len(ai)} cases")
        st.markdown("---")

        for _, row in ai.iterrows():
            parsed = str(row.get("parse_ok", "")).lower() == "true"
            status_badge = "ok" if parsed else "fail"
            status_text = "✅ Parsed" if parsed else "❌ Failed"

            with st.expander(f"**{row['case_id']}** — {status_text} | {str(row.get('root_cause', ''))[:70]}..."):
                if parsed:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        conf = str(row.get("confidence", ""))
                        conf_class = conf.lower() if conf.lower() in ["high", "medium", "low"] else "medium"
                        st.markdown(f"**Confidence:** <span class='badge badge-{conf_class}'>{conf}</span>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**OSI Layer:** {row.get('osi_layer', 'N/A')}")
                    with col3:
                        st.markdown(f"**Next Command:** `{row.get('next_command', 'N/A')}`")

                    st.markdown(f"**Root Cause:** {row.get('root_cause', '')}")
                    st.markdown(f"**Evidence:** {row.get('evidence', '')}")

                    try:
                        steps = json.loads(str(row.get("fix_steps", "[]")))
                        if steps:
                            st.markdown("**Fix Steps:**")
                            for i, step in enumerate(steps, 1):
                                st.markdown(f"  {i}. {step}")
                    except (json.JSONDecodeError, TypeError):
                        st.markdown(f"**Fix Steps:** {row.get('fix_steps', '')}")
                else:
                    st.error(f"Raw response: {row.get('raw_response', 'N/A')}")


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
                result = diagnose_live(symptom, show_output, api_key)

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

                # Show raw JSON
                with st.expander("📄 Raw JSON Response"):
                    st.json(result)


# ── PAGE: Human Review ───────────────────────────────────────────────────────
elif page == "✅ Human Review":
    st.markdown("## ✅ Human Review Log")
    st.markdown("Review of AI diagnoses — Accepted, Edited, or Rejected by the human reviewer.")
    st.markdown("---")

    review = load_review()
    if review.empty:
        st.warning("No review log found. Run `python scripts/generate_ai_and_review.py` first.")
    else:
        # Summary
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

        # Filter by verdict
        verdict_filter = st.multiselect(
            "Filter by Verdict",
            ["Accepted", "Edited", "Rejected"],
            default=["Accepted", "Edited", "Rejected"],
        )
        filtered = review[review["human_verdict"].isin(verdict_filter)]

        for _, row in filtered.iterrows():
            verdict = row["human_verdict"]
            icon = {"Accepted": "✅", "Edited": "✏️", "Rejected": "❌"}.get(verdict, "❓")

            with st.expander(f"{icon} **{row['case_id']}** — {verdict} | {str(row.get('ai_root_cause', ''))[:60]}..."):
                st.markdown(f"**AI Root Cause:** {row.get('ai_root_cause', 'N/A')}")
                st.markdown(f"**AI Confidence:** {row.get('ai_confidence', 'N/A')}")
                st.markdown(f"**Human Verdict:** **{verdict}**")

                if pd.notna(row.get("corrected_root_cause")) and str(row.get("corrected_root_cause")).strip():
                    st.markdown(f"**Corrected Root Cause:** {row['corrected_root_cause']}")

                if pd.notna(row.get("reviewer_notes")) and str(row.get("reviewer_notes")).strip():
                    st.info(f"**Reviewer Notes:** {row['reviewer_notes']}")
