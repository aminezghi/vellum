"""
vellum_theme.py — Wispr Flow Design System (Light Lumen & Dark Vast Modes).

Implements:
  - Exact Wispr Flow (wisprflow.ai) typography, tokens, and aesthetic:
      * Light "Lumen" Canvas (#FFFFEB) with warm ivory cream surfaces
      * Dark "Vast" Midnight Canvas (#111111 / #1A1A1A) with soft luminous text
      * Wispr Flare (#FF6C4C) terracotta coral active highlight across all tabs & pills
      * Wispr Fathom (#034F46) deep forest teal for academic authority
  - Unmistakable Active Tab Highlighting: Solid Wispr Flare (#FF6C4C) pill with crisp white text
  - Matching Top Tool Pill Capsules: ⚙️ Vault, ☀️/🌙 Theme, ℹ️ About, 🔄 Reset
  - Ultra-high contrast typography & labels ensuring 100% readability across both modes
  - Seamless, zero-network font rendering for zero-latency instant theme switching
"""

from __future__ import annotations

import threading
import streamlit as st
import vellum_workspace as VW


def is_dark_mode() -> bool:
    """Return True if Dark mode is active, False for Light (Day) mode."""
    if "_vellum_theme_mode" not in st.session_state:
        pref = VW.get_user_profile().get("theme", "light")
        st.session_state["_vellum_theme_mode"] = pref if pref in ("dark", "light") else "light"
    return st.session_state["_vellum_theme_mode"] == "dark"


def get_theme_mode() -> str:
    return "dark" if is_dark_mode() else "light"


def set_theme_mode(mode: str) -> None:
    st.session_state["_vellum_theme_mode"] = "dark" if mode == "dark" else "light"

    # Save to user profile in background thread for zero-latency switching
    def _save_bg() -> None:
        try:
            prof = VW.get_user_profile()
            VW.set_user_profile(
                name=prof.get("name", ""),
                field=prof.get("field", ""),
                keywords=prof.get("keywords", ""),
                theme=mode,
            )
        except Exception:
            pass

    threading.Thread(target=_save_bg, daemon=True).start()


def toggle_theme_mode() -> None:
    new_mode = "light" if is_dark_mode() else "dark"
    set_theme_mode(new_mode)


