"""Force-Directed Relationship Network Graph Module for UrbanTwin Milestone 8.

Creates an interactive force-directed graph mapping complex interdependencies between:
- Air Quality Indicators (AQI, PM2.5, PM10, NO2, CO, SO2, O3)
- Meteorological Drivers (Temperature, Humidity, Wind Speed, Pressure, Boundary Layer Ht)
- Traffic Conditions (Speed, Congestion, Travel Time - automatically added when active)

Graph Specifications:
- Nodes: Sized by degree centrality and colored by domain (Air Quality, Weather, Traffic).
- Interactive Node Hover: Variable name, Mean, Std Dev, and Missing Percentage.
- Edges: Weighted by absolute Pearson correlation |r|.
- Edge Thickness: Proportional to relationship strength (|r|).
- Edge Colors: Green (#22c55e) for positive correlation, Red (#ef4444) for negative correlation.
- Edge Labels: Correlation coefficient r.

Exports:
- `network_edges.csv`
- Publication-quality PNG figure
- Interactive Plotly force-directed network visualization
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analytics.correlation import (
    DEFAULT_VARIABLE_LABELS,
    POLLUTANT_VARIABLES,
    WEATHER_VARIABLES,
    TRAFFIC_VARIABLES,
    compute_correlation_matrices,
    get_active_variables,
)
from config.logging import get_logger

logger = get_logger("urbantwin.analytics.network")

# Node category colors
CATEGORY_COLORS: Dict[str, str] = {
    "Pollutant": "#38bdf8",   # Sky blue
    "Weather": "#f59e0b",     # Amber
    "Traffic": "#ec4899",     # Pink / Magenta
}


def build_network_graph_data(
    df: pd.DataFrame,
    threshold: float = 0.20,
    variables: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Construct network node and edge metadata from correlation matrix.

    Args:
        df: Input DataFrame.
        threshold: Minimum absolute Pearson correlation |r| to establish an edge.
        variables: Optional explicit variable list.

    Returns:
        Dictionary containing nodes, edges, summary stats, and NetworkX graph instance.
    """
    target_vars = variables or get_active_variables(df)
    corr_matrices = compute_correlation_matrices(df, variables=target_vars)
    pearson_df = corr_matrices["pearson"]

    if pearson_df.empty:
        return {"nodes": [], "edges": [], "graph": nx.Graph(), "stats": {}}

    # Compute node statistics (mean, std, missing_pct)
    nodes = []
    total_rows = len(df)
    for col in target_vars:
        s = pd.to_numeric(df[col], errors="coerce")
        valid = s.dropna()
        n_missing = total_rows - len(valid)
        missing_pct = round(n_missing / total_rows * 100, 1) if total_rows > 0 else 0.0

        category = "Pollutant" if col in POLLUTANT_VARIABLES else (
            "Traffic" if col in TRAFFIC_VARIABLES else "Weather"
        )

        nodes.append({
            "id": col,
            "label": DEFAULT_VARIABLE_LABELS.get(col, col),
            "category": category,
            "color": CATEGORY_COLORS.get(category, "#94a3b8"),
            "mean": round(float(valid.mean()), 2) if len(valid) > 0 else 0.0,
            "std": round(float(valid.std()), 2) if len(valid) > 0 else 0.0,
            "missing_pct": missing_pct,
            "observations": int(len(valid)),
        })

    # Build NetworkX graph
    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"], **n)

    edges = []
    cols = list(pearson_df.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            u, v = cols[i], cols[j]
            r_val = pearson_df.loc[u, v]
            if not np.isnan(r_val) and abs(r_val) >= threshold:
                abs_r = abs(float(r_val))
                is_pos = r_val >= 0
                edge_color = "#22c55e" if is_pos else "#ef4444"
                edge_type = "positive" if is_pos else "negative"

                edge_info = {
                    "source": u,
                    "target": v,
                    "source_label": DEFAULT_VARIABLE_LABELS.get(u, u),
                    "target_label": DEFAULT_VARIABLE_LABELS.get(v, v),
                    "weight": round(abs_r, 4),
                    "correlation": round(float(r_val), 4),
                    "edge_type": edge_type,
                    "color": edge_color,
                    "thickness": round(1.0 + abs_r * 5.0, 2),  # 1.0 to 6.0 px
                }
                edges.append(edge_info)
                G.add_edge(u, v, weight=abs_r, correlation=r_val, color=edge_color)

    # Compute degree centrality for node sizing
    centralities = nx.degree_centrality(G) if len(G) > 0 else {}
    for n in nodes:
        n["centrality"] = round(float(centralities.get(n["id"], 0.0)), 3)

    return {
        "nodes": nodes,
        "edges": edges,
        "graph": G,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "threshold": threshold,
            "density": round(float(nx.density(G)), 3) if len(G) > 0 else 0.0,
        },
    }


