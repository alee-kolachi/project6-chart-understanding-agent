"""
Prompt templates for different chart types and analysis tasks.
"""

from typing import Dict


class PromptTemplates:
    """Collection of prompt templates for chart analysis."""
    
    CHART_TYPE_DETECTION = """You are an expert at analyzing charts and graphs. 
Analyze this image and determine the chart type.

Possible types:
- bar_chart (vertical or horizontal bars)
- line_chart (line plot with trends)
- pie_chart (circular chart with segments)
- scatter_plot (points on x-y axis)
- area_chart (filled area under line)
- combo_chart (combination of multiple types)
- table (data table)
- other (if none of the above)

Respond with ONLY a JSON object in this exact format:
{{
    "chart_type": "bar_chart",
    "confidence": 0.95,
    "orientation": "vertical",
    "reasoning": "Clear vertical bars with x-axis labels"
}}"""

    BAR_CHART_EXTRACTION = """You are analyzing a bar chart. Extract ALL data points with high precision.

Instructions:
1. Identify the x-axis labels (categories)
2. Read the y-axis values for each bar
3. Note the axis titles and units
4. Extract the chart title if present

Respond with ONLY a JSON object in this exact format:
{{
    "title": "Chart title here",
    "x_axis_label": "X axis label",
    "y_axis_label": "Y axis label",
    "unit": "unit of measurement",
    "data_points": [
        {{"category": "Category 1", "value": 45.5}},
        {{"category": "Category 2", "value": 32.1}}
    ],
    "notes": "Any additional observations"
}}"""

    LINE_CHART_EXTRACTION = """You are analyzing a line chart. Extract ALL data points and trends.

Instructions:
1. Identify all lines/series in the chart
2. Extract data points for each line
3. Note axis labels, titles, and units
4. Identify any trends or patterns

Respond with ONLY a JSON object in this exact format:
{{
    "title": "Chart title here",
    "x_axis_label": "X axis label",
    "y_axis_label": "Y axis label",
    "unit": "unit of measurement",
    "series": [
        {{
            "name": "Series 1",
            "data_points": [
                {{"x": "Jan", "y": 100}},
                {{"x": "Feb", "y": 120}}
            ]
        }}
    ],
    "trends": "Description of trends",
    "notes": "Any additional observations"
}}"""

    PIE_CHART_EXTRACTION = """You are analyzing a pie chart. Extract ALL segments with their values.

Instructions:
1. Identify all segments/slices
2. Extract the percentage or value for each segment
3. Note the chart title
4. Identify the total if shown

Respond with ONLY a JSON object in this exact format:
{{
    "title": "Chart title here",
    "total": 100,
    "unit": "percentage or absolute value",
    "segments": [
        {{"label": "Segment 1", "value": 35.5, "percentage": 35.5}},
        {{"label": "Segment 2", "value": 25.0, "percentage": 25.0}}
    ],
    "notes": "Any additional observations"
}}"""

    SCATTER_PLOT_EXTRACTION = """You are analyzing a scatter plot. Extract data points and patterns.

Instructions:
1. Sample key data points (if too many, sample representative ones)
2. Identify any clusters or patterns
3. Note axis labels, titles, and units
4. Describe the correlation if visible

Respond with ONLY a JSON object in this exact format:
{{
    "title": "Chart title here",
    "x_axis_label": "X axis label",
    "y_axis_label": "Y axis label",
    "data_points": [
        {{"x": 10, "y": 20}},
        {{"x": 15, "y": 25}}
    ],
    "correlation": "positive/negative/none",
    "clusters": "Description of any clusters",
    "notes": "Any additional observations"
}}"""

    GENERAL_QUESTION = """You are analyzing a chart/graph to answer a specific question.

Chart context: {context}

Question: {question}

Provide a clear, concise answer based on the visual data. If you need to make calculations, show your work.
Include specific numbers and references to the chart elements.

Respond with ONLY a JSON object in this exact format:
{{
    "answer": "Your detailed answer here",
    "evidence": "Specific data points or visual elements that support your answer",
    "confidence": 0.95
}}"""

    @classmethod
    def get_extraction_prompt(cls, chart_type: str) -> str:
        """Get the appropriate extraction prompt for a chart type."""
        prompt_map = {
            "bar_chart": cls.BAR_CHART_EXTRACTION,
            "line_chart": cls.LINE_CHART_EXTRACTION,
            "pie_chart": cls.PIE_CHART_EXTRACTION,
            "scatter_plot": cls.SCATTER_PLOT_EXTRACTION,
        }
        return prompt_map.get(chart_type, cls.BAR_CHART_EXTRACTION)
    
    @classmethod
    def format_question_prompt(cls, context: str, question: str) -> str:
        """Format a question prompt with context."""
        return cls.GENERAL_QUESTION.format(context=context, question=question)