# Pre-compiled static CSS definitions (system fonts, zero network latency)
_DARK_CSS = """
<style>
:root {
    --wispr-lumen: #ffffeb;
    --wispr-lumen-dark: #e4e4d0;
    --wispr-vast: #1a1a1a;
    --wispr-flare: #ff6c4c;
    --wispr-glow: #ffa946;
    --wispr-dawn: #f0d7ff;
    --wispr-fathom: #034f46;
    --wispr-pulse: #7f1c34;
    --wispr-signal: #ffbcf2;
    
    --bg-main: #111111;
    --text-main: #ffffeb;
    --text-muted: #a0a096;
    --panel-bg: rgba(26, 26, 26, 0.88);
    --panel-border: rgba(255, 255, 235, 0.12);
    --metric-bg: rgba(30, 30, 30, 0.85);
    --metric-num: #ffffeb;
    --metric-label: #a0a096;
    --pill-bg: rgba(255, 255, 235, 0.08);
    --pill-border: rgba(255, 255, 235, 0.12);
    --pill-text: #a0a096;
    --pill-active-bg: #ff6c4c;
    --pill-active-border: #ff6c4c;
    --pill-active-text: #ffffff;
    --card-bg: #1c1c1c;
    --card-border: rgba(255, 255, 235, 0.12);
    --apple-blue: #ff6c4c;
    --apple-blue-hover: #ff856b;
    --apple-emerald: #34d399;
    --apple-amber: #ffa946;
    --apple-rose: #ff6c4c;
    --apple-purple: #f0d7ff;
}

/* Global Wispr Vast Canvas */
.stApp {
    background: radial-gradient(ellipse at 50% 0%, #1a1a1a 0%, #121212 65%, #0a0a0a 100%) !important;
    color: #ffffeb !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    letter-spacing: -0.01em !important;
}

/* Base Headings & Typography */
h1, h2, h3, h4, h5, h6 {
    color: #ffffeb !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    letter-spacing: -0.02em !important;
}
.display-title {
    font-family: Georgia, Garamond, "Times New Roman", serif !important;
}
p, span, div {
    color: inherit;
}

/* Full-width responsive layout */
.block-container {
    padding-top: 0.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: 100% !important;
    width: 100% !important;
}

/* High-Contrast Wispr Form Labels Across Whole App */
label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
label p,
label span {
    color: #ffffeb !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: -0.01em !important;
}

/* Inputs, Textareas, and Number Inputs (Dark Mode) */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextArea"] div[data-baseweb="textarea"],
div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[data-testid="stChatInput"] div[data-baseweb="textarea"],
div[data-testid="stDateInput"] div[data-baseweb="input"],
div[data-testid="stTimeInput"] div[data-baseweb="input"] {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255, 255, 235, 0.18) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.4) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:hover,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:hover {
    border-color: rgba(255, 255, 235, 0.35) !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:focus-within {
    border-color: #ffa946 !important;
    box-shadow: 0 0 0 3px rgba(255, 169, 70, 0.25) !important;
}

div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stTextArea"] div[data-baseweb="base-input"],
div[data-testid="stNumberInput"] div[data-baseweb="base-input"],
div[data-testid="stChatInput"] div[data-baseweb="base-input"],
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input,
div[data-testid="stChatInput"] textarea,
.stTextInput input,
.stTextArea textarea {
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    color: #ffffeb !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    caret-color: #ffa946 !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stChatInput"] textarea:focus,
.stTextInput input:focus,
.stTextArea textarea:focus {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stNumberInput"] input::placeholder,
div[data-testid="stChatInput"] textarea::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #88887e !important;
    opacity: 1 !important;
}

div[data-testid="stTextInput"] input:disabled,
div[data-testid="stTextArea"] textarea:disabled,
div[data-testid="stNumberInput"] input:disabled {
    color: #777770 !important;
    cursor: not-allowed !important;
}

div[data-testid="stTextInput"] svg,
div[data-testid="stTextArea"] svg,
div[data-testid="stChatInput"] svg {
    fill: #a0a096 !important;
    color: #a0a096 !important;
}

div[data-testid="stNumberInput"] button,
button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"] {
    background-color: rgba(255, 255, 235, 0.08) !important;
    color: #ffffeb !important;
    border: none !important;
    border-left: 1px solid rgba(255, 255, 235, 0.15) !important;
    border-radius: 0 !important;
    transition: background-color 0.15s ease, color 0.15s ease !important;
}

div[data-testid="stNumberInput"] button:hover,
button[data-testid="stNumberInputStepDown"]:hover,
button[data-testid="stNumberInputStepUp"]:hover {
    background-color: rgba(255, 255, 235, 0.18) !important;
    color: #ffa946 !important;
}

div[data-testid="stNumberInput"] button svg,
button[data-testid="stNumberInputStepDown"] svg,
button[data-testid="stNumberInputStepUp"] svg {
    fill: #ffffeb !important;
    color: #ffffeb !important;
}

/* File Uploader Across Whole App (Dark Mode) */
div[data-testid="stFileUploader"],
section[data-testid="stFileUploaderDropzone"] {
    background-color: rgba(255, 255, 235, 0.04) !important;
    border: 1.5px dashed rgba(255, 255, 235, 0.22) !important;
    border-radius: 14px !important;
    color: #ffffeb !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stFileUploaderDropzone"]:hover {
    background-color: rgba(255, 255, 235, 0.08) !important;
    border-color: #ffa946 !important;
}

section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] {
    color: #ffffeb !important;
}

section[data-testid="stFileUploaderDropzone"] button,
section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
    background-color: rgba(255, 255, 235, 0.12) !important;
    color: #ffffeb !important;
    border: 1px solid rgba(255, 255, 235, 0.25) !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3) !important;
}

section[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: rgba(255, 255, 235, 0.22) !important;
    color: #ffa946 !important;
    border-color: #ffa946 !important;
}

section[data-testid="stFileUploaderDropzone"] button * {
    color: #ffffeb !important;
}

section[data-testid="stFileUploaderDropzone"] small,
section[data-testid="stFileUploaderDropzone"] span {
    color: #a0a096 !important;
}

/* MultiSelect Across Whole App (Dark Mode) */
div[data-testid="stMultiSelect"],
div[data-testid="stMultiSelect"] div[data-baseweb="select"],
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    background-color: #1a1a1a !important;
    border-color: rgba(255, 255, 235, 0.18) !important;
    border-radius: 12px !important;
    color: #ffffeb !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background-color: rgba(255, 255, 235, 0.12) !important;
    color: #ffffeb !important;
    border: 1px solid rgba(255, 255, 235, 0.2) !important;
    border-radius: 9999px !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] * {
    color: #ffffeb !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
    fill: #ffffeb !important;
}

/* Slider (Dark Mode) */
div[data-testid="stSlider"] div[data-baseweb="slider"] {
    color: #ffffeb !important;
}
div[data-testid="stSlider"] div[role="slider"] {
    background-color: #ff6c4c !important;
    border-color: #ff6c4c !important;
}

/* Top Nav & All Selectboxes (📁 Default_Project) */
div[data-testid="stSelectbox"],
div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
div[data-testid="stSelectbox"] div[data-baseweb="select"] p {
    background-color: #1a1a1a !important;
    color: #ffffeb !important;
    border-color: rgba(255, 255, 235, 0.18) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1px solid rgba(255, 255, 235, 0.18) !important;
    border-radius: 9999px !important;
    padding-left: 8px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
}
div[data-testid="stSelectbox"] svg {
    fill: #ffffeb !important;
    color: #ffffeb !important;
}

/* Selectbox Dropdown Menu Options */
ul[data-baseweb="menu"] {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255, 255, 235, 0.18) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6) !important;
}
ul[data-baseweb="menu"] li {
    color: #ffffeb !important;
}
ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] {
    background-color: rgba(255, 255, 235, 0.12) !important;
}

/* Segmented Navigation Bar & Subview Pills (Discover, Library, Evidence, etc.) */
div[class*="st-key-_main_nav_segments"],
div[class*="st-key-_main_nav_segments"] > div,
div[class*="st-key-_main_nav_segments"] [data-testid="stButtonGroup"],
div[data-testid="stButtonGroup"],
div[data-testid="stSegmentedControl"],
div[data-testid="stPills"],
div[data-testid="stPills"] > div {
    background: rgba(255, 255, 235, 0.08) !important;
    background-color: rgba(255, 255, 235, 0.08) !important;
    border: 1px solid rgba(255, 255, 235, 0.14) !important;
    border-radius: 9999px !important;
    padding: 3px !important;
    gap: 4px !important;
}
div[class*="st-key-_main_nav_segments"] button,
div[data-testid="stButtonGroup"] button,
div[data-testid="stSegmentedControl"] button,
div[data-testid="stPills"] button {
    background: transparent !important;
    background-color: transparent !important;
    color: #a0a096 !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 6px 14px !important;
    font-weight: 550 !important;
    font-size: 0.85rem !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}
div[class*="st-key-_main_nav_segments"] button *,
div[data-testid="stButtonGroup"] button *,
div[data-testid="stSegmentedControl"] button *,
div[data-testid="stPills"] button * {
    color: #a0a096 !important;
    font-weight: 550 !important;
}
div[class*="st-key-_main_nav_segments"] button:hover,
div[data-testid="stButtonGroup"] button:hover,
div[data-testid="stPills"] button:hover {
    background: rgba(255, 255, 235, 0.14) !important;
    background-color: rgba(255, 255, 235, 0.14) !important;
}

/* UNMISTAKABLE ACTIVE HIGHLIGHT: Wispr Flare Coral Solid Pill */
div[class*="st-key-_main_nav_segments"] button[data-selected],
div[class*="st-key-_main_nav_segments"] button[data-selected="true"],
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"],
div[data-testid="stButtonGroup"] button[data-selected],
div[data-testid="stButtonGroup"] button[data-selected="true"],
div[data-testid="stButtonGroup"] button[aria-selected="true"],
div[data-testid="stSegmentedControl"] button[data-selected],
div[data-testid="stSegmentedControl"] button[data-selected="true"],
div[data-testid="stSegmentedControl"] button[aria-selected="true"],
div[data-testid="stPills"] button[data-selected],
div[data-testid="stPills"] button[data-selected="true"],
div[data-testid="stPills"] button[aria-selected="true"] {
    background: #ff6c4c !important;
    background-color: #ff6c4c !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 9999px !important;
    box-shadow: 0 3px 12px rgba(255, 108, 76, 0.45) !important;
    font-weight: 700 !important;
}
div[class*="st-key-_main_nav_segments"] button[data-selected] *,
div[class*="st-key-_main_nav_segments"] button[data-selected="true"] *,
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"] *,
div[data-testid="stButtonGroup"] button[data-selected] *,
div[data-testid="stButtonGroup"] button[data-selected="true"] *,
div[data-testid="stButtonGroup"] button[aria-selected="true"] *,
div[data-testid="stSegmentedControl"] button[data-selected] *,
div[data-testid="stSegmentedControl"] button[data-selected="true"] *,
div[data-testid="stSegmentedControl"] button[aria-selected="true"] *,
div[data-testid="stPills"] button[data-selected] *,
div[data-testid="stPills"] button[data-selected="true"] *,
div[data-testid="stPills"] button[aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Wispr Tabs Across Whole App (e.g. Notes, Library, Wizard) */
div[data-testid="stTabs"] {
    background: transparent !important;
}
div[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1.5px solid rgba(255, 255, 235, 0.12) !important;
}
div[data-testid="stTabs"] button,
div[data-testid="stTabs"] button[role="tab"],
div[data-testid="stTabs"] button p,
div[data-testid="stTabs"] button span,
div[data-testid="stTabs"] button div {
    color: #a0a096 !important;
    font-weight: 550 !important;
    font-size: 0.92rem !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button:hover,
div[data-testid="stTabs"] button:hover p {
    color: #ffffeb !important;
}
div[data-testid="stTabs"] button[aria-selected="true"],
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #ff6c4c !important;
    border-bottom: 2.5px solid #ff6c4c !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] p,
div[data-testid="stTabs"] button[aria-selected="true"] span,
div[data-testid="stTabs"] button[aria-selected="true"] div {
    color: #ff6c4c !important;
    font-weight: 700 !important;
}

/* Wispr Cards & Panels */
.glass-panel {
    background: var(--panel-bg);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border: 1px solid var(--panel-border);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    padding: 20px;
    margin-bottom: 16px;
    width: 100%;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: rgba(26, 26, 26, 0.88) !important;
    border-color: rgba(255, 255, 235, 0.12) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    border-radius: 16px !important;
}

/* Wispr Metric Tile */
.glass-metric {
    background: var(--metric-bg);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid var(--panel-border);
    border-radius: 16px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.glass-metric:hover {
    transform: translateY(-2px);
    border-color: #ff6c4c;
    box-shadow: 0 6px 24px rgba(255, 108, 76, 0.25);
}
.glass-metric-num {
    font-family: Georgia, Garamond, "Times New Roman", serif !important;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--metric-num);
    line-height: 1.1;
    margin-bottom: 4px;
}
.glass-metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--metric-label);
    font-weight: 600;
}

/* Wispr Status Badges (Dark Mode) */
.badge-emerald, .badge-green {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(52, 211, 153, 0.2);
    color: #6ee7b7;
    border: 1px solid rgba(52, 211, 153, 0.35);
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-sky, .badge-blue {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(14, 165, 233, 0.2);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-violet, .badge-purple {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(240, 215, 255, 0.18);
    color: #e0b0ff;
    border: 1px solid rgba(240, 215, 255, 0.35);
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-amber, .badge-gold {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(255, 169, 70, 0.2);
    color: #ffb866;
    border: 1px solid rgba(255, 169, 70, 0.35);
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-rose, .badge-red {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(255, 108, 76, 0.22);
    color: #ff8c70;
    border: 1px solid rgba(255, 108, 76, 0.4);
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-slate {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(255, 255, 235, 0.1);
    color: #c5c5b5;
    border: 1px solid rgba(255, 255, 235, 0.18);
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 500;
}

/* Wispr Paper Row Card */
.paper-row-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.paper-row-card:hover {
    border-color: #ff6c4c;
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(255, 108, 76, 0.2);
}

/* Tactile Buttons Across Whole App (Dark Mode) */
div.stButton > button,
div.stDownloadButton > button,
div.stLinkButton > a,
div.stButton > button[kind="secondary"],
div.stDownloadButton > button[kind="secondary"],
button[data-testid="stBaseButton-secondary"],
a[data-testid="stBaseButton-secondary"] {
    background-color: rgba(255, 255, 235, 0.08) !important;
    color: #ffffeb !important;
    border: 1px solid rgba(255, 255, 235, 0.2) !important;
    border-radius: 9999px !important;
    font-weight: 550 !important;
    font-size: 0.88rem !important;
    padding: 0.42rem 1.15rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    transition: all 120ms ease !important;
    white-space: nowrap !important;
    text-decoration: none !important;
}
div.stButton > button p,
div.stDownloadButton > button p,
div.stLinkButton > a p,
div.stButton > button span,
div.stDownloadButton > button span,
div.stLinkButton > a span,
div.stButton > button div,
div.stDownloadButton > button div {
    color: #ffffeb !important;
    font-weight: 550 !important;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover,
div.stLinkButton > a:hover,
div.stButton > button[kind="secondary"]:hover,
div.stDownloadButton > button[kind="secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
a[data-testid="stBaseButton-secondary"]:hover {
    background-color: rgba(255, 255, 235, 0.16) !important;
    border-color: rgba(255, 255, 235, 0.4) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.4) !important;
}
div.stButton > button:hover p,
div.stDownloadButton > button:hover p,
div.stLinkButton > a:hover p,
div.stButton > button:hover span,
div.stDownloadButton > button:hover span,
div.stLinkButton > a:hover span {
    color: #ffffff !important;
}
div.stButton > button:active,
div.stDownloadButton > button:active,
div.stLinkButton > a:active,
div.stButton > button[kind="secondary"]:active,
div.stDownloadButton > button[kind="secondary"]:active,
button[data-testid="stBaseButton-secondary"]:active {
    transform: scale(0.97) !important;
}
div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"],
a[data-testid="stBaseButton-primary"] {
    background-color: #ff6c4c !important;
    color: #ffffff !important;
    border: 1px solid #ff6c4c !important;
    border-radius: 9999px !important;
    font-weight: 650 !important;
    font-size: 0.88rem !important;
    padding: 0.42rem 1.25rem !important;
    box-shadow: 0 2px 10px rgba(255, 108, 76, 0.35) !important;
    text-decoration: none !important;
}
div.stButton > button[kind="primary"] p,
div.stDownloadButton > button[kind="primary"] p,
div.stLinkButton > a[kind="primary"] p,
div.stButton > button[kind="primary"] span,
div.stDownloadButton > button[kind="primary"] span,
div.stLinkButton > a[kind="primary"] span,
div.stButton > button[kind="primary"] div,
div.stDownloadButton > button[kind="primary"] div {
    color: #ffffff !important;
    font-weight: 650 !important;
}
div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button[kind="primary"]:hover,
div.stLinkButton > a[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
a[data-testid="stBaseButton-primary"]:hover {
    background-color: #ff856b !important;
    border-color: #ff856b !important;
    color: #ffffff !important;
    box-shadow: 0 4px 16px rgba(255, 108, 76, 0.5) !important;
    transform: translateY(-1px) !important;
}
div.stButton > button[kind="primary"]:hover p,
div.stDownloadButton > button[kind="primary"]:hover p,
div.stButton > button[kind="primary"]:hover span,
div.stDownloadButton > button[kind="primary"]:hover span {
    color: #ffffff !important;
}

/* Glide Data Grid / st.dataframe in Dark Mode (Adaptive Midnight Contrast) */
div[data-testid="stDataFrame"],
div[data-testid="stTable"],
div[data-testid="stDataFrameGlideDataGrid"] {
    filter: invert(0.92) hue-rotate(180deg) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 235, 0.14) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    overflow: hidden !important;
}

/* Matching Pill Capsule Tool Controls (⚙️ Vault, ☀️/🌙 Theme, ℹ️ About, 🔄 Reset) */
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button {
    width: 100% !important;
    min-width: unset !important;
    max-width: unset !important;
    height: 38px !important;
    border-radius: 9999px !important;
    padding: 4px 10px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 4px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    background: rgba(255, 255, 235, 0.08) !important;
    background-color: rgba(255, 255, 235, 0.08) !important;
    border: 1px solid rgba(255, 255, 235, 0.16) !important;
    color: #ffffeb !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    transition: all 120ms ease !important;
}
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button p,
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button span {
    color: #ffffeb !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button:hover {
    background: rgba(255, 255, 235, 0.16) !important;
    background-color: rgba(255, 255, 235, 0.16) !important;
    border-color: #ffa946 !important;
    transform: translateY(-1px) !important;
}

/* Modal Dialogs */
div[role="dialog"] {
    background-color: #1a1a1a !important;
    color: #ffffeb !important;
    border: 1px solid rgba(255, 255, 235, 0.18) !important;
    border-radius: 20px !important;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.75) !important;
}

/* Wispr Expanders & Accordions in Dark Mode */
div[data-testid="stExpander"],
details[data-testid="stExpander"] {
    background-color: rgba(26, 26, 26, 0.95) !important;
    border: 1px solid rgba(255, 255, 235, 0.14) !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3) !important;
    overflow: hidden !important;
}
div[data-testid="stExpander"] summary,
details[data-testid="stExpander"] summary {
    background: rgba(255, 255, 235, 0.05) !important;
    background-color: rgba(255, 255, 235, 0.05) !important;
    color: #ffffeb !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    font-weight: 600 !important;
    border: none !important;
}
div[data-testid="stExpander"] summary:hover,
details[data-testid="stExpander"] summary:hover {
    background-color: rgba(255, 255, 235, 0.1) !important;
    color: #ffa946 !important;
}
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary svg {
    color: #ffffeb !important;
    fill: #ffffeb !important;
}
div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background-color: transparent !important;
    border: none !important;
    padding: 16px 20px !important;
}
</style>
"""

