"""
Validation and consistency checking for extracted chart data.
"""

from typing import Dict, List, Any, Optional, Tuple
from loguru import logger


class DataValidator:
    """Validates and checks consistency of extracted chart data."""
    
    def __init__(self, min_confidence: float = 0.7):
        """
        Initialize the DataValidator.
        
        Args:
            min_confidence: Minimum confidence threshold for validation
        """
        self.min_confidence = min_confidence
        logger.info(f"DataValidator initialized with min_confidence={min_confidence}")
    
    def validate_detection(self, detection: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate chart type detection results.
        
        Args:
            detection: Detection result dictionary
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check required fields
        if "chart_type" not in detection:
            issues.append("Missing 'chart_type' field")
        
        if "confidence" not in detection:
            issues.append("Missing 'confidence' field")
        else:
            confidence = detection["confidence"]
            if not isinstance(confidence, (int, float)):
                issues.append("Confidence must be a number")
            elif confidence < 0 or confidence > 1:
                issues.append("Confidence must be between 0 and 1")
            elif confidence < self.min_confidence:
                issues.append(f"Confidence {confidence} below threshold {self.min_confidence}")
        
        # Validate chart type
        valid_types = ["bar_chart", "line_chart", "pie_chart", "scatter_plot", 
                      "area_chart", "combo_chart", "table", "other"]
        if detection.get("chart_type") not in valid_types:
            issues.append(f"Invalid chart type: {detection.get('chart_type')}")
        
        is_valid = len(issues) == 0
        if is_valid:
            logger.info("Detection validation passed")
        else:
            logger.warning(f"Detection validation failed: {issues}")
        
        return is_valid, issues
    
    def validate_extraction(self, extraction: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate extracted chart data.
        
        Args:
            extraction: Extracted data dictionary
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        chart_type = extraction.get("chart_type", "unknown")
        
        logger.info(f"Validating extraction for chart type: {chart_type}")
        
        if chart_type == "bar_chart":
            issues.extend(self._validate_bar_chart(extraction))
        elif chart_type == "line_chart":
            issues.extend(self._validate_line_chart(extraction))
        elif chart_type == "pie_chart":
            issues.extend(self._validate_pie_chart(extraction))
        elif chart_type == "scatter_plot":
            issues.extend(self._validate_scatter_plot(extraction))
        else:
            issues.append(f"Unknown chart type for validation: {chart_type}")
        
        is_valid = len(issues) == 0
        if is_valid:
            logger.info("Extraction validation passed")
        else:
            logger.warning(f"Extraction validation issues: {issues}")
        
        return is_valid, issues
    
    def _validate_bar_chart(self, data: Dict) -> List[str]:
        """Validate bar chart specific data."""
        issues = []
        
        data_points = data.get("data_points", [])
        if not data_points:
            issues.append("No data points found in bar chart")
            return issues
        
        # Check data point structure
        for i, point in enumerate(data_points):
            if not isinstance(point, dict):
                issues.append(f"Data point {i} is not a dictionary")
                continue
            
            if "category" not in point:
                issues.append(f"Data point {i} missing 'category'")
            
            if "value" not in point:
                issues.append(f"Data point {i} missing 'value'")
            elif not isinstance(point["value"], (int, float)):
                issues.append(f"Data point {i} value is not numeric")
        
        # Check for duplicate categories
        categories = [p.get("category") for p in data_points if "category" in p]
        if len(categories) != len(set(categories)):
            issues.append("Duplicate categories found")
        
        return issues
    
    def _validate_line_chart(self, data: Dict) -> List[str]:
        """Validate line chart specific data."""
        issues = []
        
        series_list = data.get("series", [])
        if not series_list:
            issues.append("No series found in line chart")
            return issues
        
        for i, series in enumerate(series_list):
            if not isinstance(series, dict):
                issues.append(f"Series {i} is not a dictionary")
                continue
            
            if "name" not in series:
                issues.append(f"Series {i} missing 'name'")
            
            data_points = series.get("data_points", [])
            if not data_points:
                issues.append(f"Series {i} has no data points")
                continue
            
            # Check data point structure
            for j, point in enumerate(data_points):
                if not isinstance(point, dict):
                    issues.append(f"Series {i}, point {j} is not a dictionary")
                    continue
                
                if "x" not in point or "y" not in point:
                    issues.append(f"Series {i}, point {j} missing x or y coordinate")
        
        return issues
    
    def _validate_pie_chart(self, data: Dict) -> List[str]:
        """Validate pie chart specific data."""
        issues = []
        
        segments = data.get("segments", [])
        if not segments:
            issues.append("No segments found in pie chart")
            return issues
        
        total_percentage = 0
        
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                issues.append(f"Segment {i} is not a dictionary")
                continue
            
            if "label" not in segment:
                issues.append(f"Segment {i} missing 'label'")
            
            if "value" not in segment:
                issues.append(f"Segment {i} missing 'value'")
            elif isinstance(segment["value"], (int, float)):
                total_percentage += segment.get("percentage", segment["value"])
        
        # Check if percentages sum to approximately 100
        if segments and abs(total_percentage - 100) > 5:
            issues.append(f"Percentages sum to {total_percentage}, expected ~100")
        
        return issues
    
    def _validate_scatter_plot(self, data: Dict) -> List[str]:
        """Validate scatter plot specific data."""
        issues = []
        
        data_points = data.get("data_points", [])
        if not data_points:
            issues.append("No data points found in scatter plot")
            return issues
        
        for i, point in enumerate(data_points):
            if not isinstance(point, dict):
                issues.append(f"Data point {i} is not a dictionary")
                continue
            
            if "x" not in point or "y" not in point:
                issues.append(f"Data point {i} missing x or y coordinate")
            
            if "x" in point and not isinstance(point["x"], (int, float)):
                issues.append(f"Data point {i} x-coordinate is not numeric")
            
            if "y" in point and not isinstance(point["y"], (int, float)):
                issues.append(f"Data point {i} y-coordinate is not numeric")
        
        return issues
    
    def check_data_consistency(self, detection: Dict, extraction: Dict) -> Tuple[bool, List[str]]:
        """
        Check consistency between detection and extraction results.
        
        Args:
            detection: Detection result
            extraction: Extraction result
            
        Returns:
            Tuple of (is_consistent, list of issues)
        """
        issues = []
        
        detected_type = detection.get("chart_type")
        extracted_type = extraction.get("chart_type")
        
        if detected_type != extracted_type:
            issues.append(f"Chart type mismatch: detected={detected_type}, extracted={extracted_type}")
        
        is_consistent = len(issues) == 0
        if is_consistent:
            logger.info("Data consistency check passed")
        else:
            logger.warning(f"Consistency issues: {issues}")
        
        return is_consistent, issues
    
    def validate_complete_analysis(self, analysis: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate complete analysis results.
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            Tuple of (is_valid, dictionary of issues by category)
        """
        all_issues = {
            "detection": [],
            "extraction": [],
            "consistency": []
        }
        
        # Validate detection
        if "detection" in analysis:
            _, detection_issues = self.validate_detection(analysis["detection"])
            all_issues["detection"] = detection_issues
        else:
            all_issues["detection"].append("Missing detection results")
        
        # Validate extraction
        if "extraction" in analysis:
            _, extraction_issues = self.validate_extraction(analysis["extraction"])
            all_issues["extraction"] = extraction_issues
        else:
            all_issues["extraction"].append("Missing extraction results")
        
        # Check consistency
        if "detection" in analysis and "extraction" in analysis:
            _, consistency_issues = self.check_data_consistency(
                analysis["detection"],
                analysis["extraction"]
            )
            all_issues["consistency"] = consistency_issues
        
        # Overall validation
        is_valid = all(len(issues) == 0 for issues in all_issues.values())
        
        if is_valid:
            logger.info("Complete analysis validation passed")
        else:
            logger.warning("Complete analysis validation failed")
            for category, issues in all_issues.items():
                if issues:
                    logger.warning(f"{category.upper()} issues: {issues}")
        
        return is_valid, all_issues
    
    def get_validation_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            Formatted validation report string
        """
        is_valid, all_issues = self.validate_complete_analysis(analysis)
        
        report_lines = ["=" * 60, "VALIDATION REPORT", "=" * 60, ""]
        
        if is_valid:
            report_lines.append("✓ All validations passed")
        else:
            report_lines.append("✗ Validation failed")
        
        report_lines.append("")
        
        for category, issues in all_issues.items():
            report_lines.append(f"{category.upper()}:")
            if issues:
                for issue in issues:
                    report_lines.append(f"  ✗ {issue}")
            else:
                report_lines.append("  ✓ No issues")
            report_lines.append("")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)