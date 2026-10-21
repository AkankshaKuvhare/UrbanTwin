"""Data Quality and Exploratory Data Analysis Pipeline for UrbanTwin (CongestAir Module).

Computes comprehensive missing value audits, temporal/station coverage,
pollutant descriptive statistics, completeness metrics, and exports
publication-ready figures and HTML/CSV reports.
"""

from datetime import date, datetime
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend for rendering
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import sys
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.logging import get_logger
from config.settings import settings
from database.models import AQIObservation, Station

logger = get_logger(__name__)

POLLUTANT_COLUMNS = ["aqi", "pm25", "pm10", "no2", "co", "so2", "o3"]


class DataQualityAnalyzer:
    """Core analytical engine for evaluating historical AQI data quality."""

    def __init__(self, df: pd.DataFrame) -> None:
        """Initialize analyzer with cleaned observation DataFrame.

        Expected columns:
            station_id, observation_date, aqi, pm25, pm10, no2, co, so2, o3, dominant_pollutant
            (and optionally station_name, city)
        """
        self.raw_df = df.copy()
        self.df = self._standardize_dataframe(df)

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names, date types, and numeric columns."""
        std_df = df.copy()

        # Normalize date column
        date_col = "observation_date" if "observation_date" in std_df.columns else "date"
        if date_col in std_df.columns:
            std_df["observation_date"] = pd.to_datetime(std_df[date_col]).dt.date
            std_df["datetime"] = pd.to_datetime(std_df[date_col])
        else:
            raise ValueError("DataFrame must contain 'observation_date' or 'date' column.")

        # Ensure station_id is string
        if "station_id" in std_df.columns:
            std_df["station_id"] = std_df["station_id"].astype(str).str.strip()

        # Ensure numeric fields are floats
        for col in POLLUTANT_COLUMNS:
            if col in std_df.columns:
                std_df[col] = pd.to_numeric(std_df[col], errors="coerce")
            else:
                std_df[col] = np.nan

        # Derived temporal features for EDA
        std_df["year"] = std_df["datetime"].dt.year
        std_df["month"] = std_df["datetime"].dt.month
        std_df["year_month"] = std_df["datetime"].dt.to_period("M").astype(str)
        std_df["day_of_week"] = std_df["datetime"].dt.day_name()

        return std_df

    # -------------------------------------------------------------------------
    # 1. Missing Value Report & Null Percentage
    # -------------------------------------------------------------------------
    def compute_missing_value_report(self) -> pd.DataFrame:
        """Compute null counts, valid counts, and null percentages for each column."""
        total_rows = len(self.df)
        records = []

        cols_to_check = [
            col for col in ["station_id", "station_name", "observation_date"] + POLLUTANT_COLUMNS + ["dominant_pollutant"]
            if col in self.df.columns
        ]

        for col in cols_to_check:
            null_count = int(self.df[col].isna().sum())
            valid_count = total_rows - null_count
            null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            records.append({
                "column": col,
                "total_rows": total_rows,
                "valid_count": valid_count,
                "null_count": null_count,
                "null_percentage": null_pct,
            })

        return pd.DataFrame(records)

    # -------------------------------------------------------------------------
    # 2. Duplicate Detection
    # -------------------------------------------------------------------------
    def compute_duplicate_report(self) -> Dict[str, Any]:
        """Detect duplicate station-date pairs and exact full-row duplicate records."""
        total_records = len(self.df)
        station_date_dups = int(self.df.duplicated(subset=["station_id", "observation_date"]).sum())
        exact_dups = int(self.df.duplicated().sum())

        return {
            "total_records": total_records,
            "duplicate_station_date_pairs": station_date_dups,
            "exact_duplicate_rows": exact_dups,
            "has_duplicates": (station_date_dups > 0 or exact_dups > 0),
        }

    # -------------------------------------------------------------------------
    # 3. Date Coverage
    # -------------------------------------------------------------------------
    def compute_date_coverage(self) -> Dict[str, Any]:
        """Compute min date, max date, total calendar days, and missing days."""
        if self.df.empty or "observation_date" not in self.df.columns:
            return {
                "start_date": None,
                "end_date": None,
                "total_calendar_days": 0,
                "observed_dates_count": 0,
                "missing_dates_count": 0,
                "temporal_coverage_pct": 0.0,
            }

        min_date = self.df["observation_date"].min()
        max_date = self.df["observation_date"].max()

        # Unique dates with at least one station reporting
        observed_dates = set(self.df["observation_date"].dropna().unique())
        observed_count = len(observed_dates)

        # Full calendar range
        all_dates_range = pd.date_range(start=min_date, end=max_date, freq="D").date
        total_days = len(all_dates_range)
        missing_count = total_days - observed_count
        coverage_pct = round((observed_count / total_days) * 100, 2) if total_days > 0 else 0.0

        return {
            "start_date": str(min_date),
            "end_date": str(max_date),
            "total_calendar_days": total_days,
            "observed_dates_count": observed_count,
            "missing_dates_count": missing_count,
            "temporal_coverage_pct": coverage_pct,
        }

    # -------------------------------------------------------------------------
    # 4. Station Coverage
    # -------------------------------------------------------------------------
    def compute_station_coverage(self) -> pd.DataFrame:
        """Analyze reporting statistics, date ranges, and observation counts per station."""
        records = []
        name_map = {}
        if "station_name" in self.df.columns:
            name_map = self.df.dropna(subset=["station_name"]).set_index("station_id")["station_name"].to_dict()

        for station_id, group in self.df.groupby("station_id"):
            st_name = name_map.get(station_id, f"Station {station_id}")
            st_min_date = group["observation_date"].min()
            st_max_date = group["observation_date"].max()
            st_total_days = (st_max_date - st_min_date).days + 1 if st_min_date and st_max_date else 0
            st_obs_count = len(group)
            st_unique_dates = group["observation_date"].nunique()
            st_coverage = round((st_unique_dates / st_total_days) * 100, 2) if st_total_days > 0 else 0.0
            avg_aqi = round(float(group["aqi"].mean()), 2) if group["aqi"].notna().any() else None

            records.append({
                "station_id": str(station_id),
                "station_name": st_name,
                "observation_count": st_obs_count,
                "first_date": str(st_min_date),
                "last_date": str(st_max_date),
                "active_days_span": st_total_days,
                "reporting_completeness_pct": st_coverage,
                "mean_aqi": avg_aqi,
            })

        return pd.DataFrame(records).sort_values("observation_count", ascending=False)

    # -------------------------------------------------------------------------
    # 5. Statistics (AQI and Pollutants)
    # -------------------------------------------------------------------------
    def compute_statistics(self) -> pd.DataFrame:
        """Generate parametric and non-parametric summary statistics for pollutants."""
        records = []
        for col in POLLUTANT_COLUMNS:
            series = self.df[col].dropna()
            if series.empty:
                records.append({
                    "parameter": col,
                    "count": 0,
                    "mean": None,
                    "std": None,
                    "min": None,
                    "q25": None,
                    "median": None,
                    "q75": None,
                    "max": None,
                    "skewness": None,
                    "kurtosis": None,
                })
                continue

            records.append({
                "parameter": col,
                "count": int(series.count()),
                "mean": round(float(series.mean()), 2),
                "std": round(float(series.std()), 2),
                "min": round(float(series.min()), 2),
                "q25": round(float(series.quantile(0.25)), 2),
                "median": round(float(series.median()), 2),
                "q75": round(float(series.quantile(0.75)), 2),
                "max": round(float(series.max()), 2),
                "skewness": round(float(series.skew()), 2),
                "kurtosis": round(float(series.kurtosis()), 2),
            })

        return pd.DataFrame(records)

    # -------------------------------------------------------------------------
    # 6. Daily Observation Counts
    # -------------------------------------------------------------------------
    def compute_daily_observation_counts(self) -> pd.DataFrame:
        """Compute the frequency of observations collected per calendar day."""
        daily_counts = (
            self.df.groupby("observation_date")
            .size()
            .reset_index(name="observation_count")
        )
        return daily_counts.sort_values("observation_date")

    # -------------------------------------------------------------------------
    # 7. Data Completeness Score
    # -------------------------------------------------------------------------
    def compute_data_completeness_score(self) -> float:
        """Compute aggregate data completeness score (0.0 to 100.0%).

        Formula:
            completeness = (total non-null cells across core pollutants) /
                           (total rows * number of pollutants) * 100.0
        """
        if self.df.empty:
            return 0.0

        total_cells = len(self.df) * len(POLLUTANT_COLUMNS)
        valid_cells = int(self.df[POLLUTANT_COLUMNS].notna().sum().sum())
        return round((valid_cells / total_cells) * 100, 2) if total_cells > 0 else 0.0

    # -------------------------------------------------------------------------
    # Comprehensive Summary Dictionary
    # -------------------------------------------------------------------------
    def generate_full_report(self) -> Dict[str, Any]:
        """Aggregate all analytical modules into an integrated summary dictionary."""
        missing_df = self.compute_missing_value_report()
        stats_df = self.compute_statistics()
        station_df = self.compute_station_coverage()
        date_cov = self.compute_date_coverage()
        dups = self.compute_duplicate_report()
        completeness = self.compute_data_completeness_score()

        mean_aqi = round(float(self.df["aqi"].mean()), 2) if self.df["aqi"].notna().any() else None

        return {
            "generated_at": datetime.now().isoformat(),
            "total_observations": len(self.df),
            "total_stations": int(self.df["station_id"].nunique()),
            "average_aqi": mean_aqi,
            "data_completeness_score": completeness,
            "date_coverage": date_cov,
            "duplicates": dups,
            "missing_values": missing_df.to_dict(orient="records"),
            "pollutant_statistics": stats_df.to_dict(orient="records"),
            "station_coverage": station_df.to_dict(orient="records"),
        }

    # -------------------------------------------------------------------------
    # Visualization Generation (Publication-Ready PNG Plots)
    # -------------------------------------------------------------------------
    def generate_and_save_plots(self, output_dir: Union[str, Path]) -> Dict[str, Path]:
        """Generate all 11 required exploratory and quality plots as PNG files.

        Returns:
            Dictionary mapping plot name to its absolute file path.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        saved_plots: Dict[str, Path] = {}

        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        # 1. AQI over time
        fig, ax = plt.subplots(figsize=(12, 5))
        daily_aqi = self.df.groupby("datetime")["aqi"].mean().dropna()
        ax.plot(daily_aqi.index, daily_aqi.values, color="#1f77b4", linewidth=1.2, alpha=0.85, label="Daily Mean AQI")
        ax.set_title("Pune Historical AQI Over Time", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel("AQI", fontsize=11)
        ax.axhline(100, color="orange", linestyle="--", alpha=0.7, label="Moderate Threshold (100)")
        ax.axhline(200, color="red", linestyle="--", alpha=0.7, label="Poor Threshold (200)")
        ax.legend(loc="upper right")
        fig.tight_layout()
        p1 = out_path / "aqi_over_time.png"
        fig.savefig(p1, dpi=200)
        plt.close(fig)
        saved_plots["aqi_over_time"] = p1

        # 2. PM2.5 trend
        fig, ax = plt.subplots(figsize=(12, 4.5))
        daily_pm25 = self.df.groupby("datetime")["pm25"].mean().dropna()
        ax.plot(daily_pm25.index, daily_pm25.values, color="#d62728", linewidth=1.2)
        ax.set_title("PM2.5 Historical Trend (µg/m³)", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("PM2.5 (µg/m³)", fontsize=10)
        ax.axhline(60, color="darkred", linestyle=":", label="NAAQS 24h Standard (60 µg/m³)")
        ax.legend(loc="upper right")
        fig.tight_layout()
        p2 = out_path / "pm25_trend.png"
        fig.savefig(p2, dpi=200)
        plt.close(fig)
        saved_plots["pm25_trend"] = p2

        # 3. PM10 trend
        fig, ax = plt.subplots(figsize=(12, 4.5))
        daily_pm10 = self.df.groupby("datetime")["pm10"].mean().dropna()
        ax.plot(daily_pm10.index, daily_pm10.values, color="#ff7f0e", linewidth=1.2)
        ax.set_title("PM10 Historical Trend (µg/m³)", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("PM10 (µg/m³)", fontsize=10)
        ax.axhline(100, color="darkorange", linestyle=":", label="NAAQS 24h Standard (100 µg/m³)")
        ax.legend(loc="upper right")
        fig.tight_layout()
        p3 = out_path / "pm10_trend.png"
        fig.savefig(p3, dpi=200)
        plt.close(fig)
        saved_plots["pm10_trend"] = p3

        # 4. NO2 trend
        fig, ax = plt.subplots(figsize=(12, 4.5))
        daily_no2 = self.df.groupby("datetime")["no2"].mean().dropna()
        ax.plot(daily_no2.index, daily_no2.values, color="#2ca02c", linewidth=1.2)
        ax.set_title("NO2 Historical Trend (µg/m³)", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("NO2 (µg/m³)", fontsize=10)
        ax.axhline(80, color="darkgreen", linestyle=":", label="NAAQS 24h Standard (80 µg/m³)")
        ax.legend(loc="upper right")
        fig.tight_layout()
        p4 = out_path / "no2_trend.png"
        fig.savefig(p4, dpi=200)
        plt.close(fig)
        saved_plots["no2_trend"] = p4

        # 5. Dominant pollutant frequency
        fig, ax = plt.subplots(figsize=(8, 5))
        if "dominant_pollutant" in self.df.columns and self.df["dominant_pollutant"].notna().any():
            dom_counts = self.df["dominant_pollutant"].value_counts()
            bars = ax.bar(dom_counts.index, dom_counts.values, color="#9467bd", edgecolor="black", alpha=0.85)
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f"{height}", xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=10)
        ax.set_title("Dominant Pollutant Frequency", fontsize=13, fontweight="bold", pad=10)
        ax.set_ylabel("Count of Observations", fontsize=10)
        fig.tight_layout()
        p5 = out_path / "dominant_pollutant_frequency.png"
        fig.savefig(p5, dpi=200)
        plt.close(fig)
        saved_plots["dominant_pollutant_frequency"] = p5

        # 6. AQI distribution
        fig, ax = plt.subplots(figsize=(9, 5))
        aqi_clean = self.df["aqi"].dropna()
        ax.hist(aqi_clean, bins=40, color="#17becf", edgecolor="black", alpha=0.8, density=True)
        ax.set_title("Distribution of Historical AQI", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("AQI Value", fontsize=10)
        ax.set_ylabel("Probability Density", fontsize=10)
        if not aqi_clean.empty:
            ax.axvline(aqi_clean.mean(), color="red", linestyle="--", label=f"Mean: {aqi_clean.mean():.1f}")
            ax.axvline(aqi_clean.median(), color="green", linestyle="-", label=f"Median: {aqi_clean.median():.1f}")
            ax.legend(loc="upper right")
        fig.tight_layout()
        p6 = out_path / "aqi_distribution.png"
        fig.savefig(p6, dpi=200)
        plt.close(fig)
        saved_plots["aqi_distribution"] = p6

        # 7. Correlation matrix between pollutants
        fig, ax = plt.subplots(figsize=(8, 7))
        corr_cols = [c for c in POLLUTANT_COLUMNS if self.df[c].notna().sum() > 5]
        corr_matrix = self.df[corr_cols].corr()
        cax = ax.imshow(corr_matrix, cmap="coolwarm", vmin=-1, vmax=1)
        fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
        ax.set_xticks(range(len(corr_cols)))
        ax.set_yticks(range(len(corr_cols)))
        ax.set_xticklabels(corr_cols, rotation=45, ha="right")
        ax.set_yticklabels(corr_cols)
        ax.set_title("Pollutant Correlation Matrix", fontsize=13, fontweight="bold", pad=10)
        for i in range(len(corr_cols)):
            for j in range(len(corr_cols)):
                val = corr_matrix.iloc[i, j]
                if not np.isnan(val):
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                            color="black" if abs(val) < 0.6 else "white", fontsize=9)
        fig.tight_layout()
        p7 = out_path / "correlation_matrix.png"
        fig.savefig(p7, dpi=200)
        plt.close(fig)
        saved_plots["correlation_matrix"] = p7

        # 8. Missing value heatmap
        fig, ax = plt.subplots(figsize=(10, 5))
        null_subset = self.df[POLLUTANT_COLUMNS].isna().astype(int)
        # Sample if large to keep heatmap legible
        if len(null_subset) > 500:
            null_sample = null_subset.sample(500, random_state=42).sort_index()
        else:
            null_sample = null_subset
        ax.imshow(null_sample.T, cmap="binary", aspect="auto", interpolation="nearest")
        ax.set_yticks(range(len(POLLUTANT_COLUMNS)))
        ax.set_yticklabels(POLLUTANT_COLUMNS)
        ax.set_xlabel("Observations (Black = Missing, White = Present)", fontsize=10)
        ax.set_title("Missing Values Heatmap across Pollutants", fontsize=13, fontweight="bold", pad=10)
        fig.tight_layout()
        p8 = out_path / "missing_value_heatmap.png"
        fig.savefig(p8, dpi=200)
        plt.close(fig)
        saved_plots["missing_value_heatmap"] = p8

        # 9. Monthly AQI trend
        fig, ax = plt.subplots(figsize=(10, 5))
        monthly_avg = self.df.groupby("month")["aqi"].mean()
        months_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        present_months = [m for m in range(1, 13) if m in monthly_avg.index]
        ax.bar([months_labels[m - 1] for m in present_months], [monthly_avg[m] for m in present_months],
               color="#e377c2", edgecolor="black", alpha=0.85)
        ax.set_title("Seasonality: Monthly Average AQI in Pune", fontsize=13, fontweight="bold", pad=10)
        ax.set_ylabel("Mean AQI", fontsize=10)
        fig.tight_layout()
        p9 = out_path / "monthly_aqi_trend.png"
        fig.savefig(p9, dpi=200)
        plt.close(fig)
        saved_plots["monthly_aqi_trend"] = p9

        # 10. Yearly AQI trend
        fig, ax = plt.subplots(figsize=(8, 5))
        yearly_avg = self.df.groupby("year")["aqi"].mean()
        ax.plot(yearly_avg.index.astype(str), yearly_avg.values, marker="o", color="#8c564b", linewidth=2, markersize=7)
        for x, y in zip(yearly_avg.index.astype(str), yearly_avg.values):
            ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontweight="bold")
        ax.set_title("Inter-Annual Average AQI Trend", fontsize=13, fontweight="bold", pad=10)
        ax.set_ylabel("Mean AQI", fontsize=10)
        ax.set_xlabel("Year", fontsize=10)
        fig.tight_layout()
        p10 = out_path / "yearly_aqi_trend.png"
        fig.savefig(p10, dpi=200)
        plt.close(fig)
        saved_plots["yearly_aqi_trend"] = p10

        # 11. Station-wise AQI comparison
        fig, ax = plt.subplots(figsize=(11, 5.5))
        st_data = []
        st_labels = []
        name_map = {}
        if "station_name" in self.df.columns:
            name_map = self.df.dropna(subset=["station_name"]).set_index("station_id")["station_name"].to_dict()

        for st_id, group in self.df.groupby("station_id"):
            vals = group["aqi"].dropna().values
            if len(vals) > 0:
                st_data.append(vals)
                label = name_map.get(st_id, st_id)
                if len(label) > 25:
                    label = label[:22] + "..."
                st_labels.append(label)

        if st_data:
            ax.boxplot(st_data, tick_labels=st_labels, patch_artist=True,
                       boxprops=dict(facecolor="#bcbd22", color="black"),
                       medianprops=dict(color="darkred", linewidth=1.5))
            ax.set_xticklabels(st_labels, rotation=30, ha="right", fontsize=9)
            ax.set_title("Station-Wise AQI Distribution Comparison", fontsize=13, fontweight="bold", pad=10)
            ax.set_ylabel("AQI", fontsize=10)
        fig.tight_layout()
        p11 = out_path / "station_wise_aqi_comparison.png"
        fig.savefig(p11, dpi=200)
        plt.close(fig)
        saved_plots["station_wise_aqi_comparison"] = p11

        logger.info("Generated all 11 exploratory data quality plots", output_dir=str(out_path))
        return saved_plots

    # -------------------------------------------------------------------------
    # Report Export (CSV Summary & HTML Report)
    # -------------------------------------------------------------------------
    def export_reports(self, output_dir: Union[str, Path]) -> Dict[str, Path]:
        """Export CSV summary, figures, and an interactive HTML report to disk.

        Args:
            output_dir: Base directory (e.g. reports/data_quality/)

        Returns:
            Dictionary of exported file paths.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        figures_dir = out_path / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate Figures
        saved_plots = self.generate_and_save_plots(figures_dir)

        # 2. Export CSV Summaries
        missing_df = self.compute_missing_value_report()
        stats_df = self.compute_statistics()
        station_df = self.compute_station_coverage()

        csv_summary_path = out_path / "data_quality_summary.csv"
        missing_df.to_csv(csv_summary_path, index=False)

        stats_csv_path = out_path / "pollutant_statistics.csv"
        stats_df.to_csv(stats_csv_path, index=False)

        station_csv_path = out_path / "station_coverage.csv"
        station_df.to_csv(station_csv_path, index=False)

        # 3. Generate HTML Report
        full_summary = self.generate_full_report()
        html_report_path = out_path / "data_quality_report.html"
        html_content = self._build_html_report(full_summary, saved_plots)
        html_report_path.write_text(html_content, encoding="utf-8")

        return {
            "csv_summary": csv_summary_path,
            "pollutant_statistics_csv": stats_csv_path,
            "station_coverage_csv": station_csv_path,
            "html_report": html_report_path,
            "figures_dir": figures_dir,
        }

    def _build_html_report(self, summary: Dict[str, Any], plots: Dict[str, Path]) -> str:
        """Construct a responsive HTML dashboard report."""
        date_cov = summary["date_coverage"]
        dups = summary["duplicates"]
        completeness = summary["data_completeness_score"]

        # Missing values table HTML
        missing_rows = "".join(
            f"<tr><td><strong>{r['column']}</strong></td><td>{r['valid_count']}</td>"
            f"<td>{r['null_count']}</td><td><div class='progress-bar'><div class='progress' style='width:{r['null_percentage']}%'></div></div> {r['null_percentage']}%</td></tr>"
            for r in summary["missing_values"]
        )

        # Statistics table HTML
        stat_rows = "".join(
            f"<tr><td><strong>{r['parameter'].upper()}</strong></td><td>{r['count']}</td>"
            f"<td>{r['mean']}</td><td>{r['std']}</td><td>{r['min']}</td><td>{r['median']}</td><td>{r['max']}</td>"
            f"<td>{r['skewness']}</td></tr>"
            for r in summary["pollutant_statistics"]
        )

        # Station table HTML
        station_rows = "".join(
            f"<tr><td>{r['station_id']}</td><td>{r['station_name']}</td><td>{r['observation_count']}</td>"
            f"<td>{r['first_date']} to {r['last_date']}</td><td>{r['reporting_completeness_pct']}%</td><td>{r['mean_aqi']}</td></tr>"
            for r in summary["station_coverage"]
        )

        # Gallery HTML
        gallery_items = "".join(
            f"<div class='figure-card'><h4>{name.replace('_', ' ').title()}</h4><img src='figures/{path.name}' alt='{name}' /></div>"
            for name, path in plots.items()
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UrbanTwin - Historical AQI Data Quality Report</title>
    <style>
        :root {{
            --primary: #1e3a8a;
            --secondary: #3b82f6;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #0f172a;
            --border: #e2e8f0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
        }}
        .header {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 24px;
            border: 1px solid var(--border);
        }}
        .header h1 {{ margin: 0 0 8px 0; color: var(--primary); }}
        .header p {{ margin: 0; color: #64748b; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .metric-title {{ font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; }}
        .metric-value {{ font-size: 1.8rem; font-weight: 700; color: var(--primary); margin-top: 6px; }}
        .section {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 24px;
        }}
        h2 {{ margin-top: 0; color: var(--primary); font-size: 1.3rem; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 0.92rem;
        }}
        th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #f8fafc; color: #475569; font-weight: 600; }}
        .progress-bar {{
            background: #e2e8f0;
            border-radius: 999px;
            height: 8px;
            width: 80px;
            display: inline-block;
            vertical-align: middle;
            margin-right: 6px;
            overflow: hidden;
        }}
        .progress {{ background: #ef4444; height: 100%; }}
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
            gap: 20px;
        }}
        .figure-card {{
            background: #fff;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .figure-card h4 {{ margin: 0 0 8px 0; color: #334155; font-size: 0.95rem; }}
        .figure-card img {{ width: 100%; height: auto; border-radius: 4px; display: block; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>UrbanTwin - CongestAir Quality & EDA Report</h1>
        <p>Comprehensive historical air quality profiling and data health audit for Pune, India | Generated: {summary['generated_at']}</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">Total Observations</div>
            <div class="metric-value">{summary['total_observations']:,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Active Stations</div>
            <div class="metric-value">{summary['total_stations']}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Date Span</div>
            <div class="metric-value" style="font-size: 1.1rem; margin-top: 10px;">{date_cov['start_date']} &rarr; {date_cov['end_date']}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Average AQI</div>
            <div class="metric-value">{summary['average_aqi']}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Data Completeness</div>
            <div class="metric-value">{completeness}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Duplicate Rows</div>
            <div class="metric-value">{dups['duplicate_station_date_pairs']}</div>
        </div>
    </div>

    <div class="section">
        <h2>Pollutant Descriptive Statistics</h2>
        <table>
            <thead>
                <tr>
                    <th>Pollutant</th><th>Valid Count</th><th>Mean</th><th>Std</th><th>Min</th><th>Median</th><th>Max</th><th>Skewness</th>
                </tr>
            </thead>
            <tbody>
                {stat_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Station Coverage & Data Completeness</h2>
        <table>
            <thead>
                <tr>
                    <th>Station ID</th><th>Station Name</th><th>Observations</th><th>Temporal Coverage</th><th>Continuity</th><th>Mean AQI</th>
                </tr>
            </thead>
            <tbody>
                {station_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Missing Value Audit</h2>
        <table>
            <thead>
                <tr>
                    <th>Field</th><th>Valid Records</th><th>Null Count</th><th>Missing Percentage</th>
                </tr>
            </thead>
            <tbody>
                {missing_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Exploratory Visualizations</h2>
        <div class="gallery-grid">
            {gallery_items}
        </div>
    </div>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# Standalone Pipeline Function / Factory
# -----------------------------------------------------------------------------
def run_data_quality_pipeline(
    csv_path: Optional[Union[str, Path]] = None,
    db_url: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Execute complete data quality audit from DB or CSV fallback and export reports."""
    out_dir = Path(output_dir) if output_dir else settings.BASE_DIR / "reports" / "data_quality"
    out_dir.mkdir(parents=True, exist_ok=True)

    df: Optional[pd.DataFrame] = None

    # 1. Try reading from Database if connection is provided or default configured
    target_url = db_url or settings.DATABASE_URL
    try:
        engine = create_engine(target_url)
        with engine.connect() as conn:
            # Query stations joined with observations
            query = """
                SELECT 
                    o.id, o.station_id, o.observation_date, o.aqi, o.pm25, o.pm10, 
                    o.no2, o.co, o.so2, o.o3, o.dominant_pollutant,
                    s.station_name, s.city, s.latitude, s.longitude
                FROM aqi_observations o
                LEFT JOIN stations s ON o.station_id = s.station_id
                ORDER BY o.observation_date ASC
            """
            df = pd.read_sql(query, conn)
            logger.info("Loaded records from database for quality audit", row_count=len(df))
    except Exception as db_exc:
        logger.warning("Could not read from database directly, falling back to CSV", error=str(db_exc))

    # 2. Fallback to CSV if DB was empty or unavailable
    if df is None or df.empty:
        candidate_paths = [
            Path(csv_path) if csv_path else None,
            settings.BASE_DIR / "data" / "all_stations_combined.csv",
            settings.BASE_DIR / "data" / "real" / "raw" / "all_stations_combined.csv",
            Path.home() / "Downloads" / "all_stations_combined.csv",
        ]
        valid_csv = next((p for p in candidate_paths if p is not None and p.exists()), None)
        if valid_csv is None:
            raise FileNotFoundError("No data source found. Database was unreachable and CSV not found.")
        df = pd.read_csv(valid_csv)
        logger.info("Loaded records from CSV fallback for quality audit", csv_path=str(valid_csv), row_count=len(df))

    # 3. Analyze and Export
    analyzer = DataQualityAnalyzer(df)
    exports = analyzer.export_reports(out_dir)
    full_report = analyzer.generate_full_report()

    return {
        "status": "success",
        "report_summary": full_report,
        "exported_files": {k: str(v) for k, v in exports.items()},
    }


if __name__ == "__main__":
    result = run_data_quality_pipeline()
    print("\n--- DATA QUALITY PIPELINE COMPLETED ---")
    print(f"Total Observations Analyzed: {result['report_summary']['total_observations']}")
    print(f"Data Completeness Score:     {result['report_summary']['data_completeness_score']}%")
    print(f"HTML Report Generated at:   {result['exported_files']['html_report']}")
    print(f"Summary CSV Generated at:    {result['exported_files']['csv_summary']}")
