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
  - Offline, local font rendering for zero-latency instant theme switching
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
    --wispr-lumen: #f5f5f7;
    --wispr-lumen-dark: #e5e5ea;
    --wispr-vast: #1e1e1e;
    --wispr-flare: #0a84ff;
    --wispr-glow: #409cff;
    --wispr-dawn: #bf5af2;
    --wispr-fathom: #30d158;
    --wispr-pulse: #ff453a;
    --wispr-signal: #5e5ce6;
    
    --bg-main: #1e1e1e;
    --text-main: #f5f5f7;
    --text-muted: #8e8e93;
    --panel-bg: rgba(36, 36, 38, 0.88);
    --panel-border: rgba(255, 255, 255, 0.12);
    --metric-bg: rgba(44, 44, 46, 0.82);
    --metric-num: #ffffff;
    --metric-label: #8e8e93;
    --pill-bg: rgba(255, 255, 255, 0.08);
    --pill-border: rgba(255, 255, 255, 0.12);
    --pill-text: #aeaeb2;
    --pill-active-bg: #0a84ff;
    --pill-active-border: #0a84ff;
    --pill-active-text: #ffffff;
    --card-bg: rgba(36, 36, 38, 0.90);
    --card-border: rgba(255, 255, 255, 0.10);
    --apple-blue: #0a84ff;
    --apple-blue-hover: #409cff;
    --apple-emerald: #30d158;
    --apple-amber: #ff9f0a;
    --apple-rose: #ff453a;
    --apple-purple: #bf5af2;
}

