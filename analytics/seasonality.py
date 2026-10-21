"""Seasonality and Cyclic Pattern Analysis for UrbanTwin Milestone 8.

Extracts periodic recurring temporal patterns across:
- Monthly cycles (January - December)
- Weekly cycles (ISO weeks 1 - 52)
- Day-of-week cycles (Monday - Sunday)
- Diurnal / 2D Heatmap profiles (e.g. Month vs Day-of-Week)

Exports:
- `seasonality.csv`
- Publication-quality Matplotlib figures
- Interactive Plotly visualizations for dashboards
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analytics.correlation import DEFAULT_VARIABLE_LABELS, get_active_variables
from analytics.time_series_analysis import prepare_datetime_index
from config.logging import get_logger

logger = get_logger("urbantwin.analytics.seasonality")

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def compute_seasonality_aggregates(
    df: pd.DataFrame,
    target_col: str = "aqi",
) -> Dict[str, pd.DataFrame]:
    """Compute monthly, weekly, and day-of-week aggregations for a target variable.

    Returns:
        Dictionary with keys 'monthly', 'weekly', 'day_of_week', and 'month_dow_pivot'.
    """
    clean_df = prepare_datetime_index(df)
    clean_df["_target"] = pd.to_numeric(clean_df[target_col], errors="coerce")
    clean_df = clean_df.dropna(subset=["_target"])

    clean_df["_month"] = clean_df.index.month
    clean_df["_week"] = clean_df.index.isocalendar().week.astype(int)
    clean_df["_dow"] = clean_df.index.dayofweek

    # Monthly
    m_agg = (
        clean_df.groupby("_month")["_target"]
        .agg(["count", "mean", "std", "median", "min", "max"])
        .reset_index()
    )
    m_agg["month_name"] = m_agg["_month"].apply(lambda m: MONTH_NAMES[m - 1] if 1 <= m <= 12 else str(m))
    m_agg = m_agg.round(2)

    # Weekly
    w_agg = (
        clean_df.groupby("_week")["_target"]
        .agg(["count", "mean", "std", "median", "min", "max"])
        .reset_index()
        .round(2)
    )

    # Day of week
    dow_agg = (
        clean_df.groupby("_dow")["_target"]
        .agg(["count", "mean", "std", "median", "min", "max"])
        .reset_index()
    )
    dow_agg["day_name"] = dow_agg["_dow"].apply(lambda d: DOW_NAMES[d] if 0 <= d <= 6 else str(d))
    dow_agg = dow_agg.round(2)

    # Month vs Day-of-week pivot
    pivot = clean_df.pivot_table(
        index="_month",
        columns="_dow",
        values="_target",
        aggfunc="mean",
    ).round(2)
    pivot.index = [MONTH_NAMES[m - 1] for m in pivot.index]
    pivot.columns = [DOW_NAMES[c] for c in pivot.columns]

    return {
        "monthly": m_agg,
        "weekly": w_agg,
        "day_of_week": dow_agg,
        "month_dow_pivot": pivot,
    }


def compute_all_variables_seasonality(
    df: pd.DataFrame,
    variables: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute monthly mean profiles for all active variables to export seasonality.csv."""
    clean_df = prepare_datetime_index(df)
    target_vars = variables or get_active_variables(clean_df)
    numeric_df = clean_df[target_vars].apply(pd.to_numeric, errors="coerce")
    numeric_df["_month"] = clean_df.index.month

    monthly_means = numeric_df.groupby("_month").mean().round(2).reset_index()
    monthly_means["month_name"] = monthly_means["_month"].apply(
        lambda m: MONTH_NAMES[m - 1] if 1 <= m <= 12 else str(m)
    )

    # Reorder columns
    cols = ["_month", "month_name"] + [c for c in monthly_means.columns if c not in ["_month", "month_name"]]
    return monthly_means[cols]


