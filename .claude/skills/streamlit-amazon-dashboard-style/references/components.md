# Component Code Reference — Amazon Dashboard

All examples assume Plotly (`pip install plotly`) and Streamlit >= 1.28.

---

## 1. KPI Card {#kpi-card}

```python
def kpi_card(label: str, value: str, sublabel: str = "") -> str:
    """Returns HTML string for one KPI card."""
    sub_html = f'<div class="kpi-sublabel">{sublabel}</div>' if sublabel else ""
    return f"""
    <div class="amazon-kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
    </div>
    """

# Usage
cols = st.columns(5)
kpi_data = [
    ("Total Products",  "2,847",  "across all categories"),
    ("Avg Price",       "$142",   "median: $89"),
    ("Avg Rating",      "4.2 ★",  "from 12,400 reviews"),
    ("Amazon's Choice", "634",    "22.3% of catalog"),
    ("Climate Friendly","389",    "13.7% of catalog"),
]

for col, (label, value, sub) in zip(cols, kpi_data):
    with col:
        st.markdown(kpi_card(label, value, sub), unsafe_allow_html=True)
```

---

## 2. Bar Chart — Top 10 Categories {#bar-chart}

```python
import plotly.graph_objects as go

def bar_chart_top_categories(df_agg):
    """
    df_agg: DataFrame with columns ['category', 'count']
    sorted descending by count, top 10 rows.
    """
    top10 = df_agg.nlargest(10, 'count')

    fig = go.Figure(go.Bar(
        x=top10['count'],
        y=top10['category'],
        orientation='h',
        marker_color='#FF9900',
        text=top10['count'],
        textposition='outside',
        textfont=dict(size=11, color='#555555'),
    ))

    fig.update_layout(
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        font_family="Inter, system-ui, sans-serif",
        font_color='#1A1A1A',
        margin=dict(l=160, r=40, t=20, b=20),
        height=380,
        xaxis=dict(
            showgrid=True,
            gridcolor='#F0F0F0',
            showline=False,
            zeroline=False,
            tickfont=dict(color='#555555', size=11),
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color='#555555', size=12),
            autorange='reversed',
        ),
        bargap=0.35,
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
```

---

## 3. Donut Chart — Flag/Label Distribution {#donut-chart}

```python
def donut_chart_flags(labels: list, values: list):
    """
    labels: e.g. ["Climate Friendly", "Has Variations", "Amazon's Choice"]
    values: corresponding counts
    """
    colors = ['#FF9900', '#B85C00', '#E8C99A', '#FFD580', '#CC7A00']

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.52,
        marker=dict(colors=colors[:len(labels)], line=dict(color='#FFFFFF', width=2)),
        textinfo='percent',
        textfont=dict(size=12, color='#FFFFFF'),
        hovertemplate='%{label}<br>Count: %{value}<br>Share: %{percent}<extra></extra>',
    ))

    fig.update_layout(
        paper_bgcolor='#FFFFFF',
        font_family="Inter, system-ui, sans-serif",
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom', y=-0.2,
            xanchor='center', x=0.5,
            font=dict(size=11, color='#555555'),
        ),
        margin=dict(l=20, r=20, t=10, b=60),
        height=320,
        annotations=[dict(
            text='Flags',
            x=0.5, y=0.5,
            font=dict(size=14, color='#1A1A1A', family='Inter'),
            showarrow=False,
        )],
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
```

---

## 4. Combo Chart — Avg Price + Sales Volume {#combo-chart}

```python
def combo_chart_price_sales(df_monthly):
    """
    df_monthly: DataFrame with ['month', 'avg_price', 'sales_count']
    """
    fig = go.Figure()

    # Bar: Average Price
    fig.add_trace(go.Bar(
        x=df_monthly['month'],
        y=df_monthly['avg_price'],
        name='Avg Price ($)',
        marker_color='#FF9900',
        yaxis='y1',
        hovertemplate='Month: %{x}<br>Avg Price: $%{y:.2f}<extra></extra>',
    ))

    # Line: Sales Count
    fig.add_trace(go.Scatter(
        x=df_monthly['month'],
        y=df_monthly['sales_count'],
        name='Sales Volume',
        mode='lines+markers',
        line=dict(color='#1A1A1A', width=2),
        marker=dict(symbol='circle-open', size=8, color='#1A1A1A', line=dict(width=2)),
        yaxis='y2',
        hovertemplate='Month: %{x}<br>Sales: %{y:,}<extra></extra>',
    ))

    fig.update_layout(
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        font_family="Inter, system-ui, sans-serif",
        height=360,
        margin=dict(l=60, r=60, t=20, b=40),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color='#555555', size=11),
        ),
        yaxis=dict(
            title='Avg Price ($)',
            titlefont=dict(color='#FF9900', size=11),
            tickfont=dict(color='#FF9900', size=11),
            showgrid=True,
            gridcolor='#F0F0F0',
        ),
        yaxis2=dict(
            title='Sales Volume',
            titlefont=dict(color='#1A1A1A', size=11),
            tickfont=dict(color='#1A1A1A', size=11),
            overlaying='y',
            side='right',
            showgrid=False,
        ),
        bargap=0.3,
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
```

---

## 5. Top 5 Table {#top-5-table}

### Option A: Plotly Table (interactive)