/* Apple macOS Sequoia Canvas (Dark Window) */
.stApp {
    background: radial-gradient(ellipse at 50% 0%, #252528 0%, #1c1c1e 100%) !important;
    color: #f5f5f7 !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro", "Segoe UI", Roboto, sans-serif !important;
    letter-spacing: -0.01em !important;
}

/* Base Headings & Typography */
h1, h2, h3, h4, h5, h6 {
    color: #f5f5f7 !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro", "Segoe UI", sans-serif !important;
    letter-spacing: -0.02em !important;
    font-weight: 700 !important;
}
.display-title {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro", sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
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
div[data-testid="stTimeInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] > div,
div[data-testid="stTextInput"] > div > div,
div[data-testid="stTextArea"] > div,
div[data-testid="stTextArea"] > div > div,
div[data-testid="stNumberInput"] > div,
div[data-testid="stNumberInput"] > div > div,
div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stTextArea"] div[data-baseweb="base-input"] {
    background-color: #242426 !important;
    background: #242426 !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.35) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    color: #f5f5f7 !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:hover,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:hover {
    border-color: rgba(255, 255, 255, 0.3) !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:focus-within,
div[data-testid="stTextInput"] > div:focus-within {
    border-color: #0a84ff !important;
    box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.35) !important;
}

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
    color: #f5f5f7 !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    caret-color: #0a84ff !important;
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
    color: #8e8e93 !important;
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
    color: #f5f5f7 !important;
}
div[data-testid="stSlider"] div[role="slider"] {
    background-color: #0a84ff !important;
    border-color: #0a84ff !important;
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

/* Apple macOS Segmented Navigation Bar (Dark Mode) */
div[class*="st-key-_main_nav_segments"],
div[class*="st-key-_main_nav_segments"] > div,
div[class*="st-key-_main_nav_segments"] [data-testid="stButtonGroup"],
div[data-testid="stSegmentedControl"],
div[data-testid="stSegmentedControl"] > div {
    background: rgba(255, 255, 255, 0.08) !important;
    background-color: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 9999px !important;
    padding: 3px !important;
    gap: 2px !important;
}

div[class*="st-key-_main_nav_segments"] button,
div[data-testid="stSegmentedControl"] button {
    background: transparent !important;
    background-color: transparent !important;
    color: #aeaeb2 !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 5px 12px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

div[class*="st-key-_main_nav_segments"] button *,
div[data-testid="stSegmentedControl"] button * {
    color: #aeaeb2 !important;
    font-weight: 500 !important;
}

div[class*="st-key-_main_nav_segments"] button:hover,
div[data-testid="stSegmentedControl"] button:hover {
    background: rgba(255, 255, 255, 0.12) !important;
    background-color: rgba(255, 255, 255, 0.12) !important;
    color: #f5f5f7 !important;
}

/* Apple HIG Active Segment (Dark Mode) */
div[class*="st-key-_main_nav_segments"] button[data-selected],
div[class*="st-key-_main_nav_segments"] button[data-selected="true"],
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"],
div[data-testid="stSegmentedControl"] button[data-selected],
div[data-testid="stSegmentedControl"] button[data-selected="true"],
div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
    background: #0a84ff !important;
    background-color: #0a84ff !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 9999px !important;
    box-shadow: 0 2px 8px rgba(10, 132, 255, 0.45) !important;
    font-weight: 600 !important;
}

div[class*="st-key-_main_nav_segments"] button[data-selected="true"] *,
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"] *,
div[data-testid="stSegmentedControl"] button[data-selected="true"] *,
div[data-testid="stSegmentedControl"] button[aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Apple HIG Subview Pills (Dark Mode) */
div[data-testid="stPills"],
div[data-testid="stPills"] > div,
div[class*="st-key-_subnav_"],
div[class*="st-key-_subnav_"] > div {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    padding: 2px 0 !important;
    gap: 6px !important;
}

div[data-testid="stPills"] button,
div[class*="st-key-_subnav_"] button {
    background: rgba(255, 255, 255, 0.08) !important;
    background-color: rgba(255, 255, 255, 0.08) !important;
    color: #f5f5f7 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 9999px !important;
    padding: 4px 14px !important;
    font-weight: 550 !important;
    font-size: 0.83rem !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.15s ease !important;
}

div[data-testid="stPills"] button *,
div[class*="st-key-_subnav_"] button * {
    color: #f5f5f7 !important;
    font-weight: 550 !important;
}

div[data-testid="stPills"] button:hover,
div[class*="st-key-_subnav_"] button:hover {
    background: rgba(255, 255, 255, 0.14) !important;
    background-color: rgba(255, 255, 255, 0.14) !important;
    border-color: #0a84ff !important;
}

div[data-testid="stPills"] button[data-selected="true"],
div[data-testid="stPills"] button[aria-selected="true"],
div[class*="st-key-_subnav_"] button[data-selected="true"],
div[class*="st-key-_subnav_"] button[aria-selected="true"] {
    background: #0a84ff !important;
    background-color: #0a84ff !important;
    color: #ffffff !important;
    border: 1px solid #0a84ff !important;
    border-radius: 9999px !important;
    box-shadow: 0 2px 8px rgba(10, 132, 255, 0.45) !important;
    font-weight: 600 !important;
}

div[data-testid="stPills"] button[data-selected="true"] *,
div[data-testid="stPills"] button[aria-selected="true"] *,
div[class*="st-key-_subnav_"] button[data-selected="true"] *,
div[class*="st-key-_subnav_"] button[aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
}
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
    color: var(--apple-blue, #0a84ff) !important;
    border-bottom: 2.5px solid var(--apple-blue, #0a84ff) !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] p,
div[data-testid="stTabs"] button[aria-selected="true"] span,
div[data-testid="stTabs"] button[aria-selected="true"] div {
    color: var(--apple-blue, #0a84ff) !important;
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
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.glass-metric:hover {
    transform: translateY(-2px);
    border-color: #0a84ff;
    box-shadow: 0 6px 24px rgba(10, 132, 255, 0.25);
}
.glass-metric-num {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro", sans-serif !important;
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
    background: rgba(255, 69, 58, 0.18);
    color: #ff453a;
    border: 1px solid rgba(255, 69, 58, 0.35);
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
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.paper-row-card:hover {
    border-color: #0a84ff;
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(10, 132, 255, 0.2);
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
    background-color: #0a84ff !important;
    color: #ffffff !important;
    border: 1px solid #0a84ff !important;
    border-radius: 9999px !important;
    font-weight: 650 !important;
    font-size: 0.88rem !important;
    padding: 0.42rem 1.25rem !important;
    box-shadow: 0 2px 10px rgba(10, 132, 255, 0.35) !important;
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
    background-color: #409cff !important;
    border-color: #409cff !important;
    color: #ffffff !important;
    box-shadow: 0 4px 16px rgba(10, 132, 255, 0.5) !important;
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
    --wispr-lumen: #ffffff;
    --wispr-lumen-dark: #f2f2f7;
    --wispr-vast: #1d1d1f;
    --wispr-flare: #007aff;
    --wispr-glow: #0062cc;
    --wispr-dawn: #af52de;
    --wispr-fathom: #34c759;
    --wispr-pulse: #ff3b30;
    --wispr-signal: #5856d6;

    --bg-main: #f5f5f7;
    --text-main: #1d1d1f;
    --text-muted: #6e6e73;
    --panel-bg: rgba(255, 255, 255, 0.88);
    --panel-border: rgba(0, 0, 0, 0.08);
    --metric-bg: rgba(255, 255, 255, 0.95);
    --metric-num: #1d1d1f;
    --metric-label: #86868b;
    --pill-bg: rgba(0, 0, 0, 0.05);
    --pill-border: rgba(0, 0, 0, 0.08);
    --pill-text: #1d1d1f;
    --pill-active-bg: #007aff;
    --pill-active-border: #007aff;
    --pill-active-text: #ffffff;
    --card-bg: #ffffff;
    --card-border: rgba(0, 0, 0, 0.08);
    --apple-blue: #007aff;
    --apple-blue-hover: #0062cc;
    --apple-emerald: #34c759;
    --apple-amber: #ff9500;
    --apple-rose: #ff3b30;
    --apple-purple: #af52de;
}

/* Apple macOS Sequoia Canvas (Light Window) */
.stApp {
    background: #f5f5f7 !important;
    background-color: #f5f5f7 !important;
    color: #1d1d1f !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro", "Segoe UI", Roboto, sans-serif !important;
    letter-spacing: -0.01em !important;
}

/* Base Headings & Typography */
h1, h2, h3, h4, h5, h6 {
    color: #1d1d1f !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro", "Segoe UI", sans-serif !important;
    letter-spacing: -0.02em !important;
    font-weight: 700 !important;
}
.display-title {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro", sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
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
    border: 1px solid rgba(0, 0, 0, 0.12) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:hover,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:hover {
    border-color: rgba(0, 0, 0, 0.25) !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:focus-within {
    border-color: #007aff !important;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2) !important;
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
    caret-color: #007aff !important;
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
    background-color: rgba(0, 0, 0, 0.02) !important;
    color: #1d1d1f !important;
    border: none !important;
    border-left: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 0 !important;
    transition: background-color 0.15s ease, color 0.15s ease !important;
}

div[data-testid="stNumberInput"] button:hover,
button[data-testid="stNumberInputStepDown"]:hover,
button[data-testid="stNumberInputStepUp"]:hover {
    background-color: rgba(0, 0, 0, 0.06) !important;
    color: #007aff !important;
}

div[data-testid="stNumberInput"] button svg,
button[data-testid="stNumberInputStepDown"] svg,
button[data-testid="stNumberInputStepUp"] svg {
    fill: #1d1d1f !important;
    color: #1d1d1f !important;
}

/* File Uploader Across Whole App (Light Mode) */
div[data-testid="stFileUploader"],
section[data-testid="stFileUploaderDropzone"] {
    background-color: #ffffff !important;
    border: 1.5px dashed rgba(0, 0, 0, 0.18) !important;
    border-radius: 12px !important;
    color: #1d1d1f !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stFileUploaderDropzone"]:hover {
    background-color: #f5f5f7 !important;
    border-color: #007aff !important;
}

section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] {
    color: #1d1d1f !important;
}

section[data-testid="stFileUploaderDropzone"] button,
section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
    background-color: #ffffff !important;
    color: #1d1d1f !important;
    border: 1px solid rgba(0, 0, 0, 0.14) !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}

section[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: #f5f5f7 !important;
    color: #007aff !important;
    border-color: #007aff !important;
}

section[data-testid="stFileUploaderDropzone"] button * {
    color: #1d1d1f !important;
}

section[data-testid="stFileUploaderDropzone"] small,
section[data-testid="stFileUploaderDropzone"] span {
    color: #6e6e73 !important;
}

/* MultiSelect Across Whole App (Light Mode) */
div[data-testid="stMultiSelect"],
div[data-testid="stMultiSelect"] div[data-baseweb="select"],
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-color: rgba(0, 0, 0, 0.12) !important;
    border-radius: 12px !important;
    color: #1d1d1f !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background-color: rgba(0, 0, 0, 0.05) !important;
    color: #1d1d1f !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 9999px !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] * {
    color: #1d1d1f !important;
}

div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
    fill: #1d1d1f !important;
}

/* Slider (Light Mode) */
div[data-testid="stSlider"] div[data-baseweb="slider"] {
    color: #1d1d1f !important;
}
div[data-testid="stSlider"] div[role="slider"] {
    background-color: #007aff !important;
    border-color: #007aff !important;
}

/* Top Nav & All Selectboxes (📁 Default_Project) */
div[data-testid="stSelectbox"],
div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
div[data-testid="stSelectbox"] div[data-baseweb="select"] p {
    background-color: #ffffff !important;
    color: #1d1d1f !important;
    border-color: rgba(0, 0, 0, 0.12) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1px solid rgba(0, 0, 0, 0.12) !important;
    border-radius: 9999px !important;
    padding-left: 8px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}
div[data-testid="stSelectbox"] svg {
    fill: #1d1d1f !important;
    color: #1d1d1f !important;
}

/* Selectbox Dropdown Menu Options */
ul[data-baseweb="menu"] {
    background-color: #ffffff !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1) !important;
}
ul[data-baseweb="menu"] li {
    color: #1d1d1f !important;
}
ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] {
    background-color: rgba(0, 0, 0, 0.04) !important;
}

/* Apple macOS Segmented Navigation Bar (Light Mode) */
div[class*="st-key-_main_nav_segments"],
div[class*="st-key-_main_nav_segments"] > div,
div[class*="st-key-_main_nav_segments"] [data-testid="stButtonGroup"],
div[data-testid="stSegmentedControl"],
div[data-testid="stSegmentedControl"] > div {
    background: rgba(118, 118, 128, 0.12) !important;
    background-color: rgba(118, 118, 128, 0.12) !important;
    border: 1px solid rgba(0, 0, 0, 0.05) !important;
    border-radius: 9999px !important;
    padding: 3px !important;
    gap: 2px !important;
}

div[class*="st-key-_main_nav_segments"] button,
div[data-testid="stSegmentedControl"] button {
    background: transparent !important;
    background-color: transparent !important;
    color: #1d1d1f !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 5px 12px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

div[class*="st-key-_main_nav_segments"] button *,
div[data-testid="stSegmentedControl"] button * {
    color: #1d1d1f !important;
    font-weight: 500 !important;
}

div[class*="st-key-_main_nav_segments"] button:hover,
div[data-testid="stSegmentedControl"] button:hover {
    background: rgba(255, 255, 255, 0.6) !important;
    background-color: rgba(255, 255, 255, 0.6) !important;
}

/* Apple HIG Active Segment (Light Mode) */
div[class*="st-key-_main_nav_segments"] button[data-selected],
div[class*="st-key-_main_nav_segments"] button[data-selected="true"],
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"],
div[data-testid="stSegmentedControl"] button[data-selected],
div[data-testid="stSegmentedControl"] button[data-selected="true"],
div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
    background: #007aff !important;
    background-color: #007aff !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 9999px !important;
    box-shadow: 0 2px 6px rgba(0, 122, 255, 0.3) !important;
    font-weight: 600 !important;
}

div[class*="st-key-_main_nav_segments"] button[data-selected="true"] *,
div[class*="st-key-_main_nav_segments"] button[aria-selected="true"] *,
div[data-testid="stSegmentedControl"] button[data-selected="true"] *,
div[data-testid="stSegmentedControl"] button[aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Apple HIG Subview Pills (Light Mode) */
div[data-testid="stPills"],
div[data-testid="stPills"] > div,
div[class*="st-key-_subnav_"],
div[class*="st-key-_subnav_"] > div {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    padding: 2px 0 !important;
    gap: 6px !important;
}

div[data-testid="stPills"] button,
div[class*="st-key-_subnav_"] button {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #1d1d1f !important;
    border: 1px solid rgba(0, 0, 0, 0.12) !important;
    border-radius: 9999px !important;
    padding: 4px 14px !important;
    font-weight: 550 !important;
    font-size: 0.83rem !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.15s ease !important;
}

div[data-testid="stPills"] button *,
div[class*="st-key-_subnav_"] button * {
    color: #1d1d1f !important;
    font-weight: 550 !important;
}

div[data-testid="stPills"] button:hover,
div[class*="st-key-_subnav_"] button:hover {
    background: #f5f5f7 !important;
    background-color: #f5f5f7 !important;
    border-color: #007aff !important;
    color: #007aff !important;
}

div[data-testid="stPills"] button[data-selected="true"],
div[data-testid="stPills"] button[aria-selected="true"],
div[class*="st-key-_subnav_"] button[data-selected="true"],
div[class*="st-key-_subnav_"] button[aria-selected="true"] {
    background: #007aff !important;
    background-color: #007aff !important;
    color: #ffffff !important;
    border: 1px solid #007aff !important;
    border-radius: 9999px !important;
    box-shadow: 0 2px 8px rgba(0, 122, 255, 0.35) !important;
    font-weight: 600 !important;
}

div[data-testid="stPills"] button[data-selected="true"] *,
div[data-testid="stPills"] button[aria-selected="true"] *,
div[class*="st-key-_subnav_"] button[data-selected="true"] *,
div[class*="st-key-_subnav_"] button[aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
}
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
    border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
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
    color: #007aff !important;
    border-bottom: 2.5px solid #007aff !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] p,
div[data-testid="stTabs"] button[aria-selected="true"] span,
div[data-testid="stTabs"] button[aria-selected="true"] div {
    color: #007aff !important;
    font-weight: 700 !important;
}

/* Wispr Cards & Panels */
.glass-panel {
    background: #ffffff;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    padding: 20px;
    margin-bottom: 16px;
    width: 100%;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: #ffffff !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
    border-radius: 12px !important;
}

/* Wispr Metric Tile */
.glass-metric {
    background: #ffffff;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.glass-metric:hover {
    transform: translateY(-2px);
    border-color: #007aff;
    box-shadow: 0 6px 20px rgba(0, 122, 255, 0.15);
}
.glass-metric-num {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro", sans-serif !important;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #1d1d1f;
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
    background: rgba(142, 142, 147, 0.12);
    color: #636366;
    border: 1px solid rgba(142, 142, 147, 0.25);
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 500;
}

/* Wispr Paper Row Card */
.paper-row-card {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}
.paper-row-card:hover {
    border-color: #007aff;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 122, 255, 0.12);
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
    color: #1d1d1f !important;
    border: 1px solid rgba(0, 0, 0, 0.14) !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.42rem 1.15rem !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
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
    background-color: #f5f5f7 !important;
    border-color: rgba(0, 0, 0, 0.3) !important;
    color: #1d1d1f !important;
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
    background-color: #0062cc !important;
    border-color: #0062cc !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(0, 122, 255, 0.35) !important;
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
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
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
    border: 1px solid rgba(0, 0, 0, 0.12) !important;
    color: #1d1d1f !important;
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
    background: #f5f5f7 !important;
    background-color: #f5f5f7 !important;
    border-color: #007aff !important;
    color: #007aff !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button:hover p,
div[data-testid="stColumn"] div[class*="st-key-_tool_btn_"] button:hover span {
    color: #007aff !important;
}

/* Apple macOS Expanders & Accordions in Light Mode */
div[data-testid="stExpander"],
details[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    overflow: hidden !important;
}
div[data-testid="stExpander"] summary,
details[data-testid="stExpander"] summary {
    background: rgba(0, 0, 0, 0.02) !important;
    background-color: rgba(0, 0, 0, 0.02) !important;
    color: #1d1d1f !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    font-weight: 600 !important;
    border: none !important;
    transition: background-color 0.15s ease, color 0.15s ease !important;
}
div[data-testid="stExpander"] summary:hover,
details[data-testid="stExpander"] summary:hover {
    background-color: rgba(0, 0, 0, 0.05) !important;
    color: #007aff !important;
}
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary svg {
    color: #1d1d1f !important;
    fill: #1d1d1f !important;
}
/* Modal Dialogs */
div[role="dialog"] {
    background-color: #ffffff !important;
    color: #1d1d1f !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 16px !important;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16) !important;
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
    title_color = "#ffffff" if dark else "#1d1d1f"
    accent_color = "#0a84ff" if dark else "#007aff"
    muted_color = "#8e8e93" if dark else "#86868b"

    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 18px;">
            <div style="font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em; color: {title_color}; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro', sans-serif;">Vellum</div>
            <div style="color: {accent_color}; font-size: 0.95rem; font-weight: 600; margin-top: 2px;">Academic Research Suite • macOS Sequoia Edition</div>
            <div style="margin-top: 6px;"><span class="badge-slate" style="border-radius: 9999px; padding: 3px 12px; font-weight: 500;">Version 2.1 • 2026 Edition</span></div>
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
    Renders the Apple HIG Top Glass Navigation Bar.
    Includes active project selector and live stats on left, quick controls on right,
    and native full-width macOS segmented navigation with subview pills.
    """
    inject_theme()

    import vellum_pages as VP

    vault = VW.get_vault_dir()
    projects = VW.list_projects()
    active_proj = VW.get_active_project_name()
    idx = projects.index(active_proj) if active_proj in projects else 0
    stats = VW.get_project_stats()
    dark = is_dark_mode()

    # ── Row 1: Workspace & Tool Controls ──
    c_left, c_right = st.columns([3.2, 1.8], vertical_alignment="center")

    with c_left:
        sub_c1, sub_c2 = st.columns([1.5, 2.2], vertical_alignment="center")
        with sub_c1:
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

        with sub_c2:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 6px; white-space: nowrap;">
                    <span class="badge-sky" title="Search Records">🔍 {stats.get('search_records', 0)}</span>
                    <span class="badge-emerald" title="Included Papers">⭐ {stats.get('included', 0)}</span>
                    <span class="badge-amber" title="Notes">📝 {stats.get('noted', 0)}</span>
                    <span class="badge-violet" title="Downloaded PDFs">📥 {stats.get('pdfs', 0)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c_right:
        t1, t2, t3, t4 = st.columns(4, gap="small")
        with t1:
            if st.button("⚙️ Vault", help="Manage Profile & Research Vaults", key="_tool_btn_vault", use_container_width=True):
                st.session_state["_show_welcome_hub"] = True
                st.rerun()
        with t2:
            theme_label = "☀️ Light" if dark else "🌙 Dark"
            theme_tip = "Switch to Apple Light Theme" if dark else "Switch to Apple Dark Theme"
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

    # ── Row 2: Primary macOS Segmented Navigation ──
    section_labels = [s["label"] for s in VP.SECTIONS]
    active_section = VP.section_of(active_url) or section_labels[0]

    sel_nav = st.segmented_control(
        "Navigation",
        section_labels,
        default=active_section,
        label_visibility="collapsed",
        key=f"_nav_seg_{active_url}",
    )
    if sel_nav and sel_nav != active_section:
        VP.go(VP.DEFAULT_PAGE[sel_nav])

    # ── Row 3: Secondary Subview Pills (Unified Paper Pool vs PDF Downloader, etc.) ──
    section = next((s for s in VP.SECTIONS if s["label"] == active_section), None)
    if section and len(section["pages"]) > 1:
        sub_options = [f"{p[2]} {p[1]}" for p in section["pages"]]
        sub_paths = {f"{p[2]} {p[1]}": p[0] for p in section["pages"]}
        cur_sub = next(
            (f"{p[2]} {p[1]}" for p in section["pages"] if p[0] == active_url),
            sub_options[0],
        )

        sel_sub = st.pills(
            f"{active_section} Section",
            sub_options,
            default=cur_sub,
            label_visibility="collapsed",
            key=f"_subnav_pills_{active_url}",
        )
        if sel_sub and sub_paths.get(sel_sub) and sub_paths.get(sel_sub) != active_url:
            VP.go(sub_paths[sel_sub])

    border_color = "rgba(255, 255, 255, 0.10)" if dark else "rgba(0, 0, 0, 0.08)"
    st.markdown(f"<hr style='margin: 8px 0 16px 0; border: none; border-bottom: 1px solid {border_color};'>", unsafe_allow_html=True)