def generate_network_graph_fig(
    df: pd.DataFrame,
    threshold: float = 0.20,
    dark_mode: bool = True,
) -> go.Figure:
    """Generate an interactive Plotly force-directed network visualization.

    Includes spring layout positioning, green/red weighted edges, and interactive hover.
    """
    data = build_network_graph_data(df, threshold=threshold)
    nodes = data["nodes"]
    edges = data["edges"]
    G = data["graph"]

    if not nodes or G.number_of_nodes() == 0:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data to build relationship network", showarrow=False)
        return fig

    # Compute 2D spring force-directed layout
    pos = nx.spring_layout(G, k=0.6, iterations=60, seed=42)

    bg_color = "#0f172a" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#1e293b"

    fig = go.Figure()

    # Draw edges
    # Separate into positive (green) and negative (red) traces for legend
    pos_x, pos_y = [], []
    neg_x, neg_y = [], []

    edge_traces = []
    for edge in edges:
        u = edge["source"]
        v = edge["target"]
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            
            # Midpoint for label / hover
            xm = (x0 + x1) / 2
            ym = (y0 + y1) / 2

            fig.add_trace(
                go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode="lines",
                    line=dict(
                        width=edge["thickness"],
                        color=edge["color"],
                    ),
                    hoverinfo="text",
                    text=f"<b>{edge['source_label']}</b> -- <b>{edge['target_label']}</b><br>r = {edge['correlation']:+.3f} (|r| = {edge['weight']:.2f})",
                    showlegend=False,
                )
            )

    # Draw nodes
    node_x, node_y, node_colors, node_sizes, node_hovers, node_labels = [], [], [], [], [], []
    for n in nodes:
        nid = n["id"]
        if nid in pos:
            x, y = pos[nid]
            node_x.append(x)
            node_y.append(y)
            node_colors.append(n["color"])
            # Scale node size with centrality
            size = 18 + n["centrality"] * 24
            node_sizes.append(size)
            node_labels.append(n["label"])

            hover = (
                f"<b>{n['label']}</b> ({n['category']})<br>"
                f"Mean: {n['mean']}<br>"
                f"Std Dev: {n['std']}<br>"
                f"Missing: {n['missing_pct']}%<br>"
                f"Degree Centrality: {n['centrality']}<br>"
                f"Valid Obs: {n['observations']:,}"
            )
            node_hovers.append(hover)

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color="#ffffff" if dark_mode else "#0f172a"),
            ),
            text=node_labels,
            textposition="top center",
            textfont=dict(color=text_color, size=11, family="Inter, system-ui"),
            hoverinfo="text",
            hovertext=node_hovers,
            name="UrbanTwin Variables",
        )
    )

    # Dummy legend entries for edge color interpretation
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color="#22c55e", width=3),
            name="Positive Correlation (Green)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color="#ef4444", width=3),
            name="Negative Correlation (Red)",
        )
    )

    fig.update_layout(
        title=dict(
            text=f"<b>Urban Twin Relationship Network Graph</b> (|r| ≥ {threshold:.2f})",
            font=dict(color=text_color, size=16),
        ),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color=text_color, size=11),
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=680,
        margin=dict(l=40, r=40, t=80, b=40),
    )
    return fig


def save_network_figure(
    df: pd.DataFrame,
    output_path: Path,
    threshold: float = 0.20,
) -> Path:
    """Save publication-quality PNG force-directed network using Matplotlib and NetworkX."""
    data = build_network_graph_data(df, threshold=threshold)
    G = data["graph"]
    nodes = {n["id"]: n for n in data["nodes"]}

    if G.number_of_nodes() == 0:
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pos = nx.spring_layout(G, k=0.6, iterations=80, seed=42)

    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # Draw edges
    edges = G.edges(data=True)
    for u, v, d in edges:
        color = d.get("color", "#64748b")
        weight = d.get("weight", 0.5)
        lw = 1.0 + weight * 4.0
        x = [pos[u][0], pos[v][0]]
        y = [pos[u][1], pos[v][1]]
        ax.plot(x, y, color=color, linewidth=lw, alpha=0.75, zorder=1)

    # Draw nodes
    for nid, (x, y) in pos.items():
        n_info = nodes.get(nid, {})
        color = n_info.get("color", "#0284c7")
        size = 500 + n_info.get("centrality", 0.1) * 1000
        ax.scatter(x, y, s=size, color=color, edgecolor="#1e293b", linewidth=1.5, zorder=2)
        label = n_info.get("label", nid)
        ax.text(x, y + 0.05, label, fontsize=9, fontweight="bold", ha="center", va="bottom", zorder=3)

    # Annotate legend
    ax.plot([], [], color="#22c55e", linewidth=2.5, label="Positive Correlation")
    ax.plot([], [], color="#ef4444", linewidth=2.5, label="Negative Correlation")
    ax.scatter([], [], s=120, color=CATEGORY_COLORS["Pollutant"], label="Pollutant Node")
    ax.scatter([], [], s=120, color=CATEGORY_COLORS["Weather"], label="Weather Node")
    if any(n["category"] == "Traffic" for n in data["nodes"]):
        ax.scatter([], [], s=120, color=CATEGORY_COLORS["Traffic"], label="Traffic Node")

    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax.set_title(f"UrbanTwin Pune: Force-Directed Relationship Network (|r| ≥ {threshold:.2f})", fontsize=13, fontweight="bold", pad=15)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def export_network_reports(
    df: pd.DataFrame,
    output_dir: Path,
    threshold: float = 0.20,
) -> Dict[str, Path]:
    """Export network_edges.csv, network_nodes.json, and network_graph.png."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data = build_network_graph_data(df, threshold=threshold)

    outputs = {}
    edges_df = pd.DataFrame(data["edges"])
    if not edges_df.empty:
        csv_path = output_dir / "network_edges.csv"
        edges_df.to_csv(csv_path, index=False)
        outputs["network_edges_csv"] = csv_path

    # Nodes JSON
    json_path = output_dir / "network_data.json"
    clean_nodes = [{k: v for k, v in n.items() if k != "graph"} for n in data["nodes"]]
    clean_edges = [{k: v for k, v in e.items()} for e in data["edges"]]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"nodes": clean_nodes, "edges": clean_edges, "stats": data["stats"]}, f, indent=2)
    outputs["network_json"] = json_path

    # Publication PNG
    png_path = output_dir / "network_graph.png"
    save_network_figure(df, png_path, threshold=threshold)
    outputs["network_graph_png"] = png_path

    logger.info("Exported network graph reports", edges_count=len(edges_df), output_dir=str(output_dir))
    return outputs