```python
def top5_table_plotly(df_top5):
    """
    df_top5: DataFrame with columns to display.
    """
    headers = list(df_top5.columns)
    cell_values = [df_top5[col].tolist() for col in headers]

    n = len(df_top5)
    row_colors = ['#FFFFFF' if i % 2 == 0 else '#FFF5E6' for i in range(n)]

    fig = go.Figure(go.Table(
        header=dict(
            values=[f'<b>{h}</b>' for h in headers],
            fill_color='#FF9900',
            font=dict(color='white', size=12, family='Inter'),
            align='left',
            height=36,
        ),
        cells=dict(
            values=cell_values,
            fill_color=[row_colors] * len(headers),
            font=dict(color='#1A1A1A', size=12, family='Inter'),
            align='left',
            height=32,
        ),
    ))

    fig.update_layout(
        paper_bgcolor='#FFFFFF',
        margin=dict(l=0, r=0, t=0, b=0),
        height=36 + 32 * n + 20,
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
```

### Option B: HTML Table (static, custom hover)

```python
def top5_table_html(df_top5):
    rows = ""
    for i, row in df_top5.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row)
        rows += f"<tr>{cells}</tr>"

    headers = "".join(f"<th>{c}</th>" for c in df_top5.columns)

    html = f"""
    <table class="amazon-table">
        <thead><tr>{headers}</tr></thead>
        <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(html, unsafe_allow_html=True)
```

---

## 6. Filter Slider {#filter-slider}

```python
# In filter bar section
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

with col1:
    category = st.selectbox(
        "Category",
        options=["All"] + sorted(df['category'].unique().tolist()),
        index=0,
    )

with col2:
    price_min = int(df['price'].min())
    price_max = int(df['price'].max())
    price_range = st.slider(
        "Price Range ($)",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, price_max),
        step=10,
        format="$%d",
    )

with col3:
    amazons_choice = st.toggle("Amazon's Choice", value=False)

with col4:
    climate_friendly = st.toggle("Climate Friendly", value=False)

# Apply filters
mask = pd.Series([True] * len(df))
if category != "All":
    mask &= df['category'] == category
mask &= df['price'].between(*price_range)
if amazons_choice:
    mask &= df['is_amazons_choice'] == True
if climate_friendly:
    mask &= df['is_climate_friendly'] == True

df_filtered = df[mask]
```

---

## 7. Toggle Switch {#toggle-switch}

Streamlit's `st.toggle` automatically respects `config.toml` `primaryColor`. To ensure the orange color:

```python
# config.toml must have: primaryColor = "#FF9900"
# Then:
value = st.toggle("Amazon's Choice Only", value=False, key="toggle_ac")

# If you need custom label styling:
st.markdown("""
<style>
[data-testid="stToggle"] label {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: #1A1A1A;
}
</style>
""", unsafe_allow_html=True)
```

---

## 8. Sidebar Navigation {#sidebar-nav}

```python
import streamlit as st

# Inject sidebar CSS (from css-tokens.md SIDEBAR_CSS)
st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

with st.sidebar:
    # Logo placeholder
    st.markdown('<div style="text-align:center;padding:12px 0;font-size:28px;">🛒</div>',
                unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#F0E0CC;margin:4px 0;">', unsafe_allow_html=True)

    # Navigation buttons (icon only at 70px width)
    nav_items = [
        ("📊", "Overview"),
        ("📦", "Products"),
        ("💰", "Pricing"),
        ("⭐", "Ratings"),
        ("🌿", "Sustainability"),
    ]

    selected = st.session_state.get("nav_page", "Overview")

    for icon, label in nav_items:
        btn_style = "background:#FFF5E6;color:#FF9900;" if selected == label else ""
        if st.button(icon, key=f"nav_{label}", help=label):
            st.session_state["nav_page"] = label
            st.rerun()
```

---

## 9. Header Banner {#header-banner}

```python
def render_header(title: str, subtitle: str = "E-Commerce Analytics"):
    # Inject CSS once
    st.markdown(HEADER_CSS, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="amazon-header">
        <div class="header-logo">🛒</div>
        <div>
            <div class="header-title">{title}</div>
            <div class="header-subtitle">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Usage at top of app.py
render_header("Amazon Product Analytics", "Dashboard · Spring 2025 Dataset")
```

---

## 10. Footer Bar {#footer-bar}

```python
def render_footer(university: str, student_name: str, course: str):
    st.markdown(FOOTER_CSS, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="amazon-footer">
        <div>© 2025 Amazon Product Dashboard</div>
        <div>
            <span class="footer-tag">{university}</span>
            <span class="footer-tag">{student_name}</span>
            <span class="footer-tag">{course}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Usage at bottom of app.py
render_footer("UEH University", "Nguyen Van A", "Data Visualization - Lab 1")
```

---

## Full App Bootstrap Template

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Amazon Product Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1. Inject all global CSS (combine all CSS blocks from css-tokens.md)
st.markdown(GLOBAL_CSS + SIDEBAR_CSS + KPI_CARD_CSS + FILTER_BAR_CSS, unsafe_allow_html=True)

# 2. Header
render_header("Amazon Product Analytics")

# 3. Sidebar nav
with st.sidebar:
    render_sidebar_nav()

# 4. Load data
@st.cache_data
def load_data():
    return pd.read_csv("data/amazon_products.csv")

df = load_data()

# 5. Filter bar
df_filtered = render_filter_bar(df)

# 6. KPI row
render_kpi_row(df_filtered)

# 7. Charts
col_left, col_right = st.columns([3, 2])
with col_left:
    bar_chart_top_categories(df_filtered.groupby('category').size().reset_index(name='count'))
with col_right:
    donut_chart_flags(...)

# 8. Footer
render_footer("UEH University", "Nguyen Van A", "Data Visualization - Lab 1")
```
