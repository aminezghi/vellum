"""Researchers page: search a directory of author profiles and save the ones
that matter, plus a CV built from the records screened in Literature check.

Two views:

* **Directory** — search OpenAlex / ORCID / Semantic Scholar, inspect a
  profile's metrics and works, and save profiles to a local store.
* **My CV** — the original portfolio view: a publication list assembled from
  Literature check screening or local PDFs, exported as Markdown/HTML/CSV/
  BibTeX.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import researchers_core as RC  # noqa: E402

VIEW_SEARCH = "Directory"
VIEW_CV = "My CV"


def _profile_frame(profiles):
    rows = []
    for p in profiles:
        rows.append({
            "name": p.get("name") or "",
            "affiliation": "; ".join(p.get("affiliations") or [])[:120],
            "orcid": p.get("orcid") or "",
            "source": p.get("source") or "",
            "works": p.get("works_count"),
            "citations": p.get("citations"),
            "h_index": p.get("h_index"),
            "also_in": ", ".join(p.get("also_found_in") or []),
        })
    return pd.DataFrame(rows)


def _works_frame(works):
    rows = []
    for w in works:
        rows.append({
            "year": w.get("year"),
            "title": w.get("title") or "",
            "journal": w.get("journal") or "",
            "cited_by": w.get("cited_by"),
            "doi": w.get("doi") or "",
            "is_oa": w.get("is_oa") or "",
            "pdf_url": w.get("pdf_url") or "",
        })
    return pd.DataFrame(rows)


def _cv_frame():
    """Reuse the portfolio module's record gathering."""
    from app_pages import portfolio
    return portfolio._gather_records()


def render():
    st.subheader("Researchers")
    st.caption("Find researchers, compare their profiles and keep a shortlist. "
               "Everything is saved locally on this machine.")

    email = st.session_state.get("lit_email") or None
    s2_key = st.session_state.get("lit_s2_key") or None

    view = st.segmented_control(
        "View", [VIEW_SEARCH, VIEW_CV], default=VIEW_SEARCH,
        label_visibility="collapsed", key="researchers_view")

    if view == VIEW_CV:
        _render_cv(email)
    else:
        _render_directory(email, s2_key)


# ── Directory ─────────────────────────────────────────────────────────────────
def _render_directory(email, s2_key):
    with st.form("researcher_search", border=False):
        q_col, n_col, go_col = st.columns([5, 1, 1])
        query = q_col.text_input(
            "Name, ORCID, affiliation or topic", placeholder="e.g. Amine Zouaghi",
            label_visibility="collapsed")
        per_source = n_col.number_input("Per source", 5, 50, 15, 5,
                                        label_visibility="collapsed")
        submitted = go_col.form_submit_button(
            ":material/search: Search", width="stretch", type="primary")

    src_cols = st.columns(3)
    chosen = []
    for (key, label), col in zip(RC.SOURCES.items(), src_cols):
        if col.toggle(label, value=True, key=f"rsrc_{key}"):
            chosen.append(key)

    results = st.session_state.get("researcher_results") or []
    notes = st.session_state.get("researcher_notes") or []

    if submitted:
        if not query.strip():
            st.warning("Type a name, ORCID or topic first.")
        elif not chosen:
            st.warning("Pick at least one source.")
        else:
            with st.status(f"Searching {', '.join(RC.SOURCES[c] for c in chosen)}…",
                           expanded=True) as status:
                results, notes = RC.search(query, tuple(chosen), int(per_source),
                                           email, s2_key)
                st.session_state.researcher_results = results
                st.session_state.researcher_notes = notes
                st.session_state.researcher_query = query
                status.update(label=f"{len(results)} profile(s) found",
                              state="complete")

    for note in notes:
        st.caption(f":material/info: {note}")

    if not results:
        st.info("Search by name, ORCID iD, affiliation or research topic. "
                "Profiles can be saved to the shortlist below.")
        _render_saved(email, s2_key)
        return

    saved_ids = {RC._norm_orcid(p.get("orcid")) or (p.get("name") or "").lower().strip()
                 for p in RC.list_saved()}

    flash = st.session_state.pop("researcher_flash", None)
    if flash:
        st.success(flash)

    df = _profile_frame(results)
    st.dataframe(
        df, width="stretch", hide_index=True, height=260,
        column_config={
            "name": st.column_config.TextColumn("Researcher", width="medium"),
            "affiliation": st.column_config.TextColumn("Affiliation", width="large"),
            "works": st.column_config.NumberColumn("Works", format="%.0f"),
            "citations": st.column_config.NumberColumn("Citations", format="%.0f"),
            "h_index": st.column_config.NumberColumn("h-index", format="%.0f"),
        })

    labels = {f"{p.get('name') or '(unnamed)'}  ·  {p.get('source')}": p for p in results}
    picked_label = st.selectbox("Inspect a profile", list(labels),
                                label_visibility="collapsed")
    profile = labels[picked_label]

    _render_profile(profile, saved_ids, email, s2_key)
    _render_saved(email, s2_key)


