"""Global keyboard shortcuts for the Vellum desktop app.

Why this is not just a ``st.text_input`` with ``on_change``
------------------------------------------------------------
A Streamlit text input only fires when it has focus, so a shortcut bound to
it would only work while the user happened to be typing in that one widget.
Screening is a high-frequency task where the reviewer's hands never leave the
keyboard, so the shortcut has to work while focus is anywhere in the app.

How it works
------------
Streamlit renders into an ordinary DOM document, and a custom component is
served from the *same origin* as the app. That combination is what makes this
possible: the component's iframe can reach ``window.parent.document`` and
observe keystrokes that land anywhere in the app, not only inside the
component itself. The component therefore never needs to hold focus.

The listener reports the pressed key back to Python, and Python runs exactly
the same handler the on-screen button would run - there is one code path, so
the shortcut and the button cannot drift apart.

Caveats worth knowing
---------------------
* The shortcut is inactive while the user is typing in a text field, or
  while a modal dialog is open. Both are handled in the component itself,
  because the component is the only place that can see the DOM.
* ``Ctrl``/``Cmd``/``Alt`` combinations are ignored, so browser and
  application shortcuts keep working.
* Each press carries a timestamp, so pressing the *same* key twice in a row
  is still detected as two distinct presses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import streamlit as st
import streamlit.components.v1 as components

# The component's frontend lives next to this module and is shipped into the
# frozen bundle by vellum_packaging.py (see TREES).
_COMPONENT_DIR = Path(__file__).resolve().parent / "keyboard_component"

# Keys we never want to interpret as a shortcut, whatever the page asks for.
_RESERVED = {"escape", "tab", "enter", "backspace", "delete", "shift", "control",
             "alt", "meta", "capslock", "arrowup", "arrowdown", "arrowleft",
             "arrowright", "home", "end", "pageup", "pagedown", " "}

_component = components.declare_component(
    "vellum_keyboard",
    path=str(_COMPONENT_DIR),
)


def _runtime_available() -> bool:
    """True when a real browser session is attached."""
    try:
        return bool(st.runtime.exists())
    except Exception:
        return False


def _is_new_press(stamp, last) -> bool:
    """True when this press has not been handled yet.

    The component keeps returning its last value on every rerun, so the same
    press would otherwise be applied again and again. The timestamp makes two
    presses of the *same* key distinguishable.

    Kept as a pure function so it can be tested without a live Streamlit
    session.
    """
    return last is None or stamp > last


def capture(shortcuts: Mapping[str, str], disabled: bool = False) -> str | None:
    """Render the key listener and return the shortcut pressed since last call.

    Parameters
    ----------
    shortcuts:
        Mapping of lowercase key -> action name, e.g. ``{"i": "include"}``.
    disabled:
        When True the listener is rendered but inert. Useful while a modal is
        open.

    Returns
    -------
    str | None
        The action name for the key pressed since the previous call, or None.
    """
    if not _runtime_available() or not shortcuts:
        return None

    payload = {
        "map": {k.lower(): v for k, v in shortcuts.items() if k.lower() not in _RESERVED},
        "disabled": bool(disabled),
    }

    try:
        value = _component(
            config=json.dumps(payload),
            default=None,
            key="_vellum_keyboard_capture",
        )
    except Exception:
        # A component failure must never take the page down.
        return None

    if not isinstance(value, dict):
        return None

    action = value.get("action")
    stamp = value.get("ts")
    if not action or stamp is None:
        return None

    if action == "__diag__":
        st.session_state["_vellum_keyboard_diag"] = value.get("diag")
        return None

    # The component keeps returning the last value on every rerun, so compare
    # against what we already handled. The timestamp makes two identical keys
    # pressed in a row distinguishable.
    last = st.session_state.get("_vellum_keyboard_last_stamp")
    if not _is_new_press(stamp, last):
        return None
    st.session_state["_vellum_keyboard_last_stamp"] = stamp

    return action


def clear() -> None:
    """Forget the last handled press (used when leaving a page)."""
    st.session_state.pop("_vellum_keyboard_last_stamp", None)