_LIGHT_CSS = """
<style>
:root {
    --wispr-lumen: #ffffeb;
    --wispr-lumen-dark: #e4e4d0;
    --wispr-vast: #1a1a1a;
    --wispr-flare: #ff6c4c;
    --wispr-glow: #ffa946;
    --wispr-dawn: #f0d7ff;
    --wispr-fathom: #034f46;
    --wispr-pulse: #7f1c34;
    --wispr-signal: #ffbcf2;

    --bg-main: #ffffeb;
    --text-main: #1a1a1a;
    --text-muted: #5f5f5f;
    --panel-bg: #ffffff;
    --panel-border: #e4e4d0;
    --metric-bg: #ffffff;
    --metric-num: #1a1a1a;
    --metric-label: #666666;
    --pill-bg: #eaead6;
    --pill-border: #d8d8bf;
    --pill-text: #1a1a1a;
    --pill-active-bg: #ff6c4c;
    --pill-active-border: #ff6c4c;
    --pill-active-text: #ffffff;
    --card-bg: #ffffff;
    --card-border: #e4e4d0;
    --apple-blue: #ff6c4c;
    --apple-blue-hover: #ff5530;
    --apple-emerald: #034f46;
    --apple-amber: #ffa946;
    --apple-rose: #7f1c34;
    --apple-purple: #8944ab;
}

/* Global Wispr Lumen Canvas (Warm Rich Ivory) */
.stApp {
    background: #ffffeb !important;
    background-color: #ffffeb !important;
    color: #1a1a1a !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    letter-spacing: -0.01em !important;
}

/* Base Headings & Typography */
h1, h2, h3, h4, h5, h6 {
    color: #1a1a1a !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    letter-spacing: -0.02em !important;
}
.display-title {
    font-family: Georgia, Garamond, "Times New Roman", serif !important;
}
p, span, div {
    color: inherit;
}

/* Full-width responsive layout */
.block-container {
    padding-top: 0.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: 100% !important;
    width: 100% !important;
}

/* High-Contrast Form Labels Across Whole App */
label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
label p,
label span {
    color: #1a1a1a !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: -0.01em !important;
}

/* Inputs, Textareas, and Number Inputs (Light Mode) */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextArea"] div[data-baseweb="textarea"],
div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[data-testid="stChatInput"] div[data-baseweb="textarea"],
div[data-testid="stDateInput"] div[data-baseweb="input"],
div[data-testid="stTimeInput"] div[data-baseweb="input"] {
    background-color: #ffffff !important;
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 2px rgba(26, 26, 26, 0.04) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:hover,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:hover {
    border-color: #cfcfb8 !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:focus-within {
    border-color: #ff6c4c !important;
    box-shadow: 0 0 0 3px rgba(255, 108, 76, 0.2) !important;
}

div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stTextArea"] div[data-baseweb="base-input"],
div[data-testid="stNumberInput"] div[data-baseweb="base-input"],
div[data-testid="stChatInput"] div[data-baseweb="base-input"],
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input,
div[data-testid="stChatInput"] textarea,
.stTextInput input,
.stTextArea textarea {
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    color: #1a1a1a !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    caret-color: #ff6c4c !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stChatInput"] textarea:focus,
.stTextInput input:focus,
.stTextArea textarea:focus {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stNumberInput"] input::placeholder,
div[data-testid="stChatInput"] textarea::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #8a8a80 !important;
    opacity: 1 !important;
}

div[data-testid="stTextInput"] input:disabled,
div[data-testid="stTextArea"] textarea:disabled,
div[data-testid="stNumberInput"] input:disabled {
    color: #9c9c8e !important;
    cursor: not-allowed !important;
}

div[data-testid="stTextInput"] svg,
div[data-testid="stTextArea"] svg,
div[data-testid="stChatInput"] svg {
    fill: #5f5f5f !important;
    color: #5f5f5f !important;
}

div[data-testid="stNumberInput"] button,
button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"] {
    background-color: #faf8f2 !important;
    color: #1a1a1a !important;
    border: none !important;
    border-left: 1.5px solid #e4e4d0 !important;
    border-radius: 0 !important;
    transition: background-color 0.15s ease, color 0.15s ease !important;
}

div[data-testid="stNumberInput"] button:hover,
button[data-testid="stNumberInputStepDown"]:hover,
button[data-testid="stNumberInputStepUp"]:hover {
    background-color: #f0ede0 !important;
    color: #ff6c4c !important;
}

div[data-testid="stNumberInput"] button svg,
button[data-testid="stNumberInputStepDown"] svg,
button[data-testid="stNumberInputStepUp"] svg {
    fill: #1a1a1a !important;
    color: #1a1a1a !important;
}

/* File Uploader Across Whole App (Light Mode) */
div[data-testid="stFileUploader"],
section[data-testid="stFileUploaderDropzone"] {
    background-color: #ffffff !important;
    border: 1.5px dashed #cfcfb8 !important;
    border-radius: 14px !important;
    color: #1a1a1a !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stFileUploaderDropzone"]:hover {
    background-color: #faf8ed !important;
    border-color: #ff6c4c !important;
}

section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] {
    color: #1a1a1a !important;
}

section[data-testid="stFileUploaderDropzone"] button,
section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
    background-color: #f7f6ed !important;
    color: #1a1a1a !important;
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(26, 26, 26, 0.05) !important;
}

section[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: #eaead6 !important;
    color: #ff6c4c !important;
    border-color: #ff6c4c !important;
}

section[data-testid="stFileUploaderDropzone"] button * {
    color: #1a1a1a !important;
}

section[data-testid="stFileUploaderDropzone"] small,
section[data-testid="stFileUploaderDropzone"] span {
    color: #5f5f5f !important;
}

/* MultiSelect Across Whole App (Light Mode) */
div[data-testid="stMultiSelect"],
div[data-testid="stMultiSelect"] div[data-baseweb="select"],
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-color: #e4e4d0 !important;
    border-radius: 12px !important;
    color: #1a1a1a !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background-color: #f0ede0 !important;
    color: #1a1a1a !important;
    border: 1px solid #dcdcc8 !important;
    border-radius: 9999px !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] * {
    color: #1a1a1a !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
    fill: #1a1a1a !important;
}

/* Slider (Light Mode) */
div[data-testid="stSlider"] div[data-baseweb="slider"] {
    color: #1a1a1a !important;
}
div[data-testid="stSlider"] div[role="slider"] {
    background-color: #ff6c4c !important;
    border-color: #ff6c4c !important;
}

/* Top Nav & All Selectboxes (📁 Default_Project) */
div[data-testid="stSelectbox"],
div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
div[data-testid="stSelectbox"] div[data-baseweb="select"] p {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border-color: #e4e4d0 !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 9999px !important;
    padding-left: 8px !important;
    box-shadow: 0 1px 3px rgba(26, 26, 26, 0.05) !important;
}
div[data-testid="stSelectbox"] svg {
    fill: #1a1a1a !important;
    color: #1a1a1a !important;
}

/* Selectbox Dropdown Menu Options */
ul[data-baseweb="menu"] {
    background-color: #ffffff !important;
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 30px rgba(26, 26, 26, 0.12) !important;
}
ul[data-baseweb="menu"] li {
    color: #1a1a1a !important;
}
ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] {
    background-color: #faf8ed !important;
}

/* Segmented Navigation Bar & Subview Pills (Discover, Library, Evidence, etc.) */
div[class*="st-key-_main_nav_segments"],
div[class*="st-key-_main_nav_segments"] > div,
div[class*="st-key-_main_nav_segments"] [data-testid="stButtonGroup"],
div[data-testid="stButtonGroup"],
div[data-testid="stSegmentedControl"],
div[data-testid="stPills"],
div[data-testid="stPills"] > div {
    background: #eaead6 !important;
    background-color: #eaead6 !important;
    border: 1px solid #d8d8bf !important;
    border-radius: 9999px !important;
    padding: 3px !important;
    gap: 4px !important;
}
div[class*="st-key-_main_nav_segments"] button,
div[data-testid="stButtonGroup"] button,
div[data-testid="stSegmentedControl"] button,
div[data-testid="stPills"] button {
    background: transparent !important;
    background-color: transparent !important;
    color: #1a1a1a !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 6px 14px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}
div[class*="st-key-_main_nav_segments"] button *,
div[data-testid="stButtonGroup"] button *,
div[data-testid="stSegmentedControl"] button *,
div[data-testid="stPills"] button * {
    color: #1a1a1a !important;
    font-weight: 600 !important;
}
div[class*="st-key-_main_nav_segments"] button:hover,
div[data-testid="stButtonGroup"] button:hover,
div[data-testid="stPills"] button:hover {
    background: rgba(255, 255, 255, 0.45) !important;
    background-color: rgba(255, 255, 255, 0.45) !important;
}

/* UNMISTAKABLE ACTIVE HIGHLIGHT: Wispr Flare Coral Solid Pill */
div[class*="st-key-_main_nav_segments"] button[data-selected],
div[class*="st-key-_main_nav_segments"] button[data-selected="true"],
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"],
div[data-testid="stButtonGroup"] button[data-selected],
div[data-testid="stButtonGroup"] button[data-selected="true"],
div[data-testid="stButtonGroup"] button[aria-selected="true"],
div[data-testid="stSegmentedControl"] button[data-selected],
div[data-testid="stSegmentedControl"] button[data-selected="true"],
div[data-testid="stSegmentedControl"] button[aria-selected="true"],
div[data-testid="stPills"] button[data-selected],
div[data-testid="stPills"] button[data-selected="true"],
div[data-testid="stPills"] button[aria-selected="true"] {
    background: #ff6c4c !important;
    background-color: #ff6c4c !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 9999px !important;
    box-shadow: 0 3px 10px rgba(255, 108, 76, 0.38) !important;
    font-weight: 700 !important;
}
div[class*="st-key-_main_nav_segments"] button[data-selected] *,
div[class*="st-key-_main_nav_segments"] button[data-selected="true"] *,
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"] *,
div[data-testid="stButtonGroup"] button[data-selected] *,
div[data-testid="stButtonGroup"] button[data-selected="true"] *,
div[data-testid="stButtonGroup"] button[aria-selected="true"] *,
div[data-testid="stSegmentedControl"] button[data-selected] *,
div[data-testid="stSegmentedControl"] button[data-selected="true"] *,
div[data-testid="stSegmentedControl"] button[aria-selected="true"] *,
div[data-testid="stPills"] button[data-selected] *,
div[data-testid="stPills"] button[data-selected="true"] *,
div[data-testid="stPills"] button[aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Wispr Tabs Across Whole App (e.g. Notes, Library, Wizard) */
div[data-testid="stTabs"] {
    background: transparent !important;
}
div[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1.5px solid #e4e4d0 !important;
}
div[data-testid="stTabs"] button,
div[data-testid="stTabs"] button[role="tab"],
div[data-testid="stTabs"] button p,
div[data-testid="stTabs"] button span,
div[data-testid="stTabs"] button div {
    color: #5f5f5f !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button:hover,
div[data-testid="stTabs"] button:hover p {
    color: #1a1a1a !important;
}
div[data-testid="stTabs"] button[aria-selected="true"],
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #ff6c4c !important;
    border-bottom: 2.5px solid #ff6c4c !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] p,
div[data-testid="stTabs"] button[aria-selected="true"] span,
div[data-testid="stTabs"] button[aria-selected="true"] div {
    color: #ff6c4c !important;
    font-weight: 700 !important;
}

/* Wispr Cards & Panels */
.glass-panel {
    background: #ffffff;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1.5px solid #e4e4d0;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(26, 26, 26, 0.04), 0 1px 3px rgba(26, 26, 26, 0.03);
    padding: 20px;
    margin-bottom: 16px;
    width: 100%;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: #ffffff !important;
    border: 1.5px solid #e4e4d0 !important;
    box-shadow: 0 2px 12px rgba(26, 26, 26, 0.04) !important;
    border-radius: 16px !important;
}

/* Wispr Metric Tile */
.glass-metric {
    background: #ffffff;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1.5px solid #e4e4d0;
    border-radius: 16px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(26, 26, 26, 0.04);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.glass-metric:hover {
    transform: translateY(-2px);
    border-color: #ff6c4c;
    box-shadow: 0 6px 20px rgba(255, 108, 76, 0.15);
}
.glass-metric-num {
    font-family: Georgia, Garamond, "Times New Roman", serif !important;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #1a1a1a;
    line-height: 1.1;
    margin-bottom: 4px;
}
.glass-metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #666666;
    font-weight: 600;
}

/* Wispr Status Badges (Light Mode) */
.badge-emerald, .badge-green {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #cef5ca;
    color: #114e0b;
    border: 1px solid #a2e59a;
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-sky, .badge-blue {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #e0f2fe;
    color: #0369a1;
    border: 1px solid #bae6fd;
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-violet, .badge-purple {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #f0d7ff;
    color: #6b2a99;
    border: 1px solid #e0b0ff;
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-amber, .badge-gold {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #fff0d4;
    color: #a35c00;
    border: 1px solid #ffe0a3;
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-rose, .badge-red {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #ffe2dc;
    color: #bf3617;
    border: 1px solid #ffc4b8;
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
}
.badge-slate {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #ebebe0;
    color: #444444;
    border: 1px solid #d5d5c5;
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 500;
}

/* Wispr Paper Row Card */
.paper-row-card {
    background: #ffffff;
    border: 1.5px solid #e4e4d0;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(26, 26, 26, 0.04);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.paper-row-card:hover {
    border-color: #ff6c4c;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(255, 108, 76, 0.12);
}

/* Tactile Buttons Across Whole App (Light Mode - Crystal Clear & High Contrast) */
div.stButton > button,
div.stDownloadButton > button,
div.stLinkButton > a,
div.stButton > button[kind="secondary"],
div.stDownloadButton > button[kind="secondary"],
button[data-testid="stBaseButton-secondary"],
a[data-testid="stBaseButton-secondary"] {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.42rem 1.15rem !important;
    box-shadow: 0 1px 3px rgba(26, 26, 26, 0.06) !important;
    transition: all 120ms ease !important;
    white-space: nowrap !important;
    text-decoration: none !important;
}
div.stButton > button p,
div.stDownloadButton > button p,
div.stLinkButton > a p,
div.stButton > button span,
div.stDownloadButton > button span,
div.stLinkButton > a span,
div.stButton > button div,
div.stDownloadButton > button div {
    color: #1a1a1a !important;
    font-weight: 600 !important;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover,
div.stLinkButton > a:hover,
div.stButton > button[kind="secondary"]:hover,
div.stDownloadButton > button[kind="secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
a[data-testid="stBaseButton-secondary"]:hover {
    background-color: #faf8ed !important;
    border-color: #1a1a1a !important;
    color: #1a1a1a !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 8px rgba(26, 26, 26, 0.1) !important;
}
div.stButton > button:hover p,
div.stDownloadButton > button:hover p,
div.stLinkButton > a:hover p,
div.stButton > button:hover span,
div.stDownloadButton > button:hover span,
div.stLinkButton > a:hover span {
    color: #1a1a1a !important;
}
div.stButton > button:active,
div.stDownloadButton > button:active,
div.stLinkButton > a:active,
div.stButton > button[kind="secondary"]:active,
div.stDownloadButton > button[kind="secondary"]:active,
button[data-testid="stBaseButton-secondary"]:active {
    transform: scale(0.97) !important;
}
div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"],
a[data-testid="stBaseButton-primary"] {
    background-color: #1a1a1a !important;
    color: #ffffeb !important;
    border: 1.5px solid #1a1a1a !important;
    border-radius: 9999px !important;
    font-weight: 650 !important;
    font-size: 0.88rem !important;
    padding: 0.42rem 1.25rem !important;
    box-shadow: 0 2px 8px rgba(26, 26, 26, 0.18) !important;
    text-decoration: none !important;
}
div.stButton > button[kind="primary"] p,
div.stDownloadButton > button[kind="primary"] p,
div.stLinkButton > a[kind="primary"] p,
div.stButton > button[kind="primary"] span,
div.stDownloadButton > button[kind="primary"] span,
div.stLinkButton > a[kind="primary"] span,
div.stButton > button[kind="primary"] div,
div.stDownloadButton > button[kind="primary"] div {
    color: #ffffeb !important;
    font-weight: 650 !important;
}
div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button[kind="primary"]:hover,
div.stLinkButton > a[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
a[data-testid="stBaseButton-primary"]:hover {
    background-color: #ff6c4c !important;
    border-color: #ff6c4c !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(255, 108, 76, 0.35) !important;
    transform: translateY(-1px) !important;
}
div.stButton > button[kind="primary"]:hover p,
div.stDownloadButton > button[kind="primary"]:hover p,
div.stButton > button[kind="primary"]:hover span,
div.stDownloadButton > button[kind="primary"]:hover span {
    color: #ffffff !important;
}

/* Glide Data Grid / st.dataframe in Light Mode */
div[data-testid="stDataFrame"],
div[data-testid="stTable"],
div[data-testid="stDataFrameGlideDataGrid"] {
    background-color: #ffffff !important;
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 10px rgba(26, 26, 26, 0.04) !important;
    overflow: hidden !important;
}

/* Matching Pill Capsule Tool Controls (⚙️ Vault, ☀️/🌙 Theme, ℹ️ About, 🔄 Reset) */
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button {
    width: 100% !important;
    min-width: unset !important;
    max-width: unset !important;
    height: 38px !important;
    border-radius: 9999px !important;
    padding: 4px 10px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 4px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1.5px solid #e4e4d0 !important;
    color: #1a1a1a !important;
    box-shadow: 0 1px 3px rgba(26, 26, 26, 0.05) !important;
    transition: all 120ms ease !important;
}
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button p,
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button span {
    color: #1a1a1a !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button:hover {
    background: #faf8ed !important;
    background-color: #faf8ed !important;
    border-color: #ff6c4c !important;
    color: #ff6c4c !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button:hover p,
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button:hover span {
    color: #ff6c4c !important;
}

/* Wispr Expanders & Accordions in Light Mode */
div[data-testid="stExpander"],
details[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 10px rgba(26, 26, 26, 0.04) !important;
    overflow: hidden !important;
}
div[data-testid="stExpander"] summary,
details[data-testid="stExpander"] summary {
    background: #faf8f2 !important;
    background-color: #faf8f2 !important;
    color: #1a1a1a !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    font-weight: 600 !important;
    border: none !important;
}
div[data-testid="stExpander"] summary:hover,
details[data-testid="stExpander"] summary:hover {
    background-color: #f2efe4 !important;
    color: #ff6c4c !important;
}
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary svg {
    color: #1a1a1a !important;
    fill: #1a1a1a !important;
}
/* Modal Dialogs */
div[role="dialog"] {
    background-color: #ffffeb !important;
    color: #1a1a1a !important;
    border: 1.5px solid #e4e4d0 !important;
    border-radius: 20px !important;
    box-shadow: 0 20px 60px rgba(26, 26, 26, 0.2) !important;
}
</style>
"""

