# CSS Tokens & Snippets — Amazon Dashboard

## CSS Custom Properties (Design Tokens)

```css
:root {
  /* Brand Colors */
  --amazon-primary:    #FF9900;
  --amazon-secondary:  #B85C00;
  --amazon-accent:     #E8C99A;

  /* Backgrounds */
  --bg-page:           #FFF8F0;
  --bg-card:           #FFFFFF;
  --bg-header:         #FFE0B2;
  --bg-header-end:     #FFF8F0;
  --bg-table-alt:      #FFF5E6;
  --bg-table-hover:    #FFE0B2;

  /* Text */
  --text-main:         #1A1A1A;
  --text-sub:          #666666;
  --text-muted:        #999999;
  --text-on-primary:   #FFFFFF;

  /* Component */
  --card-radius:       12px;
  --card-shadow:       0 2px 8px rgba(0, 0, 0, 0.08);
  --card-border-left:  4px solid #FF9900;
  --card-padding:      20px 24px;

  /* Typography */
  --font-family:       'Inter', system-ui, -apple-system, sans-serif;
  --font-title:        700 30px / 1.2 var(--font-family);
  --font-kpi-label:    600 11px / 1 var(--font-family);
  --font-kpi-value:    700 38px / 1 var(--font-family);
  --font-sub-label:    400 12px / 1.4 var(--font-family);

  /* Spacing */
  --space-xs:          4px;
  --space-sm:          8px;
  --space-md:          16px;
  --space-lg:          24px;
  --space-xl:          32px;
}
```

---

## Global Streamlit Reset

Paste this as the first `st.markdown()` call in `app.py`:

```python
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Page background */
[data-testid="stAppViewContainer"] {
    background-color: #FFF8F0 !important;
    font-family: 'Inter', system-ui, sans-serif;
}

/* Remove default Streamlit top padding */
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 0 !important;
    max-width: 100% !important;
}

/* Hide Streamlit hamburger menu + footer */
#MainMenu, footer, header { visibility: hidden; }

/* Metric widget override */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border-left: 4px solid #FF9900;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #666666 !important;
}
[data-testid="stMetricValue"] {
    font-size: 36px !important;
    font-weight: 700 !important;
    color: #1A1A1A !important;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
    color: #999999 !important;
}
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
```

---

## Sidebar CSS

```python
SIDEBAR_CSS = """
<style>
/* Narrow icon-only sidebar */
[data-testid="stSidebar"] {
    min-width: 72px !important;
    max-width: 72px !important;
    background: #FFFFFF !important;
    border-right: 1px solid #F0E0CC;
}

/* Hide sidebar text labels, keep icons */
[data-testid="stSidebar"] .css-pkbazv,
[data-testid="stSidebar"] span {
    display: none !important;
}

/* Nav icon button style */
[data-testid="stSidebar"] button {
    width: 48px !important;
    height: 48px !important;
    border-radius: 10px !important;
    margin: 4px auto !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    border: none !important;
    background: transparent !important;
    color: #666666 !important;
    font-size: 20px !important;
}

/* Active nav item highlight */
[data-testid="stSidebar"] button.active,
[data-testid="stSidebar"] button:hover {
    background: #FFF5E6 !important;
    color: #FF9900 !important;
}
</style>
"""
```

---

## KPI Card CSS

```python
KPI_CARD_CSS = """
<style>
.amazon-kpi-card {
    background: #FFFFFF;
    border-left: 4px solid #FF9900;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    min-height: 120px;
    position: relative;
}
.amazon-kpi-card .kpi-label {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #666666;
    margin-bottom: 8px;
}
.amazon-kpi-card .kpi-value {
    font-family: 'Inter', sans-serif;
    font-size: 38px;
    font-weight: 700;
    color: #1A1A1A;
    line-height: 1;
    margin-bottom: 6px;
}
.amazon-kpi-card .kpi-sublabel {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-style: italic;
    color: #999999;
}
</style>
"""
```

---

## Header Banner CSS

```python
HEADER_CSS = """
<style>
.amazon-header {
    background: linear-gradient(135deg, #FFE0B2 0%, #FFF8F0 100%);
    padding: 20px 32px;
    border-radius: 0 0 16px 16px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    border-bottom: 2px solid #FF9900;
}
.amazon-header .header-logo {
    font-size: 36px;
}
.amazon-header .header-title {
    font-family: 'Inter', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #1A1A1A;
    line-height: 1.1;
}
.amazon-header .header-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #666666;
    margin-top: 2px;
}
</style>
"""
```

---

## Table CSS

```python
TABLE_CSS = """
<style>
.amazon-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.amazon-table thead tr {
    background: #FF9900;
    color: #FFFFFF;
}
.amazon-table thead th {
    padding: 12px 16px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    text-align: left;
}
.amazon-table tbody tr:nth-child(even) {
    background: #FFF5E6;
}
.amazon-table tbody tr:nth-child(odd) {
    background: #FFFFFF;
}
.amazon-table tbody tr:hover {
    background: #FFE0B2 !important;
    transition: background 0.15s ease;
}
.amazon-table tbody td {
    padding: 11px 16px;
    color: #1A1A1A;
    border-bottom: 1px solid #F5E8D8;
}
</style>
"""
```

---

## Filter Bar CSS

```python
FILTER_BAR_CSS = """
<style>
.amazon-filter-bar {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 16px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
}

/* Slider thumb color */
[data-testid="stSlider"] .rc-slider-handle {
    border-color: #FF9900 !important;
    background: #FF9900 !important;
}
[data-testid="stSlider"] .rc-slider-track {
    background: #FF9900 !important;
}

/* Toggle switch color */
[data-testid="stToggle"] input:checked + div {
    background-color: #FF9900 !important;
}

/* Selectbox focus ring */
[data-testid="stSelectbox"] > div:focus-within {
    border-color: #FF9900 !important;
    box-shadow: 0 0 0 2px rgba(255,153,0,0.2) !important;
}
</style>
"""
```

---

## Footer Bar CSS

```python
FOOTER_CSS = """
<style>
.amazon-footer {
    background: #FF9900;
    color: #FFFFFF;
    padding: 12px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    border-radius: 12px 12px 0 0;
    margin-top: 32px;
}
.amazon-footer .footer-tag {
    background: rgba(255,255,255,0.25);
    color: #FFFFFF;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin-left: 8px;
}
</style>
"""
```

---

## Streamlit config.toml

Place in `.streamlit/config.toml` to align native widgets with the design system:

```toml
[theme]
base = "light"
primaryColor = "#FF9900"
backgroundColor = "#FFF8F0"
secondaryBackgroundColor = "#FFE0B2"
textColor = "#1A1A1A"
font = "sans serif"
```
