"""
Extract and structure data from chart analysis results.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from loguru import logger


class DataExtractor:
    """Handles extraction and structuring of chart data."""
    
    def __init__(self):
        """Initialize the DataExtractor."""
        logger.info("DataExtractor initialized")
    
    def extract_to_dataframe(self, chart_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Convert extracted chart data to pandas DataFrame.
        
        Args:
            chart_data: Extracted chart data dictionary
            
        Returns:
            DataFrame or None if conversion fails
        """
        try:
            chart_type = chart_data.get("chart_type", "unknown")
            logger.info(f"Converting {chart_type} data to DataFrame")
            
            if chart_type == "bar_chart":
                return self._bar_chart_to_df(chart_data)
            elif chart_type == "line_chart":
                return self._line_chart_to_df(chart_data)
            elif chart_type == "pie_chart":
                return self._pie_chart_to_df(chart_data)
            elif chart_type == "scatter_plot":
                return self._scatter_plot_to_df(chart_data)
            else:
                logger.warning(f"Unknown chart type: {chart_type}")
                return self._generic_to_df(chart_data)
                
        except Exception as e:
            logger.error(f"Failed to convert to DataFrame: {str(e)}")
            return None
    
    def _bar_chart_to_df(self, data: Dict) -> pd.DataFrame:
        """Convert bar chart data to DataFrame."""
        data_points = data.get("data_points", [])
        df = pd.DataFrame(data_points)
        
        # Add metadata
        df.attrs["title"] = data.get("title", "")
        df.attrs["x_label"] = data.get("x_axis_label", "")
        df.attrs["y_label"] = data.get("y_axis_label", "")
        df.attrs["unit"] = data.get("unit", "")
        
        logger.debug(f"Created bar chart DataFrame with {len(df)} rows")
        return df
    
    def _line_chart_to_df(self, data: Dict) -> pd.DataFrame:
        """Convert line chart data to DataFrame."""
        series_list = data.get("series", [])
        
        if not series_list:
            return pd.DataFrame()
        
        # Create multi-series DataFrame
        dfs = []
        for series in series_list:
            series_name = series.get("name", "Series")
            points = series.get("data_points", [])
            
            df_temp = pd.DataFrame(points)
            df_temp["series"] = series_name
            dfs.append(df_temp)
        
        df = pd.concat(dfs, ignore_index=True)
        
        # Add metadata
        df.attrs["title"] = data.get("title", "")
        df.attrs["x_label"] = data.get("x_axis_label", "")
        df.attrs["y_label"] = data.get("y_axis_label", "")
        
        logger.debug(f"Created line chart DataFrame with {len(df)} rows")
        return df
    
    def _pie_chart_to_df(self, data: Dict) -> pd.DataFrame:
        """Convert pie chart data to DataFrame."""
        segments = data.get("segments", [])
        df = pd.DataFrame(segments)
        
        # Add metadata
        df.attrs["title"] = data.get("title", "")
        df.attrs["total"] = data.get("total", 100)
        df.attrs["unit"] = data.get("unit", "")
        
        logger.debug(f"Created pie chart DataFrame with {len(df)} rows")
        return df
    
    def _scatter_plot_to_df(self, data: Dict) -> pd.DataFrame:
        """Convert scatter plot data to DataFrame."""
        data_points = data.get("data_points", [])
        df = pd.DataFrame(data_points)
        
        # Add metadata
        df.attrs["title"] = data.get("title", "")
        df.attrs["x_label"] = data.get("x_axis_label", "")
        df.attrs["y_label"] = data.get("y_axis_label", "")
        df.attrs["correlation"] = data.get("correlation", "")
        
        logger.debug(f"Created scatter plot DataFrame with {len(df)} rows")
        return df
    
    def _generic_to_df(self, data: Dict) -> pd.DataFrame:
        """Generic conversion for unknown chart types."""
        # Try to find any list of data points
        for key, value in data.items():
            if isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    return pd.DataFrame(value)
        
        logger.warning("Could not find suitable data for DataFrame conversion")
        return pd.DataFrame()
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate basic statistics from DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary of statistics
        """
        try:
            stats = {}
            
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            for col in numeric_cols:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "sum": float(df[col].sum()),
                    "count": int(df[col].count())
                }
            
            logger.debug(f"Calculated statistics for {len(numeric_cols)} columns")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {str(e)}")
            return {}
    
    def extract_summary(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a summary of the chart data.
        
        Args:
            chart_data: Extracted chart data
            
        Returns:
            Summary dictionary
        """
        try:
            summary = {
                "chart_type": chart_data.get("chart_type", "unknown"),
                "title": chart_data.get("title", "Untitled"),
                "data_point_count": 0,
                "key_metrics": {}
            }
            
            chart_type = summary["chart_type"]
            
            if chart_type == "bar_chart":
                data_points = chart_data.get("data_points", [])
                summary["data_point_count"] = len(data_points)
                if data_points:
                    values = [dp.get("value", 0) for dp in data_points]
                    summary["key_metrics"] = {
                        "highest": max(values),
                        "lowest": min(values),
                        "average": sum(values) / len(values)
                    }
            
            elif chart_type == "line_chart":
                series_list = chart_data.get("series", [])
                summary["series_count"] = len(series_list)
                total_points = sum(len(s.get("data_points", [])) for s in series_list)
                summary["data_point_count"] = total_points
            
            elif chart_type == "pie_chart":
                segments = chart_data.get("segments", [])
                summary["data_point_count"] = len(segments)
                summary["total"] = chart_data.get("total", 100)
            
            logger.info(f"Generated summary for {chart_type}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to extract summary: {str(e)}")
            return {}
    
    def export_to_csv(self, df: pd.DataFrame, output_path: str) -> bool:
        """
        Export DataFrame to CSV file.
        
        Args:
            df: DataFrame to export
            output_path: Path for output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            df.to_csv(output_path, index=False)
            logger.info(f"Exported data to CSV: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            return False
    
    def export_to_json(self, data: Dict, output_path: str) -> bool:
        """
        Export data to JSON file.
        
        Args:
            data: Data dictionary to export
            output_path: Path for output JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported data to JSON: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export JSON: {str(e)}")
            return False