_CSS_CACHE = {
    True: _DARK_CSS,
    False: _LIGHT_CSS,
}


def get_theme_css(dark: bool) -> str:
    return _CSS_CACHE.get(dark, _LIGHT_CSS)


FROSTED_GLASS_CSS = get_theme_css(dark=False)


def inject_theme() -> None:
    """Inject the active Wispr Flow theme CSS (Midnight Vast vs Lumen Day)."""
    dark = is_dark_mode()
    st.markdown(get_theme_css(dark), unsafe_allow_html=True)


@st.dialog("About Vellum & Developer Credits")
def show_about_dialog() -> None:
    dark = is_dark_mode()
    title_color = "#ffffeb" if dark else "#1a1a1a"
    accent_color = "#ffa946" if dark else "#ff6c4c"
    muted_color = "#a0a096" if dark else "#5f5f5f"

    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 18px;">
            <div style="font-size: 2.4rem; font-weight: 800; letter-spacing: -0.03em; color: {title_color}; font-family: Georgia, serif;">Vellum</div>
            <div style="color: {accent_color}; font-size: 0.95rem; font-weight: 600; margin-top: 2px;">Academic Research Companion</div>
            <div style="margin-top: 6px;"><span class="badge-slate" style="border-radius: 9999px; padding: 3px 12px; font-weight: 500;">Version 2.0 • 2026 Edition</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="glass-panel" style="padding: 18px 20px; border-radius: 16px; margin-bottom: 16px;">
            <div style="font-size: 0.72rem; text-transform: uppercase; color: {accent_color}; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 6px;">
                DEVELOPER CREDITS
            </div>
            <div style="font-size: 1.25rem; font-weight: 700; color: {title_color}; margin-bottom: 8px;">
                Amine Zouaghi
            </div>
            <div style="font-size: 0.88rem; color: {muted_color}; line-height: 1.6;">
                🏛️ <b>Affiliation:</b> University of Parma<br>
                📧 <b>Email:</b> <a href="mailto:amine.zouaghi@unipr.it" style="color: {accent_color}; text-decoration: none; font-weight: 500;">amine.zouaghi@unipr.it</a><br>
                💼 <b>LinkedIn:</b> <a href="https://www.linkedin.com/in/zouaghi-amine/" target="_blank" style="color: {accent_color}; text-decoration: none; font-weight: 500;">linkedin.com/in/zouaghi-amine</a>
            </div>
        </div>
        <p style="font-size: 0.85rem; color: {muted_color}; line-height: 1.5; text-align: center; margin: 0 10px 10px 10px;">
            Vellum is a 100% local-first, privacy-preserving academic research companion. All paper metadata, PDFs, notes, and citation networks remain securely on your workstation.
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_top_nav(active_url: str = "overview") -> None:
    """
    Renders the Top Horizontal Glass Navigation Bar.
    Includes active project/notebook selector on the left, section tabs in center,
    quick controls (Vault, Theme, About, Reset), and live metrics pill on the right.

    ``active_url`` is the url_path of the screen being shown. Selecting a
    different section navigates to that section's landing screen, and a section
    that holds more than one screen gets a secondary row of pills.
    """
    inject_theme()

    import vellum_pages as VP

    vault = VW.get_vault_dir()
    projects = VW.list_projects()
    active_proj = VW.get_active_project_name()
    idx = projects.index(active_proj) if active_proj in projects else 0
    stats = VW.get_project_stats()
    dark = is_dark_mode()

    # Top Navigation Row with balanced spacing
    c_proj, c_nav, c_tools, c_stat = st.columns([1.4, 5.4, 2.2, 1.2], vertical_alignment="center")

    with c_proj:
        sel = st.selectbox(
            "Project / Notebook",
            projects,
            index=idx,
            label_visibility="collapsed",
            key="_top_proj_sel",
            help="Active systematic review project / notebook workspace",
            format_func=lambda x: f"📁 {x}",
        )
        if sel != active_proj:
            VW.set_active_project(sel)
            st.rerun()

    with c_nav:
        # Botanical Bento Native Segmented Control Bar
        section_labels = [s["label"] for s in VP.SECTIONS]
        active_section = VP.section_of(active_url) or section_labels[0]

        # Ensure widget key is synchronized whenever the section changes programmatically:
        last_tab = st.session_state.get("_last_synced_tab")
        if active_section != last_tab:
            st.session_state["_main_nav_segments"] = active_section
            st.session_state["_last_synced_tab"] = active_section

        sel_nav = st.segmented_control(
            "Navigation",
            section_labels,
            default=active_section,
            label_visibility="collapsed",
            key="_main_nav_segments",
        )
        if sel_nav and sel_nav != active_section:
            # Navigating for real means the URL follows, the browser's Back
            # button works, and the screen can be linked to directly.
            VP.go(VP.DEFAULT_PAGE[sel_nav])

    # ── Secondary navigation for sections that hold more than one screen ──
    section = next((s for s in VP.SECTIONS if s["label"] == active_section), None)
    if section and len(section["pages"]) > 1:
        sub_options = [f"{p[2]} {p[1]}" for p in section["pages"]]
        sub_paths = {f"{p[2]} {p[1]}": p[0] for p in section["pages"]}
        cur_sub = next(
            (f"{p[2]} {p[1]}" for p in section["pages"] if p[0] == active_url),
            sub_options[0],
        )
        sub_key = f"_subnav_{active_section}"
        if st.session_state.get(sub_key) != cur_sub:
            st.session_state[sub_key] = cur_sub
        sel_sub = st.pills(
            f"{active_section} Section",
            sub_options,
            default=cur_sub,
            label_visibility="collapsed",
            key=sub_key,
        )
        if sel_sub and sub_paths.get(sel_sub) != active_url:
            VP.go(sub_paths[sel_sub])

    with c_tools:
        # Matching Pill Capsules with Icon + Short Label
        t1, t2, t3, t4 = st.columns(4, gap="small")
        with t1:
            if st.button("⚙️ Vault", help="Manage Profile & Research Vaults", key="_tool_btn_vault", use_container_width=True):
                st.session_state["_show_welcome_hub"] = True
                st.rerun()
        with t2:
            theme_label = "☀️ Day" if dark else "🌙 Dark"
            theme_tip = "Switch to Day (Lumen) Theme" if dark else "Switch to Dark (Vast) Theme"
            if st.button(theme_label, help=theme_tip, key="_tool_btn_theme", use_container_width=True):
                toggle_theme_mode()
                st.rerun()
        with t3:
            if st.button("ℹ️ About", help="About & Developer Credits", key="_tool_btn_about", use_container_width=True):
                show_about_dialog()
        with t4:
            if st.button("🔄 Reset", help="Reset Current Session & Clear Cache", key="_tool_btn_reset", use_container_width=True):
                for k in list(st.session_state.keys()):
                    if not k.startswith("_vw_active_vault"):
                        st.session_state.pop(k, None)
                st.rerun()

    with c_stat:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; gap: 5px; white-space: nowrap;">
                <span class="badge-sky" title="Search Records">🔍 {stats.get('search_records', 0)}</span>
                <span class="badge-emerald" title="Included Papers">⭐ {stats.get('included', 0)}</span>
                <span class="badge-amber" title="Notes">📝 {stats.get('noted', 0)}</span>
                <span class="badge-violet" title="Downloaded PDFs">📥 {stats.get('pdfs', 0)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    border_color = "rgba(255, 255, 235, 0.12)" if dark else "#e4e4d0"
    st.markdown(f"<hr style='margin: 8px 0 20px 0; border: none; border-bottom: 1px solid {border_color};'>", unsafe_allow_html=True)
