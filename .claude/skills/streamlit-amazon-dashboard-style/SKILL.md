# Streamlit Amazon-Style E-Commerce Dashboard

## Trigger Conditions

Use this skill when the user mentions any of:
- "streamlit dashboard", "dashboard phong cách Amazon"
- "ecommerce analytics UI", "orange theme dashboard"
- "KPI cards streamlit", "thiết kế dashboard thương mại điện tử"
- Uploads or references a dashboard screenshot with orange/amber color scheme
- Asks about styling Streamlit with a retail/e-commerce theme

---

## Overview

This skill captures the full design system for an Amazon-inspired Streamlit dashboard used in e-commerce analytics. The aesthetic is warm, professional, and action-oriented — orange accents on white backgrounds, bold KPI numbers, and clean data tables.

**Key visual identity:**
- Amazon Orange (`#FF9900`) as the primary action/highlight color
- Warm off-white backgrounds (never pure white or dark)
- High-contrast KPI numbers with subdued labels
- Left-border accent pattern for card components

---

## Design Tokens (Quick Reference)

| Token | Value | Usage |
|-------|-------|-------|
| `--primary` | `#FF9900` | Buttons, borders, chart bars, active nav |
| `--secondary` | `#B85C00` | Hover states, donut slice 2, dark accents |
| `--accent` | `#E8C99A` | Donut slice 3, alternating table row |
| `--bg-page` | `#FFF8F0` | Page background |
| `--bg-card` | `#FFFFFF` | Card and chart backgrounds |
| `--bg-header` | `#FFE0B2` | Top header banner |
| `--text-main` | `#1A1A1A` | Primary text, KPI values |
| `--text-sub` | `#666666` | Descriptions, axis labels |
| `--text-muted` | `#999999` | Sub-labels, italic helpers |
| `--border-radius` | `12px` | Cards, chart containers |
| `--shadow` | `0 2px 8px rgba(0,0,0,0.08)` | Card elevation |

Full CSS variables + snippets → [references/css-tokens.md](references/css-tokens.md)

---

## Layout Architecture

```
┌─────────────────────────────────────────────────────┐
│  HEADER BANNER  (#FFE0B2 gradient)  Logo + Title    │
├──────┬──────────────────────────────────────────────┤
│      │  FILTER BAR  (category | price | toggles)    │
│ SIDE │──────────────────────────────────────────────┤
│ BAR  │  KPI CARDS  (5 cards, horizontal row)        │
│      │──────────────────────────────────────────────┤
│ 70px │  CHARTS  (bar | donut | combo | table)       │
│      │                                              │
└──────┴──────────────────────────────────────────────┘
│  FOOTER BAR  (#FF9900 background, white text pills) │
└─────────────────────────────────────────────────────┘
```

### Streamlit Layout Strategy
- Sidebar: `st.sidebar` with custom CSS to collapse to ~70px icon-only mode
- Header: `st.markdown()` HTML block injected at top of `app.py`
- Filter bar: `st.columns([2,2,1,1])` inside a styled container
- KPI row: `st.columns(5)` with each column containing a `st.markdown()` card
- Charts: `st.plotly_chart(fig, use_container_width=True)` inside styled `div`

---

## Component Inventory

| Component | Type | Reference |
|-----------|------|-----------|
| KPI Card | HTML/CSS via `st.markdown` | [components.md §1](references/components.md#kpi-card) |
| Bar Chart (Top 10) | Plotly `go.Bar` | [components.md §2](references/components.md#bar-chart) |
| Donut Chart | Plotly `go.Pie` hole=0.5 | [components.md §3](references/components.md#donut-chart) |
| Combo Chart | Plotly `go.Bar` + `go.Scatter` | [components.md §4](references/components.md#combo-chart) |
| Top 5 Table | Plotly `go.Table` | [components.md §5](references/components.md#top-5-table) |
| Filter Slider | `st.slider` + CSS | [components.md §6](references/components.md#filter-slider) |
| Toggle Switch | `st.toggle` + CSS | [components.md §7](references/components.md#toggle-switch) |
| Sidebar Nav | `st.sidebar` + CSS | [components.md §8](references/components.md#sidebar-nav) |
| Header Banner | `st.markdown` HTML | [components.md §9](references/components.md#header-banner) |
| Footer Bar | `st.markdown` HTML | [components.md §10](references/components.md#footer-bar) |

---

## Chart Library Guidance

**Preferred: Plotly** (`plotly.graph_objects`)
- Full control over colors, dual axes, hover templates
- Native Streamlit support via `st.plotly_chart`
- Use `fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')` for clean backgrounds

**Alternative: Altair**
- Good for declarative specs; use `.configure_view(stroke=None)` to remove borders
- Less flexible for dual-axis combos

**Avoid Matplotlib** for production dashboards — requires `st.pyplot()` which doesn't scale cleanly and lacks interactivity. If forced, use `rcParams` to set facecolor `#FFFFFF` and spine color `#E0E0E0`.

---

## Streamlit Limitations to Know

1. **CSS scope**: `st.markdown(..., unsafe_allow_html=True)` injects globally into the page — there is no component-level scoping. Use specific class names (e.g., `.amazon-kpi-card`) to avoid conflicts.

2. **No localStorage**: Streamlit re-renders on every interaction. Store filter state in `st.session_state`, not browser storage.

3. **Sidebar width**: Streamlit's sidebar has a minimum width (~250px by default). The "70px icon-only" look requires CSS `[data-testid="stSidebar"] { min-width: 70px !important; max-width: 70px !important; }` — this can break on Streamlit version updates.

4. **Dark mode conflicts**: Streamlit's built-in dark mode toggle overrides some CSS. Force light mode in `.streamlit/config.toml`:
   ```toml
   [theme]
   base = "light"
   primaryColor = "#FF9900"
   backgroundColor = "#FFF8F0"
   secondaryBackgroundColor = "#FFE0B2"
   textColor = "#1A1A1A"
   ```

5. **Component re-render**: Heavy `st.markdown` HTML blocks re-render on every state change. For static UI (header, footer), use `@st.cache_resource` wrapper or place them outside the main reactive flow.

6. **Plotly theming**: Set `config={'displayModeBar': False}` in `st.plotly_chart()` to hide the Plotly toolbar for a cleaner look.

---

## Implementation Checklist

- [ ] Set `config.toml` theme tokens first (affects all native widgets)
- [ ] Inject global CSS via a single `st.markdown(CSS_BLOCK, unsafe_allow_html=True)` call at app startup
- [ ] Build KPI cards as HTML strings with f-string data injection
- [ ] Use `go.Figure` with explicit `layout` settings for every Plotly chart
- [ ] Test sidebar collapse CSS on target Streamlit version
- [ ] Verify footer stays at bottom with `position: fixed` or `st.empty()` spacer