def generate_seasonality_figures(
    df: pd.DataFrame,
    target_col: str = "aqi",
    dark_mode: bool = True,
) -> Dict[str, go.Figure]:
    """Generate interactive Plotly figures for monthly, weekly, dow, and heatmap."""
    aggs = compute_seasonality_aggregates(df, target_col=target_col)
    label = DEFAULT_VARIABLE_LABELS.get(target_col, target_col)

    bg_color = "#0f172a" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#1e293b"
    grid_color = "#334155" if dark_mode else "#e2e8f0"

    # 1. Monthly Cycle Bar / Line
    m_df = aggs["monthly"]
    fig_month = go.Figure()
    fig_month.add_trace(
        go.Bar(
            x=m_df["month_name"],
            y=m_df["mean"],
            name=f"Mean {label}",
            marker=dict(color="#f59e0b"),
            error_y=dict(type="data", array=m_df["std"], visible=True, color="#94a3b8"),
        )
    )
    fig_month.update_layout(
        title=dict(text=f"<b>Monthly Seasonal Profile: {label}</b> (Mean ± 1 SD)", font=dict(color=text_color, size=15)),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color, family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Month", gridcolor=grid_color),
        yaxis=dict(title=f"Mean {label}", gridcolor=grid_color),
        height=400,
        margin=dict(l=60, r=40, t=60, b=50),
    )

    # 2. Day-of-week Cycle
    dow_df = aggs["day_of_week"]
    fig_dow = go.Figure()
    fig_dow.add_trace(
        go.Scatter(
            x=dow_df["day_name"],
            y=dow_df["mean"],
            mode="lines+markers",
            name=f"Mean {label}",
            line=dict(color="#38bdf8", width=3),
            marker=dict(size=10, color="#0284c7"),
        )
    )
    fig_dow.update_layout(
        title=dict(text=f"<b>Day-of-Week Profile: {label}</b>", font=dict(color=text_color, size=15)),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color, family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Day", gridcolor=grid_color),
        yaxis=dict(title=f"Mean {label}", gridcolor=grid_color),
        height=400,
        margin=dict(l=60, r=40, t=60, b=50),
    )

    # 3. Month vs Day-of-Week Heatmap
    pivot = aggs["month_dow_pivot"]
    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale="Viridis",
            colorbar=dict(title=label),
            hovertemplate="Month: %{y}<br>Day: %{x}<br>Mean " + label + ": %{z:.1f}<extra></extra>",
        )
    )
    fig_heatmap.update_layout(
        title=dict(text=f"<b>Seasonal Matrix: {label} by Month and Day-of-Week</b>", font=dict(color=text_color, size=15)),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color, family="Inter, system-ui, sans-serif"),
        xaxis=dict(gridcolor=grid_color),
        yaxis=dict(autorange="reversed", gridcolor=grid_color),
        height=450,
        margin=dict(l=60, r=40, t=60, b=50),
    )

    return {
        "monthly": fig_month,
        "day_of_week": fig_dow,
        "heatmap": fig_heatmap,
    }


def save_seasonality_figure(
    df: pd.DataFrame,
    output_path: Path,
    target_col: str = "aqi",
) -> Path:
    """Save publication-quality 3-panel Matplotlib seasonality overview."""
    aggs = compute_seasonality_aggregates(df, target_col=target_col)
    m_df = aggs["monthly"]
    dow_df = aggs["day_of_week"]
    pivot = aggs["month_dow_pivot"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)

    # 1. Monthly Bar
    axes[0].bar(m_df["month_name"], m_df["mean"], yerr=m_df["std"], color="#f59e0b", capsize=3, alpha=0.85)
    axes[0].set_title("Monthly Seasonality (Mean ± SD)", fontsize=11, fontweight="bold")
    axes[0].set_ylabel(DEFAULT_VARIABLE_LABELS.get(target_col, target_col))
    axes[0].grid(True, linestyle=":", alpha=0.6)

    # 2. Day of Week
    axes[1].plot(dow_df["day_name"], dow_df["mean"], marker="o", color="#0284c7", lw=2)
    axes[1].set_title("Day-of-Week Pattern", fontsize=11, fontweight="bold")
    axes[1].grid(True, linestyle=":", alpha=0.6)

    # 3. Heatmap
    cax = axes[2].matshow(pivot.values, cmap="YlOrRd")
    fig.colorbar(cax, ax=axes[2], fraction=0.046, pad=0.04)
    axes[2].set_xticks(range(len(pivot.columns)))
    axes[2].set_xticklabels(list(pivot.columns))
    axes[2].set_yticks(range(len(pivot.index)))
    axes[2].set_yticklabels(list(pivot.index))
    axes[2].set_title("Month x Day Heatmap", fontsize=11, fontweight="bold", pad=20)

    fig.suptitle("UrbanTwin Pune: Comprehensive Air Quality Seasonality Analysis", fontsize=14, fontweight="bold", y=1.03)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def export_seasonality_reports(
    df: pd.DataFrame,
    output_dir: Path,
    target_col: str = "aqi",
) -> Dict[str, Path]:
    """Export seasonality CSV and publication figure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    all_season_df = compute_all_variables_seasonality(df)

    outputs = {}
    csv_path = output_dir / "seasonality.csv"
    all_season_df.to_csv(csv_path, index=False)
    outputs["seasonality_csv"] = csv_path

    png_path = output_dir / "seasonality_overview.png"
    save_seasonality_figure(df, png_path, target_col=target_col)
    outputs["seasonality_png"] = png_path

    logger.info("Exported seasonality reports", output_dir=str(output_dir))
    return outputs
