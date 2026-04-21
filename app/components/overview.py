"""
Overview component — Wrapper for backward compatibility.
Actual implementation moved to tabs/tab_tong_quan.py.
"""

from tabs.tab_tong_quan import render as _render_overview

def render_overview(state):
    """Render the overview section. Delegates to tabs/tab_tong_quan."""
    _render_overview(state)
