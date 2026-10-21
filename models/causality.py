"""Causality and Econometric Time-Series Analysis Interface (Stage 6).

Implements Vector Autoregression (VAR) and Granger Causality testing to determine
whether traffic congestion causally precedes short-term air quality variation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel


class GrangerTestSummary(BaseModel):
    """Encapsulates the statistical results of a bivariate or multivariate Granger test."""
    target_variable: str
    causing_variable: str
    optimal_lag_hours: int
    f_statistic: float
    p_value: float
    is_causally_significant: bool  # typically p < 0.05
    test_type: str = "ssr_ftest"


class BaseCausalityTester(ABC):
    """Abstract interface for causality testing across time series panels."""

    @abstractmethod
    def test_stationarity(
        self,
        series: pd.Series,
        significance_level: float = 0.05,
    ) -> Dict[str, Any]:
        """Perform Augmented Dickey-Fuller (ADF) and KPSS stationarity tests.
        
        Args:
            series: Univariate time series to test.
            significance_level: Critical threshold for hypothesis rejection.

        Returns:
            Dict containing test statistics, p-values, and differencing recommendation.
        """
        pass

    @abstractmethod
    def select_var_lag_order(
        self,
        data: pd.DataFrame,
        max_lags: int = 24,
    ) -> Dict[str, int]:
        """Select optimal VAR lag order using AIC, BIC, HQIC, and FPE criteria."""
        pass

    @abstractmethod
    def run_granger_causality(
        self,
        data: pd.DataFrame,
        target_col: str,
        cause_col: str,
        max_lags: int = 12,
    ) -> List[GrangerTestSummary]:
        """Test whether cause_col Granger-causes target_col across candidate time lags.
        
        Returns:
            List of GrangerTestSummary objects for each evaluated lag.
        """
        pass


class VARGrangerTester(BaseCausalityTester):
    """Statsmodels-backed VAR & Granger Causality test implementation."""

    def test_stationarity(
        self,
        series: pd.Series,
        significance_level: float = 0.05,
    ) -> Dict[str, Any]:
        raise NotImplementedError("VARGrangerTester.test_stationarity is not yet implemented.")

    def select_var_lag_order(
        self,
        data: pd.DataFrame,
        max_lags: int = 24,
    ) -> Dict[str, int]:
        raise NotImplementedError("VARGrangerTester.select_var_lag_order is not yet implemented.")

    def run_granger_causality(
        self,
        data: pd.DataFrame,
        target_col: str,
        cause_col: str,
        max_lags: int = 12,
    ) -> List[GrangerTestSummary]:
        raise NotImplementedError("VARGrangerTester.run_granger_causality is not yet implemented.")