def _render_profile(profile, saved_ids, email, s2_key):
    ident = RC._norm_orcid(profile.get("orcid")) or \
        (profile.get("name") or "").lower().strip()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Works", profile.get("works_count") or "—")
    c2.metric("Citations", profile.get("citations") or "—")
    c3.metric("h-index", profile.get("h_index") or "—")
    c4.metric("i10-index", profile.get("i10_index") or "—")
    c5.metric("Open access", profile.get("oa_works") or "—")

    line = [profile.get("name") or ""]
    if profile.get("affiliations"):
        line.append(" · ".join(profile["affiliations"][:2]))
    st.markdown("  \n".join(f"*{x}*" for x in line if x))

    extras = []
    if profile.get("orcid"):
        extras.append(f"[ORCID {profile['orcid']}](https://orcid.org/{profile['orcid']})")
    if profile.get("homepage"):
        extras.append(f"[Profile]({profile['homepage']})")
    if profile.get("also_found_in"):
        extras.append("Also in " + ", ".join(profile["also_found_in"]))
    if extras:
        st.caption(" · ".join(extras))

    if profile.get("topics"):
        st.caption("Topics: " + ", ".join(
            t["name"] for t in profile["topics"] if t.get("name")))

    b1, b2 = st.columns(2)
    with b1:
        if st.button(":material/download: Fetch publication list",
                     width="stretch", key="fetch_works"):
            with st.status(f"Loading works from {profile['source']}…",
                           expanded=False) as status:
                updated, err = RC.fetch_details(profile, email, s2_key)
                if err:
                    status.update(label=err, state="error")
                else:
                    profile.clear()
                    profile.update(updated)
                    st.session_state.researcher_results = [
                        updated if r.get("key") == updated.get("key") else r
                        for r in (st.session_state.get("researcher_results") or [])]
                    status.update(
                        label=f"{len(updated.get('works') or [])} work(s) loaded",
                        state="complete")
    with b2:
        already = ident in saved_ids
        if st.button(":material/bookmark_added: Update shortlist" if already
                     else ":material/bookmark_add: Save to shortlist",
                     width="stretch", type="primary", disabled=already):
            RC.save_profile(profile)
            # A flag survives the rerun; st.success immediately before
            # st.rerun() would never be painted.
            st.session_state.researcher_flash = \
                f"Saved **{profile.get('name')}** to the shortlist."
            st.rerun()

    works = profile.get("works") or []
    if not works:
        return

    wdf = _works_frame(works)
    st.dataframe(
        wdf, width="stretch", hide_index=True, height=300,
        column_config={
            "title": st.column_config.TextColumn("Title", width="large"),
            "journal": st.column_config.TextColumn("Venue", width="medium"),
            "cited_by": st.column_config.NumberColumn("Cites", format="%.0f"),
            "year": st.column_config.NumberColumn("Year", format="%.0f"),
        })

    with st.expander("Export this publication list"):
        st.download_button(":material/download: CSV",
                           wdf.to_csv(index=False).encode("utf-8"),
                           file_name=f"{_slug(profile)}.csv",
                           mime="text/csv", width="content")
        try:
            import litcheck_core as LC
            st.download_button(":material/download: BibTeX",
                               LC.export_bibtex(works).encode("utf-8"),
                               file_name=f"{_slug(profile)}.bib",
                               mime="application/x-bibtex", width="content")
        except Exception:
            pass


def _slug(p):
    import re
    base = re.sub(r"[^a-z0-9]+", "-", (p.get("name") or "researcher").lower())
    return base.strip("-") or "researcher"


# ── Saved shortlist ───────────────────────────────────────────────────────────
def _render_saved(email, s2_key):
    saved = RC.list_saved()
    with st.expander(f":material/bookmarks: Saved profiles ({len(saved)})",
                     expanded=bool(saved)):
        if not saved:
            st.caption("Profiles you save appear here and persist between sessions.")
            return

        for p in saved:
            ident = RC._norm_orcid(p.get("orcid")) or \
                (p.get("name") or "").lower().strip()
            c1, c2 = st.columns([6, 1])
            with c1:
                bits = [p.get("name") or "(unnamed)"]
                if p.get("affiliations"):
                    bits.append(p["affiliations"][0])
                if p.get("works_count"):
                    bits.append(f"{p['works_count']} works")
                if p.get("citations"):
                    bits.append(f"{p['citations']} citations")
                st.markdown(" · ".join(str(b) for b in bits if b))
            with c2:
                if st.button(":material/delete:", key=f"del_{ident}",
                             help=f"Remove {p.get('name')}", width="stretch"):
                    RC.remove_profile(ident)
                    st.rerun()

        rows = RC.saved_works()
        if rows:
            wdf = _works_frame(rows)
            st.download_button(
                ":material/download: Download shortlist (CSV)",
                wdf.to_csv(index=False).encode("utf-8"),
                file_name="vellum_researchers.csv", mime="text/csv",
                width="content")
            import json
            st.download_button(
                ":material/download: Download shortlist (JSON)",
                json.dumps(saved, indent=1, default=str).encode("utf-8"),
                file_name="vellum_researchers.json", mime="application/json",
                width="content")


