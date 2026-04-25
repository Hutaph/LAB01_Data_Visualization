import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from typing import Tuple, List

def get_shap_explanation(model, X_processed: pd.DataFrame):
    """
    CUSTOM REPLACEMENT FOR SHAP:
    Calculates feature contributions manually by perturbing each feature.
    Returns: (contributions, base_value, feature_names)
    """
    try:
        # 1. Base prediction (using zeros as baseline for scaled/normalized data)
        # In a scaled environment, 0 is usually the mean/median.
        X_base = X_processed.copy()
        for col in X_base.columns:
            X_base[col] = 0.0
        
        base_val = model.predict(X_base)[0]
        final_val = model.predict(X_processed)[0]
        
        # 2. Calculate contributions one by one (OAT - One At Time)
        contributions = []
        feature_names = X_processed.columns.tolist()
        
        for col in feature_names:
            X_temp = X_base.copy()
            X_temp[col] = X_processed[col].values[0]
            pred_temp = model.predict(X_temp)[0]
            
            # Simple contribution
            contrib = pred_temp - base_val
            contributions.append(contrib)
            
        # 3. Optional: Rescale contributions so sum(contrib) + base ~= final
        # This makes the waterfall plot visually accurate to the final output.
        sum_contrib = sum(contributions)
        total_diff = final_val - base_val
        
        if abs(sum_contrib) > 1e-9:
            ratio = total_diff / sum_contrib
            contributions = [c * ratio for c in contributions]
        
        return np.array(contributions), base_val, feature_names
    except Exception as e:
        st.warning(f"Lỗi khi tính toán giải thích: {e}")
        return None, None, None

def aggregate_category_shap(shap_values: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, List[str]]:
    """
    Aggregates one_hot encoded category contributions.
    """
    new_shap = []
    new_names = []
    
    cat_sum = 0
    found_cat = False
    
    for val, name in zip(shap_values, feature_names):
        if name.startswith("cat_") or name.startswith("cat__"):
            cat_sum += val
            found_cat = True
        else:
            new_shap.append(val)
            new_names.append(name)
            
    if found_cat:
        new_shap.append(cat_sum)
        new_names.append("Danh mục")
        
    return np.array(new_shap), new_names

def plot_shap_waterfall(shap_values, base_value, feature_names, max_display=10):
    """
    Custom Waterfall plot using Plotly (Premium Visuals).
    """
    # 1. Clean feature names
    nice_names = []
    mapping = {
        "rating": "Điểm đánh giá",
        "price": "Giá bán",
        "reviews": "Số lượt đánh giá",
        "number_of_offers": "Số nhà bán",
        "delivery_fee": "Phí vận chuyển",
        "is_prime": "Có Prime",
        "is_amazon_choice": "Amazon Choice",
        "has_variations": "Có biến thể",
        "original_price": "Giá gốc",
        "lowest_offer_price": "Giá thấp nhất",
        "is_climate_friendly": "Thân thiện MT",
        "Danh mục": "Danh mục sản phẩm"
    }
    
    for n in feature_names:
        name = n.replace("num__", "").replace("bools__", "").replace("_log_clipped", "")
        nice_names.append(mapping.get(name, name))

    # 2. Prepare data for Waterfall
    df_plot = pd.DataFrame({
        "Feature": nice_names,
        "Contribution": shap_values
    })
    
    # Sort by absolute impact
    df_plot["abs_impact"] = df_plot["Contribution"].abs()
    df_plot = df_plot.sort_values("abs_impact", ascending=False).head(max_display)
    
    # Calculate Waterfall steps
    measures = ["relative"] * len(df_plot)
    y_vals = df_plot["Contribution"].tolist()
    x_labels = df_plot["Feature"].tolist()
    
    # Add Base Value and Total
    final_val = base_value + sum(shap_values)
    
    # Reconstruct Waterfall for plot
    # Initial base
    # Then each contribution
    # Then total
    
    fig = go.Figure(go.Waterfall(
        name="Giải thích", orientation="v",
        measure=["absolute"] + ["relative"] * len(y_vals) + ["total"],
        x=["TB Thị trường"] + x_labels + ["Dự đoán cuối"],
        textposition="outside",
        text=[f"{base_value:+.2f}"] + [f"{v:+.2f}" for v in y_vals] + [f"{final_val:.2f}"],
        y=[base_value] + y_vals + [0], # Total is calculated automatically
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#EF4444"}}, # Red for positive impact
        decreasing={"marker": {"color": "#3B82F6"}}, # Blue for negative impact
        totals={"marker": {"color": "#F59E0B"}}
    ))

    fig.update_layout(
        title="Phân tích tác động các yếu tố (Waterfall)",
        showlegend=False,
        height=500,
        margin=dict(t=50, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig
