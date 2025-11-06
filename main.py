"""
CLI entry point for the Chart Understanding Agent.
"""

import sys
from pathlib import Path
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from src.config import Config
from src.chart_analyzer import ChartAnalyzer
from src.data_extractor import DataExtractor
from src.data_validator import DataValidator


console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Chart Understanding Agent - Extract and analyze data from charts and graphs.
    """
    # Validate configuration
    if not Config.validate():
        console.print("[red]Configuration validation failed. Please check your .env file.[/red]")
        sys.exit(1)


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path for results (JSON)')
@click.option('--csv', help='Export data to CSV file')
@click.option('--validate/--no-validate', default=True, help='Validate extracted data')
def analyze(image_path: str, output: str, csv: str, validate: bool):
    """
    Perform complete chart analysis on an image.
    
    Example: python main.py analyze chart.png --output results.json --csv data.csv
    """
    console.print(Panel.fit(
        f"[bold cyan]Chart Analysis[/bold cyan]\n"
        f"Image: {image_path}",
        border_style="cyan"
    ))
    
    try:
        # Initialize components
        analyzer = ChartAnalyzer()
        extractor = DataExtractor()
        validator = DataValidator()
        
        # Perform analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Analyzing chart...", total=None)
            analysis = analyzer.analyze_chart(image_path)
            progress.update(task, completed=True)
        
        if not analysis:
            console.print("[red]Analysis failed. Check logs for details.[/red]")
            return
        
        # Display results
        _display_analysis_results(analysis)
        
        # Validate if requested
        if validate:
            console.print("\n[yellow]Running validation...[/yellow]")
            report = validator.get_validation_report(analysis)
            console.print(report)
        
        # Save to JSON if output specified
        if output:
            output_path = Path(output)
            extractor.export_to_json(analysis, str(output_path))
            console.print(f"\n[green]✓ Results saved to: {output_path}[/green]")
        
        # Export to CSV if requested
        if csv:
            df = extractor.extract_to_dataframe(analysis["extraction"])
            if df is not None:
                csv_path = Path(csv)
                extractor.export_to_csv(df, str(csv_path))
                console.print(f"[green]✓ Data exported to CSV: {csv_path}[/green]")
            else:
                console.print("[yellow]⚠ Could not convert to CSV[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.exception("Analysis failed")
        sys.exit(1)


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
def detect(image_path: str):
    """
    Detect the chart type in an image.
    
    Example: python main.py detect chart.png
    """
    console.print(Panel.fit(
        f"[bold cyan]Chart Type Detection[/bold cyan]\n"
        f"Image: {image_path}",
        border_style="cyan"
    ))
    
    try:
        analyzer = ChartAnalyzer()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Detecting chart type...", total=None)
            detection = analyzer.detect_chart_type(image_path)
            progress.update(task, completed=True)
        
        if not detection:
            console.print("[red]Detection failed. Check logs for details.[/red]")
            return
        
        # Display detection results
        table = Table(title="Detection Results", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Chart Type", detection.get("chart_type", "unknown"))
        table.add_row("Confidence", f"{detection.get('confidence', 0):.2%}")
        if "orientation" in detection:
            table.add_row("Orientation", detection["orientation"])
        table.add_row("Reasoning", detection.get("reasoning", "N/A"))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.exception("Detection failed")
        sys.exit(1)


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--type', '-t', help='Chart type (auto-detected if not specified)')
@click.option('--output', '-o', help='Output file path (JSON)')
@click.option('--csv', help='Export to CSV file')
def extract(image_path: str, type: str, output: str, csv: str):
    """
    Extract structured data from a chart.
    
    Example: python main.py extract chart.png --type bar_chart --csv data.csv
    """
    console.print(Panel.fit(
        f"[bold cyan]Data Extraction[/bold cyan]\n"
        f"Image: {image_path}",
        border_style="cyan"
    ))
    
    try:
        analyzer = ChartAnalyzer()
        extractor = DataExtractor()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Extracting data...", total=None)
            extraction = analyzer.extract_data(image_path, type)
            progress.update(task, completed=True)
        
        if not extraction:
            console.print("[red]Extraction failed. Check logs for details.[/red]")
            return
        
        # Display extraction results
        console.print("\n[bold green]Extraction Successful![/bold green]")
        console.print(f"Chart Type: {extraction.get('chart_type')}")
        console.print(f"Title: {extraction.get('title', 'N/A')}")
        
        # Generate summary
        summary = extractor.extract_summary(extraction)
        console.print(f"\nData Points: {summary.get('data_point_count', 0)}")
        
        # Save to JSON if output specified
        if output:
            output_path = Path(output)
            extractor.export_to_json(extraction, str(output_path))
            console.print(f"\n[green]✓ Results saved to: {output_path}[/green]")
        
        # Export to CSV if requested
        if csv:
            df = extractor.extract_to_dataframe(extraction)
            if df is not None:
                csv_path = Path(csv)
                extractor.export_to_csv(df, str(csv_path))
                console.print(f"[green]✓ Data exported to CSV: {csv_path}[/green]")
                
                # Display statistics
                stats = extractor.calculate_statistics(df)
                if stats:
                    console.print("\n[bold]Statistics:[/bold]")
                    for col, col_stats in stats.items():
                        console.print(f"\n{col}:")
                        for stat_name, stat_value in col_stats.items():
                            console.print(f"  {stat_name}: {stat_value:.2f}")
            else:
                console.print("[yellow]⚠ Could not convert to CSV[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.exception("Extraction failed")
        sys.exit(1)


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.argument('question')
@click.option('--context', '-c', type=click.Path(exists=True), 
              help='JSON file with context from previous extraction')
def ask(image_path: str, question: str, context: str):
    """
    Ask a specific question about a chart.
    
    Example: python main.py ask chart.png "What is the highest value?"
    """
    console.print(Panel.fit(
        f"[bold cyan]Chart Question Answering[/bold cyan]\n"
        f"Image: {image_path}\n"
        f"Question: {question}",
        border_style="cyan"
    ))
    
    try:
        analyzer = ChartAnalyzer()
        
        # Load context if provided
        context_data = None
        if context:
            with open(context, 'r') as f:
                context_data = json.load(f)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Processing question...", total=None)
            answer = analyzer.answer_question(image_path, question, context_data)
            progress.update(task, completed=True)
        
        if not answer:
            console.print("[red]Failed to answer question. Check logs for details.[/red]")
            return
        
        # Display answer
        console.print("\n[bold green]Answer:[/bold green]")
        console.print(answer.get("answer", "No answer provided"))
        
        console.print("\n[bold]Evidence:[/bold]")
        console.print(answer.get("evidence", "No evidence provided"))
        
        console.print(f"\n[bold]Confidence:[/bold] {answer.get('confidence', 0):.2%}")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.exception("Question answering failed")
        sys.exit(1)


def _display_analysis_results(analysis: dict):
    """Display analysis results in a formatted way."""
    console.print("\n[bold green]Analysis Complete![/bold green]\n")
    
    # Detection results
    detection = analysis.get("detection", {})
    console.print("[bold]Chart Detection:[/bold]")
    console.print(f"  Type: {detection.get('chart_type', 'unknown')}")
    console.print(f"  Confidence: {detection.get('confidence', 0):.2%}")
    
    # Extraction results
    extraction = analysis.get("extraction", {})
    console.print("\n[bold]Data Extraction:[/bold]")
    console.print(f"  Title: {extraction.get('title', 'N/A')}")
    
    chart_type = extraction.get("chart_type")
    if chart_type == "bar_chart":
        data_points = extraction.get("data_points", [])
        console.print(f"  Data Points: {len(data_points)}")
        if data_points:
            console.print("\n  Sample Data:")
            for i, point in enumerate(data_points[:5]):
                console.print(f"    {point.get('category')}: {point.get('value')}")
            if len(data_points) > 5:
                console.print(f"    ... and {len(data_points) - 5} more")
    
    elif chart_type == "line_chart":
        series_list = extraction.get("series", [])
        console.print(f"  Series Count: {len(series_list)}")
        for series in series_list[:3]:
            points = series.get("data_points", [])
            console.print(f"    {series.get('name')}: {len(points)} points")
    
    elif chart_type == "pie_chart":
        segments = extraction.get("segments", [])
        console.print(f"  Segments: {len(segments)}")
        for segment in segments:
            console.print(f"    {segment.get('label')}: {segment.get('percentage')}%")


if __name__ == "__main__":
    cli()