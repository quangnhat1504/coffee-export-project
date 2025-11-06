"""
Utility functions for data processing, interpolation, and formatting
"""
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np


def interpolate_time_series(
    df: pd.DataFrame,
    column: str,
    method: str = 'polynomial',
    order: int = 2,
    growth_damping: float = 0.8
) -> pd.Series:
    """
    Professional time series interpolation with edge case handling.
    
    Args:
        df: DataFrame with time series data
        column: Column name to interpolate
        method: Interpolation method ('polynomial', 'linear')
        order: Polynomial order (only for polynomial method)
        growth_damping: Damping factor for growth rate extrapolation (0-1)
    
    Returns:
        Interpolated Series
    """
    series = df[column].copy()
    
    # Step 1: Polynomial/Linear interpolation for middle values
    if method == 'polynomial':
        series = series.interpolate(
            method='polynomial',
            order=order,
            limit_direction='both'
        )
    else:
        series = series.interpolate(
            method='linear',
            limit_direction='both'
        )
    
    # Step 2: Handle trailing NaNs (extrapolate forward)
    if series.isna().any():
        last_valid_idx = series.last_valid_index()
        if last_valid_idx is not None and last_valid_idx < len(series) - 1:
            valid_data = series.dropna().tail(5)
            if len(valid_data) >= 2:
                recent_growth = (valid_data.iloc[-1] - valid_data.iloc[-2]) / valid_data.iloc[-2]
                for i in range(last_valid_idx + 1, len(series)):
                    if pd.isna(series.iloc[i]):
                        series.iloc[i] = series.iloc[i - 1] * (1 + recent_growth * growth_damping)
    
    # Step 3: Handle leading NaNs (extrapolate backward)
    if series.isna().any():
        first_valid_idx = series.first_valid_index()
        if first_valid_idx is not None and first_valid_idx > 0:
            valid_data = series.dropna().head(5)
            if len(valid_data) >= 2:
                early_growth = (valid_data.iloc[1] - valid_data.iloc[0]) / valid_data.iloc[0]
                for i in range(first_valid_idx - 1, -1, -1):
                    if pd.isna(series.iloc[i]):
                        series.iloc[i] = series.iloc[i + 1] / (1 + early_growth * (1 - growth_damping * 0.1))
    
    # Final fallback: linear interpolation
    if series.isna().any():
        series = series.interpolate(method='linear', limit_direction='both', fill_value='extrapolate')
    
    return series


def calculate_growth_stats(
    series: pd.Series,
    current_value: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate growth statistics for a time series.
    
    Args:
        series: Time series data
        current_value: Current value (if None, uses last value)
    
    Returns:
        Dictionary with stats: current, avg, min, max, growth_rate, change_pct
    """
    if len(series) == 0:
        return {
            'current': None,
            'avg': 0.0,
            'min': 0.0,
            'max': 0.0,
            'growth_rate': 0.0,
            'change_pct': 0.0
        }
    
    current = float(current_value) if current_value is not None else float(series.iloc[-1])
    avg = float(series.mean())
    min_val = float(series.min())
    max_val = float(series.max())
    
    # Calculate growth rate (first to last)
    growth_rate = 0.0
    if len(series) > 1 and series.iloc[0] != 0 and not pd.isna(series.iloc[0]):
        growth_rate = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]) * 100
    
    # Calculate change percentage from average
    change_pct = 0.0
    if avg != 0 and not pd.isna(avg):
        change_pct = ((current - avg) / avg) * 100
    
    return {
        'current': current if not pd.isna(current) else None,
        'avg': avg,
        'min': min_val,
        'max': max_val,
        'growth_rate': growth_rate,
        'change_pct': change_pct
    }


def format_dataframe_rows(df: pd.DataFrame, numeric_columns: List[str]) -> List[Dict[str, Any]]:
    """
    Format DataFrame rows to dictionary format for JSON response.
    
    Args:
        df: DataFrame to format
        numeric_columns: List of numeric column names
    
    Returns:
        List of dictionaries
    """
    formatted = []
    for _, row in df.iterrows():
        row_dict = {'year': int(row['year'])}
        for col in numeric_columns:
            if col in df.columns:
                val = row[col]
                row_dict[col] = round(float(val), 2) if pd.notna(val) else None
        formatted.append(row_dict)
    return formatted


def safe_float(value: Any, default: float = 0.0, round_digits: int = 2) -> Optional[float]:
    """
    Safely convert value to float with rounding.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        round_digits: Number of decimal places
    
    Returns:
        Rounded float or None
    """
    try:
        if pd.isna(value) or value is None:
            return None
        return round(float(value), round_digits)
    except (ValueError, TypeError):
        return default if default is not None else None


def calculate_percentage(value: float, total: float) -> float:
    """
    Calculate percentage safely.
    
    Args:
        value: Part value
        total: Total value
    
    Returns:
        Percentage (0-100)
    """
    if total == 0 or pd.isna(total) or pd.isna(value):
        return 0.0
    return round((value / total) * 100, 1)

