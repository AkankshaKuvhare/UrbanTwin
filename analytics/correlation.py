"""Correlation Analysis Module for UrbanTwin Milestone 8.

Computes Pearson, Spearman, and Kendall rank correlation matrices for:
- Air Quality Indicators: AQI, PM2.5, PM10, NO2, CO, SO2, O3
- Meteorological Variables: Temperature, Relative Humidity, Wind Speed,
  Wind Direction, Surface Pressure, Precipitation, Boundary Layer Height
- Traffic Variables: Speed, Congestion, Travel Time, Confidence (automatically
  incorporated once valid observations exist)

Generates:
- Full pairwise correlation matrices (CSV, JSON)
- Correlation summary against target variable (AQI)
- Interactive Plotly heatmaps and publication-quality PNG figures
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from config.logging import get_logger

logger = get_logger("urbantwin.analytics.correlation")

# Standard core variable lists
POLLUTANT_VARIABLES = [
    "aqi", "pm25", "pm10", "no2", "co", "so2", "o3",
]

WEATHER_VARIABLES = [
    "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
    "wind_direction_10m", "surface_pressure", "precipitation",
    "boundary_layer_height",
]

TRAFFIC_VARIABLES = [
    "traffic_speed", "traffic_congestion", "traffic_travel_time", "traffic_confidence",
]

DEFAULT_VARIABLE_LABELS: Dict[str, str] = {
    "aqi": "AQI",
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no2": "NO2",
    "co": "CO",
    "so2": "SO2",
    "o3": "O3",
    "temperature_2m": "Temperature (2m)",
    "relative_humidity_2m": "Rel. Humidity",
    "wind_speed_10m": "Wind Speed (10m)",
    "wind_direction_10m": "Wind Direction",
    "surface_pressure": "Surface Pressure",
    "precipitation": "Precipitation",
    "boundary_layer_height": "Boundary Layer Ht",
    "traffic_speed": "Traffic Speed",
    "traffic_congestion": "Traffic Congestion",
    "traffic_travel_time": "Traffic Travel Time",
    "traffic_confidence": "Traffic Confidence",
}


def get_active_variables(df: pd.DataFrame, min_valid: int = 5) -> List[str]:
    """Identify columns that exist in DataFrame and have at least min_valid non-null rows.
    
    Automatically incorporates traffic variables once non-null data exists.
    """
    candidate_cols = POLLUTANT_VARIABLES + WEATHER_VARIABLES + TRAFFIC_VARIABLES
    active = []
    for col in candidate_cols:
        if col in df.columns:
            # Check numeric and non-null count
            valid_count = df[col].dropna().shape[0]
            if valid_count >= min_valid:
                # Also ensure there is some variance (std > 0)
                try:
                    s = pd.to_numeric(df[col], errors="coerce").dropna()
                    if len(s) >= min_valid and s.std() > 0:
                        active.append(col)
                except Exception:
                    pass
    return active


def compute_correlation_matrices(
    df: pd.DataFrame,
    variables: Optional[List[str]] = None,
) -> Dict[str, pd.DataFrame]:
    """Compute Pearson, Spearman, and Kendall correlation matrices.

    Args:
        df: Input DataFrame containing pollutant, weather, and optional traffic columns.
        variables: Optional explicit list of columns. If None, active variables are detected.

    Returns:
        Dictionary mapping method ('pearson', 'spearman', 'kendall') to its correlation DataFrame.
    """
    target_vars = variables or get_active_variables(df)
    if not target_vars:
        return {"pearson": pd.DataFrame(), "spearman": pd.DataFrame(), "kendall": pd.DataFrame()}

    sub_df = df[target_vars].apply(pd.to_numeric, errors="coerce")

    matrices = {}
    for method in ["pearson", "spearman", "kendall"]:
        corr = sub_df.corr(method=method).round(4)
        matrices[method] = corr

    return matrices


def compute_correlation_summary(
    df: pd.DataFrame,
    target: str = "aqi",
    variables: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute detailed correlation statistics between target and all other active variables.

    Includes Pearson r, p-value, Spearman rho, and Kendall tau.
    """
    target_vars = variables or get_active_variables(df)
    if target not in df.columns or target not in target_vars:
        return pd.DataFrame()

    other_vars = [v for v in target_vars if v != target]
    y = pd.to_numeric(df[target], errors="coerce")

    records = []
    for var in other_vars:
        x = pd.to_numeric(df[var], errors="coerce")
        # Align and drop pairwise NaNs
        valid_mask = x.notna() & y.notna()
        x_clean = x[valid_mask]
        y_clean = y[valid_mask]
        n_obs = len(x_clean)

        if n_obs < 3 or x_clean.std() == 0 or y_clean.std() == 0:
            continue

        try:
            p_r, p_val = stats.pearsonr(x_clean, y_clean)
        except Exception:
            p_r, p_val = np.nan, np.nan

        try:
            s_rho, s_val = stats.spearmanr(x_clean, y_clean)
        except Exception:
            s_rho, s_val = np.nan, np.nan

        try:
            k_tau, k_val = stats.kendalltau(x_clean, y_clean)
        except Exception:
            k_tau, k_val = np.nan, np.nan

        category = "Pollutant" if var in POLLUTANT_VARIABLES else (
            "Traffic" if var in TRAFFIC_VARIABLES else "Weather"
        )

        strength = "Strong" if abs(p_r) >= 0.5 else ("Moderate" if abs(p_r) >= 0.3 else "Weak")
        direction = "Positive" if p_r > 0 else "Negative"

        records.append({
            "variable": var,
            "label": DEFAULT_VARIABLE_LABELS.get(var, var),
            "category": category,
            "observations": n_obs,
            "pearson_r": round(float(p_r), 4),
            "pearson_p_value": float(f"{p_val:.2e}") if not np.isnan(p_val) else np.nan,
            "spearman_rho": round(float(s_rho), 4) if not np.isnan(s_rho) else np.nan,
            "kendall_tau": round(float(k_tau), 4) if not np.isnan(k_tau) else np.nan,
            "relationship_strength": strength,
            "direction": direction,
            "abs_pearson_r": round(abs(float(p_r)), 4),
        })

    summary_df = pd.DataFrame(records)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(by="abs_pearson_r", ascending=False).reset_index(drop=True)
    return summary_df


