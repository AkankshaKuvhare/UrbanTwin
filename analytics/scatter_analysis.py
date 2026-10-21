"""Scatter Analysis Module for UrbanTwin Milestone 8.

Generates bivariate scatter plots with Ordinary Least Squares (OLS) regression lines,
R², Pearson correlation (r), and statistical significance for:
- AQI vs Temperature
- AQI vs Humidity
- AQI vs Wind Speed
- AQI vs PM2.5
- AQI vs PM10
- AQI vs NO2
- Traffic vs AQI (automatically included when traffic observations are present)

Exports:
- `scatter_statistics.csv`
- Multi-panel publication-quality Matplotlib PNG figure
- Interactive Plotly figures for individual pairs and dashboards
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from analytics.correlation import DEFAULT_VARIABLE_LABELS, TRAFFIC_VARIABLES
from config.logging import get_logger

logger = get_logger("urbantwin.analytics.scatter")

# Standard predefined pairs for scatter analysis: (x_col, y_col)
STANDARD_SCATTER_PAIRS: List[Tuple[str, str]] = [
    ("pm25", "aqi"),
    ("pm10", "aqi"),
    ("no2", "aqi"),
    ("temperature_2m", "aqi"),
    ("relative_humidity_2m", "aqi"),
    ("wind_speed_10m", "aqi"),
]

TRAFFIC_SCATTER_PAIRS: List[Tuple[str, str]] = [
    ("traffic_speed", "aqi"),
    ("traffic_congestion", "aqi"),
    ("traffic_travel_time", "aqi"),
]


def get_active_scatter_pairs(df: pd.DataFrame, min_valid: int = 10) -> List[Tuple[str, str]]:
    """Determine all valid scatter pairs, auto-incorporating traffic if available."""
    pairs = []
    # Check standard pairs
    for x_col, y_col in STANDARD_SCATTER_PAIRS:
        if x_col in df.columns and y_col in df.columns:
            valid_count = (df[x_col].notna() & df[y_col].notna()).sum()
            if valid_count >= min_valid:
                pairs.append((x_col, y_col))

    # Check traffic pairs
    for x_col, y_col in TRAFFIC_SCATTER_PAIRS:
        if x_col in df.columns and y_col in df.columns:
            valid_count = (df[x_col].notna() & df[y_col].notna()).sum()
            if valid_count >= min_valid:
                pairs.append((x_col, y_col))

    return pairs


def compute_scatter_statistics(
    df: pd.DataFrame,
    pairs: Optional[List[Tuple[str, str]]] = None,
) -> pd.DataFrame:
    """Compute OLS regression parameters, R², and Pearson r for bivariate pairs.

    Returns:
        DataFrame with columns:
        x_variable, y_variable, x_label, y_label, n_observations,
        pearson_r, r_squared, slope, intercept, p_value, std_err
    """
    active_pairs = pairs or get_active_scatter_pairs(df)
    records = []

    for x_col, y_col in active_pairs:
        if x_col not in df.columns or y_col not in df.columns:
            continue

        x_raw = pd.to_numeric(df[x_col], errors="coerce")
        y_raw = pd.to_numeric(df[y_col], errors="coerce")

        mask = x_raw.notna() & y_raw.notna()
        x = x_raw[mask].values
        y = y_raw[mask].values
        n = len(x)

        if n < 5 or np.std(x) == 0 or np.std(y) == 0:
            continue

        # Linear regression
        res = stats.linregress(x, y)
        r_sq = res.rvalue ** 2

        category = "Pollutant" if x_col in ["pm25", "pm10", "no2", "co", "so2", "o3"] else (
            "Traffic" if x_col in TRAFFIC_VARIABLES else "Weather"
        )

        records.append({
            "x_variable": x_col,
            "y_variable": y_col,
            "x_label": DEFAULT_VARIABLE_LABELS.get(x_col, x_col),
            "y_label": DEFAULT_VARIABLE_LABELS.get(y_col, y_col),
            "category": category,
            "n_observations": int(n),
            "pearson_r": round(float(res.rvalue), 4),
            "r_squared": round(float(r_sq), 4),
            "slope": round(float(res.slope), 4),
            "intercept": round(float(res.intercept), 4),
            "p_value": float(f"{res.pvalue:.2e}") if not np.isnan(res.pvalue) else np.nan,
            "std_err": round(float(res.stderr), 5) if res.stderr else np.nan,
        })

    stats_df = pd.DataFrame(records)
    if not stats_df.empty:
        stats_df = stats_df.sort_values(by="r_squared", ascending=False).reset_index(drop=True)
    return stats_df


def generate_single_scatter_fig(
    df: pd.DataFrame,
    x_col: str,
    y_col: str = "aqi",
    dark_mode: bool = True,
) -> go.Figure:
    """Generate an interactive Plotly scatter plot with OLS trendline, R², and stats."""
    fig = go.Figure()

    if x_col not in df.columns or y_col not in df.columns:
        fig.add_annotation(text=f"Columns {x_col} or {y_col} not available", showarrow=False)
        return fig

    x_raw = pd.to_numeric(df[x_col], errors="coerce")
    y_raw = pd.to_numeric(df[y_col], errors="coerce")
    mask = x_raw.notna() & y_raw.notna()

    sub = df.loc[mask].copy()
    if len(sub) < 5:
        fig.add_annotation(text="Insufficient data points for scatter plot", showarrow=False)
        return fig

    x_vals = pd.to_numeric(sub[x_col]).values
    y_vals = pd.to_numeric(sub[y_col]).values

    reg = stats.linregress(x_vals, y_vals)
    r_sq = reg.rvalue ** 2

    x_label = DEFAULT_VARIABLE_LABELS.get(x_col, x_col)
    y_label = DEFAULT_VARIABLE_LABELS.get(y_col, y_col)

    bg_color = "#0f172a" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#1e293b"
    grid_color = "#334155" if dark_mode else "#e2e8f0"

    # Scatter points
    hover_texts = []
    has_station = "station_id" in sub.columns
    has_date = "observation_datetime" in sub.columns
    for idx, row in sub.iterrows():
        info = f"<b>{x_label}:</b> {row[x_col]:.2f}<br><b>{y_label}:</b> {row[y_col]:.2f}"
        if has_station:
            info += f"<br>Station: {row['station_id']}"
        if has_date:
            info += f"<br>Date: {str(row['observation_datetime'])[:10]}"
        hover_texts.append(info)

    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers",
            name="Observations",
            marker=dict(
                color="#38bdf8",
                size=6,
                opacity=0.6,
                line=dict(width=0.5, color="#0284c7"),
            ),
            hoverinfo="text",
            text=hover_texts,
        )
    )

    # Trendline
    x_sort = np.linspace(np.min(x_vals), np.max(x_vals), 100)
    y_trend = reg.slope * x_sort + reg.intercept

    fig.add_trace(
        go.Scatter(
            x=x_sort,
            y=y_trend,
            mode="lines",
            name=f"OLS Trendline (R² = {r_sq:.3f}, r = {reg.rvalue:.3f})",
            line=dict(color="#f43f5e", width=2.5, dash="dash"),
            hoverinfo="skip",
        )
    )

    title_text = f"<b>{y_label} vs {x_label}</b> | R² = {r_sq:.3f}, r = {reg.rvalue:.3f} (p < {reg.pvalue:.1e})"

    fig.update_layout(
        title=dict(text=title_text, font=dict(color=text_color, size=15)),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color, family="Inter, system-ui, sans-serif"),
        xaxis=dict(title=x_label, gridcolor=grid_color, zerolinecolor=grid_color),
        yaxis=dict(title=y_label, gridcolor=grid_color, zerolinecolor=grid_color),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=text_color),
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        height=480,
    )
    return fig


def save_scatter_grid_figure(
    df: pd.DataFrame,
    output_path: Path,
    pairs: Optional[List[Tuple[str, str]]] = None,
) -> Path:
    """Generate multi-panel publication-quality Matplotlib scatter grid figure."""
    active_pairs = pairs or get_active_scatter_pairs(df)
    if not active_pairs:
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    n_plots = len(active_pairs)
    ncols = 3
    nrows = int(np.ceil(n_plots / ncols))

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(16, 5 * nrows), dpi=300)
    axes = np.array(axes).reshape(-1)

    for i, (x_col, y_col) in enumerate(active_pairs):
        ax = axes[i]
        x_raw = pd.to_numeric(df[x_col], errors="coerce")
        y_raw = pd.to_numeric(df[y_col], errors="coerce")
        mask = x_raw.notna() & y_raw.notna()

        x = x_raw[mask].values
        y = y_raw[mask].values

        if len(x) >= 5:
            reg = stats.linregress(x, y)
            r_sq = reg.rvalue ** 2

            # Scatter points
            ax.scatter(x, y, alpha=0.35, s=18, color="#0284c7", edgecolor="none")

            # Trendline
            x_line = np.linspace(np.min(x), np.max(x), 100)
            y_line = reg.slope * x_line + reg.intercept
            ax.plot(x_line, y_line, color="#e11d48", lw=2, linestyle="--", label=f"R²={r_sq:.3f}, r={reg.rvalue:.3f}")

            ax.set_title(
                f"{DEFAULT_VARIABLE_LABELS.get(y_col, y_col)} vs {DEFAULT_VARIABLE_LABELS.get(x_col, x_col)}",
                fontsize=11,
                fontweight="bold",
            )
            ax.set_xlabel(DEFAULT_VARIABLE_LABELS.get(x_col, x_col), fontsize=9)
            ax.set_ylabel(DEFAULT_VARIABLE_LABELS.get(y_col, y_col), fontsize=9)
            ax.grid(True, linestyle=":", alpha=0.6)
            ax.legend(fontsize=8, loc="upper right")

    # Hide unused subplots
    for j in range(n_plots, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("UrbanTwin Pune: Pollutant & Meteorological Bivariate Regression Analysis", fontsize=15, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def export_scatter_reports(
    df: pd.DataFrame,
    output_dir: Path,
) -> Dict[str, Path]:
    """Compute and export scatter statistics CSV and publication PNG."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stats_df = compute_scatter_statistics(df)

    outputs = {}
    if not stats_df.empty:
        csv_path = output_dir / "scatter_statistics.csv"
        stats_df.to_csv(csv_path, index=False)
        outputs["scatter_statistics_csv"] = csv_path

    png_path = output_dir / "scatter_grid.png"
    save_scatter_grid_figure(df, png_path)
    outputs["scatter_grid_png"] = png_path

    logger.info(
        "Exported scatter analysis reports",
        pairs_analyzed=len(stats_df),
        output_dir=str(output_dir),
    )
    return outputs
