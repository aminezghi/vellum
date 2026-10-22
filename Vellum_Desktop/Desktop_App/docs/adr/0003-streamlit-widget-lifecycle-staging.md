# ADR 0003: Streamlit Widget Lifecycle & Staging State

## Context
Streamlit enforces a strict lifecycle rule: once an interactive widget with a unique key (such as `st.text_input(..., key='cg_query_input')` or `st.selectbox(..., key='...')`) has been instantiated during a script run, attempting to write to `st.session_state[key]` throws `StreamlitWidgetAlreadyInstantiatedError`. In multi-page workflows where actions on one page (or button clicks inside deep inspectors) want to programmatically refocus or prefill input widgets, direct mutation causes unhandled crashes.

## Decision
1. **Staging State Pattern**: Intersystem and inter-page transitions must NEVER directly mutate active widget keys. Instead, write to a staged state key prefixed with `_pending_` (e.g., `st.session_state["_cg_pending_target"] = new_seed`).
2. **Pre-Widget Consumption**: At the top of the target page or prior to widget rendering, inspect the pending key. If present, assign it to the target session state *before* the widget call, and delete the pending key:
   ```python
   if "_cg_pending_target" in st.session_state:
       st.session_state["cg_query_input"] = st.session_state.pop("_cg_pending_target")
   # Widget instantiation happens subsequently:
   query = st.text_input("Seed paper", key="cg_query_input")
   ```
3. **Graceful Widget Fallback**: Ensure callbacks use `st.rerun()` cleanly after staging transitions.

## Consequences
- Guaranteed elimination of `StreamlitWidgetAlreadyInstantiatedError`.
- Predictable data flow and navigation between pages (e.g. from Literature Check -> Citation Graph -> Downloader).