def generate_correlation_heatmap_fig(
    corr_df: pd.DataFrame,
    title: str = "Variable Correlation Matrix",
    method: str = "pearson",
    dark_mode: bool = True,
) -> go.Figure:
    """Generate an interactive Plotly heatmap for correlation matrix."""
    if corr_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No active variables found for correlation", showarrow=False)
        return fig

    labels = [DEFAULT_VARIABLE_LABELS.get(col, col) for col in corr_df.columns]

    z_vals = corr_df.values
    text_vals = [[f"{val:.2f}" if not np.isnan(val) else "" for val in row] for row in z_vals]

    bg_color = "#0f172a" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#1e293b"
    grid_color = "#334155" if dark_mode else "#e2e8f0"

    fig = go.Figure(
        data=go.Heatmap(
            z=z_vals,
            x=labels,
            y=labels,
            text=text_vals,
            texttemplate="%{text}",
            textfont={"size": 11, "color": "white"},
            colorscale="RdBu_r",
            zmin=-1.0,
            zmax=1.0,
            colorbar=dict(
                title=dict(text=f"{method.capitalize()} r", side="top"),
                tickvals=[-1.0, -0.5, 0.0, 0.5, 1.0],
                ticktext=["-1.0", "-0.5", "0.0", "+0.5", "+1.0"],
            ),
            hoverongaps=False,
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text=f"<b>{title}</b> ({method.capitalize()})", font=dict(color=text_color, size=16)),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color, family="Inter, system-ui, sans-serif"),
        xaxis=dict(tickangle=-45, showgrid=False),
        yaxis=dict(autorange="reversed", showgrid=False),
        margin=dict(l=80, r=40, t=60, b=100),
        height=620,
    )
    return fig


def save_correlation_figure(
    corr_df: pd.DataFrame,
    output_path: Path,
    title: str = "Pearson Correlation Matrix",
) -> Path:
    """Save publication-quality PNG correlation heatmap using Matplotlib."""
    if corr_df.empty:
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels = [DEFAULT_VARIABLE_LABELS.get(col, col) for col in corr_df.columns]

    fig, ax = plt.subplots(figsize=(11, 9), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    cax = ax.matshow(corr_df.values, cmap="coolwarm", vmin=-1, vmax=1)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Correlation Coefficient (r)")

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="left", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    # Annotate numeric values in cells
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = corr_df.iloc[i, j]
            if not np.isnan(val):
                color = "white" if abs(val) > 0.55 else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontsize=8)

    ax.set_title(title, pad=30, fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def export_correlation_reports(
    df: pd.DataFrame,
    output_dir: Path,
) -> Dict[str, Path]:
    """Compute and save correlation matrix CSV, summary CSV, JSON, and PNG heatmap."""
    output_dir.mkdir(parents=True, exist_ok=True)
    matrices = compute_correlation_matrices(df)
    summary_df = compute_correlation_summary(df, target="aqi")

    outputs = {}

    # Save Pearson correlation matrix CSV
    if not matrices["pearson"].empty:
        p_csv = output_dir / "correlation_matrix.csv"
        matrices["pearson"].to_csv(p_csv, index=True)
        outputs["correlation_matrix_csv"] = p_csv

    # Save Summary CSV
    if not summary_df.empty:
        s_csv = output_dir / "correlation_summary.csv"
        summary_df.to_csv(s_csv, index=False)
        outputs["correlation_summary_csv"] = s_csv

    # Save JSON summary of all 3 methods
    json_path = output_dir / "correlation_matrices.json"
    json_data = {
        "active_variables": list(matrices["pearson"].columns),
        "traffic_included": any(v in matrices["pearson"].columns for v in TRAFFIC_VARIABLES),
        "pearson": matrices["pearson"].to_dict(),
        "spearman": matrices["spearman"].to_dict(),
        "kendall": matrices["kendall"].to_dict(),
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    outputs["correlation_json"] = json_path

    # Save publication-quality PNG figure
    png_path = output_dir / "correlation_heatmap.png"
    save_correlation_figure(matrices["pearson"], png_path, title="UrbanTwin Pune: Pearson Correlation Matrix")
    outputs["correlation_heatmap_png"] = png_path

    logger.info(
        "Exported correlation reports",
        variables=len(matrices["pearson"].columns),
        output_dir=str(output_dir),
    )
    return outputs
