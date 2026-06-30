import os
import json
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

API_BASE = os.environ.get("VERIFYIT_DS_API", "http://localhost:8001/api")

st.set_page_config(
    page_title="VerifyIt DS — AI Fact Checker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
.verdict-fake     { background:#fee2e2; color:#991b1b; padding:6px 16px; border-radius:20px; font-weight:700; display:inline-block; }
.verdict-unverified { background:#fef9c3; color:#92400e; padding:6px 16px; border-radius:20px; font-weight:700; display:inline-block; }
.verdict-verified { background:#dcfce7; color:#166534; padding:6px 16px; border-radius:20px; font-weight:700; display:inline-block; }
.cache-banner { background:#ede9fe; color:#5b21b6; padding:8px 16px; border-radius:8px; margin-bottom:12px; }
.entity-PERSON { background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:12px; margin:2px; display:inline-block; font-size:0.8em; }
.entity-ORG    { background:#fed7aa; color:#c2410c; padding:2px 8px; border-radius:12px; margin:2px; display:inline-block; font-size:0.8em; }
.entity-GPE    { background:#d1fae5; color:#065f46; padding:2px 8px; border-radius:12px; margin:2px; display:inline-block; font-size:0.8em; }
.entity-DATE   { background:#f1f5f9; color:#475569; padding:2px 8px; border-radius:12px; margin:2px; display:inline-block; font-size:0.8em; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ─────────────────────────────────────────────────────────────────
def verdict_badge(verdict: str) -> str:
    cls = "verdict-fake" if "Fake" in verdict else ("verdict-verified" if verdict == "Verified" else "verdict-unverified")
    return f'<span class="{cls}">{verdict}</span>'

def score_color(score: int) -> str:
    if score <= 35:  return "#ef4444"
    if score <= 65:  return "#f59e0b"
    return "#22c55e"

def score_gauge(score: int, verdict: str) -> go.Figure:
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": verdict, "font": {"size": 18}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 35],  "color": "#fee2e2"},
                {"range": [35, 65], "color": "#fef3c7"},
                {"range": [65, 100],"color": "#dcfce7"},
            ],
            "threshold": {"line": {"color": color, "width": 4}, "thickness": 0.75, "value": score},
        },
    ))
    fig.update_layout(height=260, margin=dict(t=40, b=0, l=20, r=20))
    return fig

def render_entities(entity_labels: list[str]):
    if not entity_labels:
        st.caption("No named entities detected.")
        return
    parts = []
    for e in entity_labels:
        if "(" in e:
            txt, lbl = e.rsplit("(", 1)
            lbl = lbl.rstrip(")")
            css = f"entity-{lbl}" if lbl in ("PERSON","ORG","GPE","DATE") else "entity-DATE"
            parts.append(f'<span class="{css}">{txt.strip()} <b>{lbl}</b></span>')
        else:
            parts.append(f'<span class="entity-DATE">{e}</span>')
    st.markdown(" ".join(parts), unsafe_allow_html=True)

# ── Pages ────────────────────────────────────────────────────────────────────
page = st.sidebar.radio("Navigate", ["🔍 Checker", "📊 Analytics"], label_visibility="collapsed")

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Checker
# ════════════════════════════════════════════════════════════════════════════
if page == "🔍 Checker":
    st.title("🔍 VerifyIt DS — AI Fact Checker")
    st.caption("Powered by Gemini 2.5 Flash + Google Search grounding · spaCy NER · FAISS semantic cache")

    tab_text, tab_url = st.tabs(["📝 Paste Text", "🔗 Enter URL"])

    payload = {}
    with tab_text:
        claim = st.text_area("Paste the suspicious claim or WhatsApp forward here:", height=160, placeholder="E.g. Virat Kohli crying while lifting the World Cup trophy — viral video…")
        if st.button("Check Now ▶", key="check_text", type="primary", use_container_width=True):
            if claim.strip():
                payload = {"text": claim.strip()}
            else:
                st.warning("Please paste some text first.")

    with tab_url:
        url_input = st.text_input("Paste a news article or social media URL:", placeholder="https://example.com/suspicious-article")
        if st.button("Check Now ▶", key="check_url", type="primary", use_container_width=True):
            if url_input.strip().startswith("http"):
                payload = {"url": url_input.strip()}
            else:
                st.warning("Please enter a valid URL starting with https://")

    if payload:
        with st.spinner("🧠 Analysing evidence with Gemini + live Google Search…"):
            try:
                resp = requests.post(f"{API_BASE}/verify", json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Gemini is busy — please try again in a moment.")
                data = None
            except Exception as e:
                st.error(f"❌ Analysis failed: {e}")
                data = None

        if data:
            if data.get("cache_hit"):
                st.markdown(f'<div class="cache-banner">⚡ Instant result from semantic cache (similarity: {data.get("ml_confidence", 0):.1f}%)</div>', unsafe_allow_html=True)

            col_gauge, col_detail = st.columns([1, 2])

            with col_gauge:
                st.plotly_chart(score_gauge(data["score"], data["verdict"]), use_container_width=True)
                st.markdown(verdict_badge(data["verdict"]), unsafe_allow_html=True)

            with col_detail:
                st.markdown(f"### Executive Summary\n*{data['summary']}*")
                st.divider()
                st.markdown("**Key Findings:**")
                for i, reason in enumerate(data["reasons"], 1):
                    icon = "🔴" if "Fake" in data["verdict"] else ("✅" if data["verdict"] == "Verified" else "🟡")
                    st.markdown(f"{icon} **{i}.** {reason}")

                if data.get("official_source") and data["official_source"] not in ("N/A", ""):
                    src = data["official_source"].split(",")[0].strip()
                    if not src.startswith("http"):
                        src = f"https://www.google.com/search?q=fact+check+{requests.utils.quote(src)}"
                    st.markdown(f"🔗 **Source:** [{src}]({src})")

            if data.get("entities"):
                with st.expander("🏷️ Named Entities Detected", expanded=False):
                    render_entities(data["entities"])

            # Store in session
            if "history" not in st.session_state:
                st.session_state.history = []
            st.session_state.history.insert(0, data)
            st.session_state.history = st.session_state.history[:10]

    # Session history
    if st.session_state.get("history"):
        with st.expander(f"🕒 Session History ({len(st.session_state.history)} checks)", expanded=False):
            for h in st.session_state.history:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{h['input_text'][:80]}{'…' if len(h['input_text']) > 80 else ''}**")
                with col2:
                    st.markdown(verdict_badge(h["verdict"]), unsafe_allow_html=True)
                with col3:
                    st.metric("Score", h["score"])
                st.divider()

# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Analytics Dashboard
# ════════════════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.title("📊 Analytics Dashboard")

    try:
        stats_resp = requests.get(f"{API_BASE}/checks/stats", timeout=10)
        checks_resp = requests.get(f"{API_BASE}/checks?limit=200", timeout=10)
        stats = stats_resp.json()
        checks = checks_resp.json()
    except Exception as e:
        st.error(f"Could not load data: {e}")
        st.stop()

    # Metrics row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Checks", stats["total"])
    c2.metric("🔴 Likely Fake", stats["likely_fake"])
    c3.metric("🟡 Unverified", stats["unverified"])
    c4.metric("🟢 Verified", stats["verified"])
    c5.metric("Avg Score", f"{stats['avg_score']:.1f}")

    st.divider()

    if not checks:
        st.info("No checks yet — run some verifications first.")
        st.stop()

    df = pd.DataFrame(checks)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date

    col_pie, col_hist = st.columns(2)

    with col_pie:
        st.subheader("Verdict Breakdown")
        verdict_counts = df["verdict"].value_counts().reset_index()
        verdict_counts.columns = ["verdict", "count"]
        color_map = {"Likely Fake": "#ef4444", "Unverified": "#f59e0b", "Verified": "#22c55e"}
        fig_pie = px.pie(verdict_counts, names="verdict", values="count",
                         color="verdict", color_discrete_map=color_map, hole=0.4)
        fig_pie.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_hist:
        st.subheader("Score Distribution")
        fig_hist = px.histogram(df, x="score", nbins=20, color="verdict",
                                color_discrete_map=color_map,
                                labels={"score": "Credibility Score", "count": "# Checks"})
        fig_hist.update_layout(margin=dict(t=10, b=10), showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("Score Over Time")
    daily = df.groupby("date")["score"].mean().reset_index()
    daily.columns = ["date", "avg_score"]
    fig_line = px.line(daily, x="date", y="avg_score", markers=True,
                       labels={"avg_score": "Average Score", "date": "Date"},
                       color_discrete_sequence=["#6366f1"])
    fig_line.add_hline(y=65, line_dash="dash", line_color="#22c55e", annotation_text="Verified threshold")
    fig_line.add_hline(y=35, line_dash="dash", line_color="#ef4444", annotation_text="Fake threshold")
    fig_line.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_line, use_container_width=True)

    # Top entities table
    st.subheader("Top Named Entities")
    all_entities = []
    for row in checks:
        for e in (row.get("entities") or []):
            if "(" in e:
                txt, lbl = e.rsplit("(", 1)
                all_entities.append({"entity": txt.strip(), "type": lbl.rstrip(")")})
    if all_entities:
        ent_df = pd.DataFrame(all_entities)
        top_ents = ent_df.groupby(["entity", "type"]).size().reset_index(name="count")
        top_ents = top_ents.sort_values("count", ascending=False).head(20)
        st.dataframe(top_ents, use_container_width=True, hide_index=True)
    else:
        st.info("No entity data yet (spaCy NER runs once model is loaded).")
