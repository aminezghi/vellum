"""
app_pages/welcome_hub.py — Integrated 3-Step Welcome & Vault Wizard for Vellum.

Wispr Flow design aesthetic:
  - Step 1: Researcher Profile (Name, Field of Research, Keywords)
  - Step 2: Local Storage Location (Research Vault directory & Initial Project)
  - Step 3: Setup Completion & Instant Launch to Mission Control Dashboard
"""

from __future__ import annotations

import os
from pathlib import Path
import streamlit as st

import vellum_paths as VP
import vellum_pages
import vellum_theme as VT
import vellum_workspace as VW


def render() -> None:
    # Inject active theme
    if hasattr(VT, "inject_theme"):
        VT.inject_theme()

    can_return = VW.is_vault_initialized()
    active_proj = VW.get_active_project_name() if can_return else ""

    # Top return navigation bar if a vault already exists
    if can_return:
        col_back, col_spacer, col_theme = st.columns([3.0, 6.0, 1.2], vertical_alignment="center")
        with col_back:
            btn_label = f"← Return to Workspace ({active_proj})" if active_proj else "← Return to Workspace"
            if st.button(btn_label, key="_hub_back_to_workspace_top", type="secondary"):
                st.session_state["_show_welcome_hub"] = False
                st.rerun()
        with col_theme:
            is_dark = getattr(VT, "is_dark_mode", lambda: False)()
            theme_icon = "☀️ Light" if is_dark else "🌙 Dark"
            theme_tip = "Switch to Apple Light Theme" if is_dark else "Switch to Apple Dark Theme"
            if st.button(theme_icon, key="_hub_top_theme_btn", help=theme_tip, use_container_width=True):
                if hasattr(VT, "toggle_theme_mode"):
                    VT.toggle_theme_mode()
                st.rerun()

    # Header Banner in Apple HIG & Landing Page Design Architecture
    st.markdown(
        """
        <div style="text-align: center; padding: 24px 20px 16px 20px; max-width: 840px; margin: 0 auto;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 14px; border-radius: 9999px; background: rgba(52, 199, 89, 0.12); border: 1px solid rgba(52, 199, 89, 0.35); color: #34c759; font-size: 0.78rem; font-weight: 600; margin-bottom: 14px; letter-spacing: 0.02em;">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: #34c759; display: inline-block;"></span>
                <span>Systematic Literature Intelligence • 100% Local Filesystem Vault</span>
            </div>
            <div style="font-size: 2.6rem; font-weight: 800; letter-spacing: -0.035em; line-height: 1.15; margin-bottom: 10px; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro', 'Segoe UI', sans-serif; color: var(--text-main);">
                Welcome to Vellum by Amine
            </div>
            <p style="max-width: 640px; margin: 0 auto 16px auto; color: var(--text-muted, #86868b); font-size: 0.95rem; line-height: 1.6; font-weight: 400;">
                High-throughput PDF harvesting, interactive citation graphs, and active-learning systematic screening.
                All files, notes, and evidence tables remain 100% private on your machine.
            </p>
            <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 14px;">
                <div style="display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 8px; background: var(--panel-bg); border: 1px solid var(--panel-border); font-size: 0.78rem; color: var(--text-muted); font-weight: 500;">
                    <span>🏛️</span><span>250M+ OpenAlex Corpus</span>
                </div>
                <div style="display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 8px; background: var(--panel-bg); border: 1px solid var(--panel-border); font-size: 0.78rem; color: var(--text-muted); font-weight: 500;">
                    <span>⚡</span><span>Multi-Tier Paywall Resolvers</span>
                </div>
                <div style="display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 8px; background: var(--panel-bg); border: 1px solid var(--panel-border); font-size: 0.78rem; color: var(--text-muted); font-weight: 500;">
                    <span>🔒</span><span>Zero Cloud Sync &amp; Telemetry</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profile = VW.get_user_profile()
    curr_name = profile.get("name", "")
    curr_field = profile.get("field", "")
    curr_keywords = profile.get("keywords", "")

    current_vault = VW.get_vault_dir()
    default_vault_parent = str(Path.home() / "Documents") if (Path.home() / "Documents").exists() else str(Path.home())

    tab1, tab2 = st.tabs(["🚀 Setup Wizard (New & Edit)", "📂 Open Existing Vault"])

    with tab1:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        col_w1, col_w2 = st.columns([1, 1], gap="large")

        with col_w1:
            st.markdown(
                """
                <div class="glass-panel" style="margin-bottom: 14px; padding: 18px 20px; border-radius: 16px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 1.12rem; font-weight: 700; color: var(--text-main); margin-bottom: 4px;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 6px; background: rgba(52, 199, 89, 0.15); color: #34c759; font-size: 0.82rem; font-weight: 700;">1</span>
                        <span>Researcher Profile</span>
                    </div>
                    <p style="font-size: 0.84rem; color: var(--text-muted, #86868b); margin-bottom: 0px; line-height: 1.4;">
                        Personalizes your workspace and seeds smart paper recommendations.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            u_name = st.text_input(
                "Your Name / Title",
                value=curr_name or "Amine Zouaghi",
                placeholder="e.g. Dr. Jane Doe or Alex Rivera",
                help="Used for your personalized greeting and study exports",
                key="_wiz_user_name",
            )

            u_field = st.text_input(
                "Primary Field of Research",
                value=curr_field or "Biomedical Informatics",
                placeholder="e.g. Oncology, Deep Learning, Economics, Neuroscience",
                help="Your main scientific discipline",
                key="_wiz_user_field",
            )

            u_keywords = st.text_area(
                "Research Keywords & Topics",
                value=curr_keywords or "single-cell genomics, immunotherapy, machine learning",
                placeholder="e.g. rna-seq, clinical trials, transformers, biomarkers",
                height=84,
                help="Used to tailor suggested seminal papers when starting new projects",
                key="_wiz_user_keywords",
            )

        with col_w2:
            st.markdown(
                """
                <div class="glass-panel" style="margin-bottom: 14px; padding: 18px 20px; border-radius: 16px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 1.12rem; font-weight: 700; color: var(--text-main); margin-bottom: 4px;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 6px; background: rgba(52, 199, 89, 0.15); color: #34c759; font-size: 0.82rem; font-weight: 700;">2</span>
                        <span>Local Vault Storage</span>
                    </div>
                    <p style="font-size: 0.84rem; color: var(--text-muted, #86868b); margin-bottom: 0px; line-height: 1.4;">
                        Choose where all your projects, PDFs, and screening decisions are stored.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Folder selection with local desktop storage browser
            parent_initial = st.session_state.get("_wiz_parent_folder_val", default_vault_parent)
            col_pf1, col_pf2 = st.columns([3.2, 1.2], vertical_alignment="bottom")
            with col_pf1:
                parent_folder = st.text_input(
                    "Vault Parent Folder",
                    value=parent_initial,
                    help="Directory where your Research Vault folder will be created",
                    key="_wiz_parent_folder",
                )
            with col_pf2:
                if st.button("📂 Browse...", key="_wiz_browse_parent_btn", use_container_width=True, help="Browse your computer storage"):
                    chosen = VP.native_folder_dialog(
                        prompt="Select Parent Folder for Vellum Vault",
                        default_dir=parent_folder or default_vault_parent,
                    )
                    if chosen:
                        st.session_state["_wiz_parent_folder_val"] = chosen
                        st.session_state["_wiz_parent_folder"] = chosen
                        st.rerun()

            vault_name = st.text_input(
                "Vault Folder Name",
                value="Vellum_Research_Vault",
                help="Folder name for all your systematic reviews and papers",
                key="_wiz_vault_name",
            )

            initial_proj = st.text_input(
                "First Project Name",
                value="Systematic_Review_2026",
                help="Initial project workspace to start with",
                key="_wiz_init_proj",
            )

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        if can_return:
            col_act1, col_act2 = st.columns([3, 1])
            with col_act1:
                submit_clicked = st.button("✨ Save Settings & Return to Workspace", type="primary", use_container_width=True, key="_wiz_submit_btn")
            with col_act2:
                if st.button("← Cancel & Return", type="secondary", use_container_width=True, key="_wiz_cancel_btn"):
                    st.session_state["_show_welcome_hub"] = False
                    st.rerun()
        else:
            submit_clicked = st.button("✨ Complete Setup & Launch Vellum", type="primary", use_container_width=True, key="_wiz_submit_btn")

        if submit_clicked:
            if not u_name.strip():
                st.warning("Please enter your name.")
            else:
                # Save user profile
                VW.set_user_profile(
                    name=u_name.strip(),
                    field=u_field.strip(),
                    keywords=u_keywords.strip(),
                )

                # Initialize vault directory
                v_path = Path(parent_folder.strip()) / vault_name.strip()
                v_path.mkdir(parents=True, exist_ok=True)
                VW.set_vault_dir(v_path, initialized=True)

                # Create initial project if not already existing
                p_name = initial_proj.strip() or "Default_Project"
                if p_name not in VW.list_projects():
                    VW.create_project(p_name)
                VW.set_active_project(p_name)

                st.session_state["_show_welcome_hub"] = False
                st.toast(f"Welcome to Vellum, {u_name.strip()}!", icon="🎉")
                vellum_pages.go("overview")

    with tab2:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        col_ex1, col_ex2 = st.columns([1.4, 1], gap="large")

        with col_ex1:
            st.markdown(
                """
                <div class="glass-panel" style="padding: 16px 20px; margin-bottom: 14px;">
                    <div style="font-size: 1.15rem; font-weight: 700; color: var(--apple-blue, #007aff); margin-bottom: 4px;">
                        📂 Select Existing Research Vault
                    </div>
                    <p style="font-size: 0.85rem; color: var(--text-muted, #86868b); margin-bottom: 0px;">
                        Point Vellum to an existing vault folder on this machine.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Local desktop storage browser for existing vault
            existing_initial = st.session_state.get("_hub_existing_vault_val", "")
            col_ex_in1, col_ex_in2 = st.columns([3.2, 1.2], vertical_alignment="bottom")
            with col_ex_in1:
                existing_path = st.text_input(
                    "Existing Vault Path",
                    value=existing_initial,
                    placeholder=r"e.g. C:\Users\Username\Documents\Vellum_Research_Vault",
                    key="_hub_existing_vault_input",
                )
            with col_ex_in2:
                if st.button("📂 Browse...", key="_hub_browse_existing_btn", use_container_width=True, help="Browse your computer storage"):
                    chosen = VP.native_folder_dialog(
                        prompt="Select Existing Vellum Research Vault Folder",
                        default_dir=existing_path or default_vault_parent,
                    )
                    if chosen:
                        st.session_state["_hub_existing_vault_val"] = chosen
                        st.session_state["_hub_existing_vault_input"] = chosen
                        st.rerun()

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            col_open1, col_open2 = st.columns([2, 1] if can_return else [1, 0.01])
            with col_open1:
                if st.button("Open Vault", type="primary", use_container_width=True, key="_hub_open_existing_btn"):
                    p = Path(existing_path.strip())
                    if p.exists() and p.is_dir():
                        VW.set_vault_dir(p, initialized=True)
                        st.session_state["_show_welcome_hub"] = False
                        st.toast(f"Loaded vault: {p.name}", icon="📁")
                        st.rerun()
                    else:
                        st.error("Specified directory does not exist. Please check the path or use Browse.")
            if can_return:
                with col_open2:
                    if st.button("← Return", type="secondary", use_container_width=True, key="_hub_cancel_tab2"):
                        st.session_state["_show_welcome_hub"] = False
                        st.rerun()

        with col_ex2:
            recent = VW.get_recent_vaults()
            st.markdown("#### 🕒 Recent Vaults")
            if not recent:
                st.caption("No recent vaults recorded yet.")
            else:
                for idx, r_path in enumerate(recent):
                    with st.container(border=True):
                        st.markdown(f"**📁 {Path(r_path).name}**")
                        st.caption(f"`{r_path}`")
                        if st.button("Switch to this Vault", key=f"_rec_btn_{idx}", use_container_width=True):
                            if Path(r_path).exists():
                                VW.set_vault_dir(r_path, initialized=True)
                                st.session_state["_show_welcome_hub"] = False
                                st.rerun()
                            else:
                                st.error("Path not found on disk.")
