"""
app_pages/citation_graph.py — Interactive Citation Network Explorer for Vellum.

Renders an interactive force-directed graph of academic papers around a seed work,
revealing prior foundational literature, derivative breakthroughs, and co-citations.
"""

from __future__ import annotations

import html
import json
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

import citation_core as CC
import vellum_brand as VB
import vellum_theme as VT
import vellum_pages


def render():
    """Module entry point called by _render_module()."""
    render_citation_graph()


def render_citation_graph():
    VB.header()

    st.markdown("### 🕸️ Citation Network Explorer")
    st.caption(
        "Explore the scholarly lineage of any research paper. Discover foundational works "
        "cited by the author (upstream) and influential papers that cited this work (downstream)."
    )

    # Handle pending target from re-centering or examples BEFORE widget instantiation
    pending_target = st.session_state.pop("_cg_pending_target", None)
    if pending_target:
        st.session_state["cg_query_input"] = str(pending_target)
        st.session_state["_cg_force_rebuild"] = True

    # Check if a seed DOI was handed over from another page (Literature / Library / Deep)
    handover_doi = st.session_state.pop("_graph_seed_doi", None)
    if handover_doi:
        st.session_state["cg_query_input"] = str(handover_doi)
        st.session_state["_cg_force_rebuild"] = True

    # ── 1. Search & Seed Input ────────────────────────────────────────────────
    with st.container():
        c_in, c_btn = st.columns([5, 1])
        with c_in:
            query = st.text_input(
                "Seed paper DOI, title, or OpenAlex ID",
                value=st.session_state.get("cg_query_input", ""),
                placeholder="e.g. 10.1038/s41586-020-2649-2 or Attention Is All You Need",
                key="cg_query_input",
            )
        with c_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            search_btn = st.button("Explore 🚀", width="stretch", type="primary")

    # Quick seed examples
    with st.expander("💡 Example Seminal Papers to Explore", expanded=False):
        ex_cols = st.columns(3)
        if ex_cols[0].button("Attention Is All You Need (Transformers)", key="ex_trans", width="stretch"):
            st.session_state["_cg_pending_target"] = "10.48550/arXiv.1706.03762"
            st.rerun()
        if ex_cols[1].button("Deep Residual Learning (ResNet)", key="ex_resnet", width="stretch"):
            st.session_state["_cg_pending_target"] = "10.1109/CVPR.2016.90"
            st.rerun()
        if ex_cols[2].button("AlphaFold Protein Structure Prediction", key="ex_af2", width="stretch"):
            st.session_state["_cg_pending_target"] = "10.1038/s41586-021-03819-2"
            st.rerun()

    # Advanced Graph Options
    with st.expander("⚙️ Graph Depth & Filters", expanded=False):
        col_ref, col_cite = st.columns(2)
        max_refs = col_ref.slider("Max References (Cited Prior Works)", min_value=5, max_value=30, value=15, step=5)
        max_cites = col_cite.slider("Max Citing Papers (Derivative Works)", min_value=5, max_value=30, value=15, step=5)

    effective_query = (query or "").strip()

    if not effective_query:
        st.info("Enter a DOI or paper title above to generate the visual citation network.")
        return

    # ── 2. Resolve Seed & Build Graph ─────────────────────────────────────────
    force_rebuild = st.session_state.pop("_cg_force_rebuild", False)
    last_query = st.session_state.get("_cg_last_query")
    active_graph = st.session_state.get("cg_active_data")

    needs_rebuild = (
        force_rebuild
        or search_btn
        or (effective_query != last_query)
        or not active_graph
    )

    if needs_rebuild:
        with st.spinner(f"Resolving seed metadata and building citation graph for '{effective_query}'…"):
            seed = CC.resolve_seed(effective_query)
            if not seed:
                st.error(f"Could not resolve a research paper matching '{effective_query}'. Please check the DOI or title.")
                return
            graph_data = CC.build_citation_network(
                seed, max_references=max_refs, max_citations=max_cites
            )
            st.session_state["cg_active_data"] = graph_data
            st.session_state["_cg_last_query"] = effective_query
            st.session_state["cg_inspected_id"] = seed["id"]
    else:
        graph_data = active_graph

    if not graph_data:
        return

    stats = graph_data.get("stats", {})
    st.markdown(
        f"**Graph Overview:** **{stats.get('total_nodes', 0)}** papers • "
        f"**{stats.get('references_count', 0)}** cited prior works • "
        f"**{stats.get('citations_count', 0)}** citing derivative works"
    )

    dark = getattr(VT, "is_dark_mode", lambda: False)()

    # ── 3. Render D3.js Force-Directed Interactive Graph ──────────────────────
    _render_d3_graph(graph_data, dark=dark)

    # ── 4. Paper Inspector & Action Drawer ─────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📄 Paper Inspector")

    nodes = graph_data.get("nodes", [])
    node_dict = {n["id"]: n for n in nodes}

    options = [n["id"] for n in nodes]
    labels = {
        n["id"]: f"[{n['type'].upper()}] ({n['year'] or 'N/A'}) {str(n.get('title') or 'Untitled')[:65]}…"
        for n in nodes
    }

    current_sel = st.session_state.get("cg_inspected_id", graph_data.get("seed_id"))
    if current_sel not in node_dict:
        current_sel = graph_data.get("seed_id")

    picked_id = st.selectbox(
        "Select paper to inspect details and actions:",
        options=options,
        index=options.index(current_sel) if current_sel in options else 0,
        format_func=lambda x: labels.get(x, str(x)),
        key="cg_node_selector",
    )
    inspected = node_dict.get(picked_id)

    if inspected:
        _render_inspector(inspected, graph_data, dark=dark)

    # ── 5. Bulk Export Sub-Graph ───────────────────────────────────────────────
    st.markdown("---")
    with st.expander("💾 Export Discovered Papers", expanded=False):
        df_export = pd.DataFrame([
            {
                "Type": n["type"].capitalize(),
                "Year": n["year"],
                "Title": n["title"],
                "Authors": n["authors"],
                "Venue": n["venue"],
                "Citations": n["citations"],
                "DOI": n["doi"],
                "PDF_URL": n["pdf_url"],
            }
            for n in nodes
        ])
        st.dataframe(df_export, width="stretch", hide_index=True)

        valid_downloadable = [n for n in nodes if n.get("doi") or n.get("pdf_url")]
        n_dl = len(valid_downloadable)

        c_queue, c_dl, c_csv, c_bib = st.columns([1.3, 1.3, 1, 1])

        with c_queue:
            if st.button(
                f"📥 Queue All DOIs ({n_dl})",
                key="btn_queue_all_discovered_nodes",
                type="secondary",
                use_container_width=True,
                disabled=n_dl == 0,
                help="Add all discovered papers with DOIs to the download queue and open Downloader.",
            ):
                import vellum_direct_download as VDD
                p_name = VW.get_active_project()
                for p in valid_downloadable:
                    VDD.add_to_download_queue(p, p_name)

                payload = []
                for i, q in enumerate(valid_downloadable):
                    key = q.get("doi") or (q.get("pdf_url") or f"item-{i}")
                    payload.append({
                        "key": key,
                        "doi": q.get("doi") or "",
                        "pdf_url": q.get("pdf_url") or "",
                        "title": q.get("title") or key,
                    })
                st.session_state["pending_dois"] = payload
                st.session_state["_go_download"] = True
                st.toast(f"✅ Added {n_dl} papers to download queue!", icon="📥")
                st.rerun()

        with c_dl:
            if st.button(
                f"⚡ Download All PDFs ({n_dl})",
                key="btn_dl_all_discovered_nodes",
                type="primary",
                use_container_width=True,
                disabled=n_dl == 0,
                help="Queue all discovered papers and jump to PDF Downloader with Auto-Start.",
            ):
                import vellum_direct_download as VDD
                p_name = VW.get_active_project()
                for p in valid_downloadable:
                    VDD.add_to_download_queue(p, p_name)

                payload = []
                for i, q in enumerate(valid_downloadable):
                    key = q.get("doi") or (q.get("pdf_url") or f"item-{i}")
                    payload.append({
                        "key": key,
                        "doi": q.get("doi") or "",
                        "pdf_url": q.get("pdf_url") or "",
                        "title": q.get("title") or key,
                    })
                st.session_state["pending_dois"] = payload
                st.session_state["_go_download"] = True
                st.toast(f"🚀 Launching download for {n_dl} papers...", icon="⚡")
                st.rerun()

        with c_csv:
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📄 Download as CSV",
                data=csv_data,
                file_name=f"vellum_citation_graph_{inspected['doi'] or 'export'}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with c_bib:
            bibtex_entries = []
            for n in nodes:
                key = f"paper_{n['year']}_{n['id'][:6]}"
                doi_field = f"  doi = {{{n['doi']}}},\n" if n["doi"] else ""
                bib = (
                    f"@article{{{key},\n"
                    f"  title = {{{n['title']}}},\n"
                    f"  author = {{{n['authors']}}},\n"
                    f"  year = {{{n['year']}}},\n"
                    f"  journal = {{{n['venue']}}},\n"
                    f"{doi_field}"
                    f"}}"
                )
                bibtex_entries.append(bib)
            bib_data = "\n\n".join(bibtex_entries).encode("utf-8")
            st.download_button(
                "📚 Download as BibTeX",
                data=bib_data,
                file_name=f"vellum_citation_graph_{inspected['doi'] or 'export'}.bib",
                mime="text/plain",
                use_container_width=True,
            )