# ── My CV (original portfolio view) ───────────────────────────────────────────
def _render_cv(email):
    from app_pages import portfolio

    st.markdown("#### My CV")
    st.caption("A publication list built from what you screened in Literature "
               "check, enriched from local PDFs where available.")

    with st.expander("Profile details", expanded=False):
        prof = st.session_state.get("portfolio_profile") or {}
        defaults = {"name": "Your name", "affiliation": "", "email": "",
                    "orcid": "", "website": "", "tagline": ""}
        f1, f2, f3 = st.columns(3)
        prof["name"] = f1.text_input("Name", value=prof.get("name") or defaults["name"])
        prof["affiliation"] = f2.text_input("Affiliation", value=prof.get("affiliation") or "")
        prof["tagline"] = f3.text_input("Tagline", value=prof.get("tagline") or "")
        f4, f5, f6 = st.columns(3)
        prof["email"] = f4.text_input("Email", value=prof.get("email") or "")
        prof["orcid"] = f5.text_input("ORCID", value=prof.get("orcid") or "")
        prof["website"] = f6.text_input("Website", value=prof.get("website") or "")
        st.session_state.portfolio_profile = prof

    source = st.segmented_control(
        "Source", ["Screened records", "Local PDFs", "Combined"],
        default="Screened records", label_visibility="collapsed")

    with st.expander("Enrich from a local PDF folder (OCR)", expanded=False):
        import vellum_paths as VP
        folder = VP.render_folder_picker("Folder", key="cv_ocr_folder",
                                        default=st.session_state.get("out_dir"),
                                        recursive=True)
        limit = st.number_input("Max files", 1, 500, 40, 10)
        if st.button(":material/psychology: Extract titles, DOIs and abstracts",
                     width="content", disabled=not folder):
            with st.status(f"Reading up to {limit} PDF(s)…", expanded=True) as status:
                n = portfolio.ocr_enrich(folder, int(limit), 120)
                status.update(label=f"Processed {n} file(s)", state="complete")

    df = portfolio._gather_records() if source != "Local PDFs" else \
        portfolio._gather_downloads()
    if source == "Combined":
        df = portfolio._gather_records()

    if df is None or df.empty:
        st.info("Nothing to build a CV from yet. Screen records in Literature "
                "check, or download some PDFs.")
        return

    df = df[df.get("screen", "include") != "exclude"] if "screen" in df.columns else df
    if df.empty:
        st.info("Every record is marked 'not relevant'. Change the screening "
                "decisions in Literature check.")
        return

    m = portfolio.metrics_for(df)
    cols = st.columns(5)
    for col, (label, key) in zip(cols, [
            ("Publications", "publications"), ("Citations", "citations"),
            ("h-index", "h_index"), ("Journals", "journals"),
            ("Open access", "oa_share")]):
        value = m.get(key)
        col.metric(label, f"{value}%" if key == "oa_share" and value is not None
                   else (value if value is not None else "—"))

    st.dataframe(df, width="stretch", hide_index=True, height=300,
                 column_config={
                     "title": st.column_config.TextColumn("Title", width="large"),
                     "journal": st.column_config.TextColumn("Venue", width="medium"),
                     "cited_by": st.column_config.NumberColumn("Cites", format="%.0f"),
                 })

    prof = st.session_state.get("portfolio_profile") or {}
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(":material/download: Markdown CV",
                           portfolio.to_markdown(prof, df).encode("utf-8"),
                           file_name="vellum_cv.md", mime="text/markdown",
                           width="stretch")
    with d2:
        st.download_button(":material/download: HTML CV",
                           portfolio.to_html(prof, df).encode("utf-8"),
                           file_name="vellum_cv.html", mime="text/html",
                           width="stretch")
    with d3:
        st.download_button(":material/download: CSV",
                           df.to_csv(index=False).encode("utf-8"),
                           file_name="vellum_cv.csv", mime="text/csv",
                           width="stretch")