def _render_inspector(paper: Dict[str, Any], graph_data: Dict[str, Any], dark: bool = False):
    """Renders details and action buttons for the selected node in Litmaps style."""
    p_type = paper.get("type", "node").upper()

    if dark:
        card_bg = "#1e222d"
        card_border = "1px solid rgba(255, 255, 235, 0.15)"
        title_color = "#ffffeb"
        text_muted = "#a0a096"
        card_shadow = "0 2px 10px rgba(0, 0, 0, 0.3)"
        badge_bg = "#ff6c4c" if p_type == "SEED" else ("#0ea5e9" if p_type == "REFERENCE" else "#10b981")
        badge_text = "#ffffff"
    else:
        card_bg = "#ffffff"
        card_border = "1.5px solid #e4e4d0"
        title_color = "#1a1a1a"
        text_muted = "#4a5568"
        card_shadow = "0 2px 12px rgba(26, 26, 26, 0.04)"
        badge_bg = "#1e293b" if p_type == "SEED" else ("#2563eb" if p_type == "REFERENCE" else "#059669")
        badge_text = "#ffffff"

    st.markdown(
        f"""
        <div style="background:{card_bg}; border:{card_border}; border-radius:14px; padding:18px 20px; margin-bottom:14px; box-shadow:{card_shadow};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="background:{badge_bg}; color:{badge_text}; font-size:11px; font-weight:700; padding:3px 10px; border-radius:9999px; letter-spacing:0.04em;">
                    {p_type} PAPER
                </span>
                <span style="color:{text_muted}; font-size:12px; font-weight:550;">
                    📅 {paper.get('year', 'N/A')} • 📈 {paper.get('citations', 0):,} citations
                </span>
            </div>
            <h4 style="margin:0 0 8px 0; color:{title_color}; font-size:1.15rem; font-weight:700; line-height:1.4;">
                {paper.get('title', 'Untitled')}
            </h4>
            <p style="color:{text_muted}; font-size:13px; margin:0 0 6px 0; line-height:1.5;">
                👥 <b>Authors:</b> {paper.get('authors', 'Unknown')}
            </p>
            <p style="color:{text_muted}; font-size:13px; margin:0; line-height:1.5;">
                🏛️ <b>Venue:</b> {paper.get('venue', 'Unknown')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if paper.get("abstract"):
        with st.expander("📖 Abstract", expanded=False):
            st.write(paper["abstract"])

    # Action Toolbar
    act1, act2, act3, act4 = st.columns([1.2, 1.2, 1.3, 1.3])

    doi = paper.get("doi")
    with act1:
        seed_id = graph_data.get("seed_id")
        can_recenter = (
            paper["id"] != seed_id
            and (paper.get("doi") or paper.get("openalex_id") or paper.get("id") or paper.get("title"))
        )
        if can_recenter:
            if st.button("🔄 Re-center Here", key=f"btn_rec_{paper['id']}", use_container_width=True, type="primary"):
                new_target = paper.get("doi") or paper.get("openalex_id") or paper.get("id") or paper.get("title")
                st.session_state["_cg_pending_target"] = str(new_target)
                st.session_state.pop("cg_inspected_id", None)
                st.rerun()
        else:
            st.button("📍 Active Seed", disabled=True, use_container_width=True)

    with act2:
        if doi:
            st.link_button("🌐 Open via DOI", f"https://doi.org/{doi}", use_container_width=True)
        elif paper.get("pdf_url"):
            st.link_button("🌐 Open Web Link", paper["pdf_url"], use_container_width=True)
        else:
            st.button("No Web Link", disabled=True, use_container_width=True)

    with act3:
        import urllib.parse
        clean_doi = (doi or "").strip().lower().replace("https://doi.org/", "").replace("doi:", "")
        if clean_doi:
            cp_url = f"https://www.connectedpapers.com/main/{clean_doi}/graph"
        else:
            cp_url = f"https://www.connectedpapers.com/search?q={urllib.parse.quote(paper.get('title', ''))}"
        st.link_button("🕸️ Connected Papers", cp_url, use_container_width=True)

    with act4:
        if st.button("🧪 Screen in ASReview", key=f"btn_scr_{paper['id']}", use_container_width=True):
            from app_pages import screening as AS
            sessions = AS.load_screening_sessions()
            sess = AS.get_active_session(sessions)
            cands = sess.get("candidates", [])
            comb, _, _ = AS.deduplicate_records(cands, [paper], source_name="Citation Graph")
            sess["candidates"] = comb
            AS.save_screening_sessions(sessions)
            st.session_state["_active_tab"] = "screening"
            st.toast("✅ Paper added to ASReview Screening queue!", icon="🧪")
            vellum_pages.go("screening")

    import vellum_paper_actions
    vellum_paper_actions.render_paper_action_bar(
        paper,
        key_prefix=f"cg_insp_{paper['id']}",
        show_graph=False,
        show_direct_download=True,
    )


def _render_d3_graph(graph_data: Dict[str, Any], dark: bool = False):
    """Embeds an interactive D3.js force-directed physics graph in Litmaps style."""
    graph_json = json.dumps(graph_data).replace("</script>", "<\\/script>")

    if dark:
        body_bg = "#0d1712"
        container_border = "1.5px solid rgba(167, 215, 197, 0.16)"
        link_stroke = "rgba(167, 215, 197, 0.28)"
        link_opacity = "0.75"
        seed_fill = "#7c3aed"
        seed_stroke = "#c084fc"
        seed_stroke_width = "4.5px"
        ref_fill = "#13251c"
        ref_stroke = "#a7d7c5"
        ref_stroke_width = "2.5px"
        cite_fill = "#13251c"
        cite_stroke = "#52b788"
        cite_stroke_width = "2.5px"
        label_fill = "#f4f7f4"
        label_shadow = "0 1px 3px #000000"
        legend_bg = "rgba(19, 37, 28, 0.94)"
        legend_border = "1px solid rgba(167, 215, 197, 0.22)"
        legend_color = "#f4f7f4"
        tooltip_bg = "#162d22"
        tooltip_border = "1px solid rgba(167, 215, 197, 0.24)"
        tooltip_color = "#f4f7f4"
        tooltip_shadow = "0 8px 24px rgba(0,0,0,0.5)"
        seed_dot = "#c084fc"
        ref_dot = "#a7d7c5"
        cite_dot = "#52b788"
    else:
        # Fernly Botanical Bento / Connected Papers Light Palette
        body_bg = "#fafcf9"
        container_border = "1.5px solid #dce7e1"
        link_stroke = "rgba(27, 67, 50, 0.22)"
        link_opacity = "0.85"
        seed_fill = "#6b21a8"
        seed_stroke = "#a855f7"
        seed_stroke_width = "4.5px"
        ref_fill = "#ffffff"
        ref_stroke = "#a7d7c5"
        ref_stroke_width = "2.5px"
        cite_fill = "#ffffff"
        cite_stroke = "#1b4332"
        cite_stroke_width = "2.5px"
        label_fill = "#1b4332"
        label_shadow = "0 1px 2px #ffffff, 0 0 5px #ffffff"
        legend_bg = "rgba(255, 255, 255, 0.96)"
        legend_border = "1.5px solid #dce7e1"
        legend_color = "#1b4332"
        tooltip_bg = "#ffffff"
        tooltip_border = "1.5px solid #dce7e1"
        tooltip_color = "#1b4332"
        tooltip_shadow = "0 8px 24px rgba(27,67,50,0.12)"
        seed_dot = "#a855f7"
        ref_dot = "#a7d7c5"
        cite_dot = "#1b4332"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://d3js.org/d3.v7.min.js"></script>
      <style>
        /* Connected Papers & Fernly Botanical Palette (legacy compat: #2563eb #1e293b) */
        body {{
          margin: 0;
          padding: 0;
          background: {body_bg};
          overflow: hidden;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          user-select: none;
        }}
        #canvas-container {{
          width: 100%;
          height: 520px;
          position: relative;
          background: {body_bg};
          border: {container_border};
          border-radius: 16px;
          box-sizing: border-box;
        }}
        svg {{
          width: 100%;
          height: 100%;
          cursor: grab;
          border-radius: 16px;
        }}
        svg:active {{
          cursor: grabbing;
        }}
        .link {{
          stroke: {link_stroke};
          stroke-opacity: {link_opacity};
          stroke-width: 1.5px;
        }}
        .node {{
          cursor: pointer;
          transition: transform 0.2s, stroke-width 0.15s;
        }}
        .node-seed {{
          fill: {seed_fill};
          stroke: {seed_stroke};
          stroke-width: {seed_stroke_width};
        }}
        .node-reference {{
          fill: {ref_fill};
          stroke: {ref_stroke};
          stroke-width: {ref_stroke_width};
        }}
        .node-citation {{
          fill: {cite_fill};
          stroke: {cite_stroke};
          stroke-width: {cite_stroke_width};
        }}
        .node:hover {{
          stroke-width: 4px;
          filter: drop-shadow(0 2px 8px rgba(37,99,235,0.4));
        }}
        .node-label {{
          fill: {label_fill};
          font-size: 11px;
          font-weight: 600;
          pointer-events: none;
          text-shadow: {label_shadow};
        }}
        #tooltip {{
          position: absolute;
          display: none;
          background: {tooltip_bg};
          border: {tooltip_border};
          border-radius: 10px;
          padding: 12px 16px;
          color: {tooltip_color};
          font-size: 12px;
          max-width: 320px;
          pointer-events: none;
          box-shadow: {tooltip_shadow};
          z-index: 100;
        }}
        #legend {{
          position: absolute;
          top: 14px;
          left: 16px;
          background: {legend_bg};
          border: {legend_border};
          border-radius: 9999px;
          padding: 6px 16px;
          font-size: 12px;
          font-weight: 550;
          color: {legend_color};
          display: flex;
          align-items: center;
          gap: 16px;
          z-index: 10;
          box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .legend-item {{
          display: flex;
          align-items: center;
          gap: 6px;
        }}
        .legend-dot {{
          width: 11px;
          height: 11px;
          border-radius: 50%;
        }}
      </style>
    </head>
    <body>
      <div id="canvas-container">
        <div id="legend">
          <div class="legend-item"><span class="legend-dot" style="background:{seed_dot};"></span> Seed Paper</div>
          <div class="legend-item"><span class="legend-dot" style="background:{ref_dot};"></span> Prior Work (Cited)</div>
          <div class="legend-item"><span class="legend-dot" style="background:{cite_dot};"></span> Derivative Work (Citing)</div>
        </div>
        <div id="tooltip"></div>
        <svg id="network-svg"></svg>
      </div>

      <script>
        const data = {graph_json};
        const width = window.innerWidth || 800;
        const height = 520;

        const svg = d3.select("#network-svg")
          .attr("viewBox", [0, 0, width, height]);

        const g = svg.append("g");

        const zoom = d3.zoom()
          .scaleExtent([0.3, 4])
          .on("zoom", (event) => {{
            g.attr("transform", event.transform);
          }});
        svg.call(zoom);

        const simulation = d3.forceSimulation(data.nodes)
          .force("link", d3.forceLink(data.links).id(d => d.id).distance(d => d.type === 'cites' ? 95 : 120))
          .force("charge", d3.forceManyBody().strength(-240))
          .force("center", d3.forceCenter(width / 2, height / 2))
          .force("collision", d3.forceCollide().radius(d => nodeRadius(d) + 12));

        const link = g.append("g")
          .selectAll("line")
          .data(data.links)
          .join("line")
          .attr("class", "link");

        function nodeRadius(d) {{
          if (d.type === "seed") return 18;
          const citations = d.citations || 0;
          return Math.max(9, Math.min(22, 9 + Math.log10(citations + 1) * 3.8));
        }}

        function getLitmapsLabel(d) {{
          let author = "";
          if (d.authors) {{
            const first = d.authors.split(/[,;]/)[0].trim();
            const parts = first.split(" ").filter(Boolean);
            author = parts.length > 0 ? parts[parts.length - 1] : "";
          }}
          const yr = d.year || "";
          if (author && yr) return `${{author}}, ${{yr}}`;
          if (author) return author;
          if (yr) return `(${{yr}})`;
          return d.title ? d.title.substring(0, 16) + '…' : '';
        }}

        const node = g.append("g")
          .selectAll("circle")
          .data(data.nodes)
          .join("circle")
          .attr("class", d => `node node-${{d.type}}`)
          .attr("r", nodeRadius)
          .call(drag(simulation));

        const label = g.append("g")
          .selectAll("text")
          .data(data.nodes)
          .join("text")
          .attr("class", "node-label")
          .attr("dy", d => nodeRadius(d) + 14)
          .attr("text-anchor", "middle")
          .text(getLitmapsLabel);

        const tooltip = d3.select("#tooltip");

        node.on("mouseover", (event, d) => {{
          const typeColor = d.type === 'seed' ? '{seed_dot}' : (d.type === 'reference' ? '{ref_dot}' : '{cite_dot}');
          const titleColor = '{tooltip_color}';
          const mutedColor = '{'#a0a096' if dark else '#64748b'}';
          const citeColor = '{'#38bdf8' if dark else '#2563eb'}';
          tooltip.style("display", "block")
            .html(`
              <div style="color:${{typeColor}}; font-weight:700; text-transform:uppercase; font-size:10px; margin-bottom:4px; letter-spacing:0.04em;">
                ${{d.type.toUpperCase()}} PAPER (${{d.year || 'N/A'}})
              </div>
              <div style="font-weight:700; color:${{titleColor}}; margin-bottom:6px; font-size:13px; line-height:1.35;">${{d.title}}</div>
              <div style="color:${{mutedColor}}; font-size:11px; margin-bottom:3px;">👥 ${{d.authors || 'Unknown'}}</div>
              <div style="color:${{mutedColor}}; font-size:11px; margin-bottom:4px;">🏛️ ${{d.venue || 'Unknown'}}</div>
              <div style="color:${{citeColor}}; font-size:11px; font-weight:600;">📈 ${{d.citations.toLocaleString()}} citations</div>
            `);
        }})
        .on("mousemove", (event) => {{
          tooltip.style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 20) + "px");
        }})
        .on("mouseout", () => {{
          tooltip.style("display", "none");
        }});

        simulation.on("tick", () => {{
          link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

          node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

          label
            .attr("x", d => d.x)
            .attr("y", d => d.y);
        }});

        function drag(sim) {{
          return d3.drag()
            .on("start", (event, d) => {{
              if (!event.active) sim.alphaTarget(0.3).restart();
              d.fx = d.x;
              d.fy = d.y;
            }})
            .on("drag", (event, d) => {{
              d.fx = event.x;
              d.fy = event.y;
            }})
            .on("end", (event, d) => {{
              if (!event.active) sim.alphaTarget(0);
              d.fx = null;
              d.fy = null;
            }});
        }}
      </script>
    </body>
    </html>
    """

    st.components.v1.html(html_content, height=540, scrolling=False)
