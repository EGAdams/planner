#!/usr/bin/env python3
"""
Command-line interface for importing bank statements into nonprofit finance database
"""

import click
import sys
import os
from pathlib import Path
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.pipeline import IngestionPipeline, PipelineConfig
from app.config import settings

console = Console()

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--org-id', '-o', type=int, required=True, help='Organization ID')
@click.pass_context
def cli(ctx, verbose, org_id):
    """
    Nonprofit Finance Database - Bank Statement Import Tool

    Import and process bank statements with duplicate detection and validation.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['org_id'] = org_id

    if verbose:
        console.print(f"[bold blue]Organization ID:[/bold blue] {org_id}")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--auto-process', '-a', is_flag=True, default=True,
              help='Automatically process high-confidence duplicates')
@click.option('--dry-run', '-d', is_flag=True, help='Perform dry run without importing')
@click.option('--output-format', '-f', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
@click.pass_context
def import_file(ctx, file_path, auto_process, dry_run, output_format):
    """Import a bank statement file"""

    org_id = ctx.obj['org_id']
    verbose = ctx.obj['verbose']

    if dry_run:
        console.print("[yellow]⚠️  DRY RUN MODE - No data will be imported[/yellow]")

    console.print(f"\n[bold]Importing bank statement file:[/bold] {file_path}")

    try:
        # Initialize pipeline
        pipeline = IngestionPipeline(org_id=org_id)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Start import process
            task = progress.add_task("Processing file...", total=None)

            if not dry_run:
                result = pipeline.ingest_file(file_path, auto_process=auto_process)
            else:
                # For dry run, just validate file and parse
                result = _dry_run_import(pipeline, file_path)

            progress.update(task, completed=True)

        # Display results
        _display_import_results(result, output_format, dry_run)

    except Exception as e:
        console.print(f"[red]❌ Import failed: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--pattern', '-p', default='*.csv', help='File pattern to match')
@click.option('--auto-process', '-a', is_flag=True, default=True)
@click.option('--dry-run', '-d', is_flag=True, help='Perform dry run without importing')
@click.pass_context
def import_directory(ctx, directory, pattern, auto_process, dry_run):
    """Import all bank statement files from a directory"""

    org_id = ctx.obj['org_id']
    verbose = ctx.obj['verbose']

    if dry_run:
        console.print("[yellow]⚠️  DRY RUN MODE - No data will be imported[/yellow]")

    # Find matching files
    directory_path = Path(directory)
    files = list(directory_path.glob(pattern))

    if not files:
        console.print(f"[yellow]No files found matching pattern '{pattern}' in {directory}[/yellow]")
        return

    console.print(f"\n[bold]Found {len(files)} files to import[/bold]")

    # Initialize pipeline
    pipeline = IngestionPipeline(org_id=org_id)

    results = []
    for file_path in files:
        console.print(f"\n[cyan]Processing:[/cyan] {file_path.name}")

        try:
            if not dry_run:
                result = pipeline.ingest_file(str(file_path), auto_process=auto_process)
            else:
                result = _dry_run_import(pipeline, str(file_path))

            result['file_name'] = file_path.name
            results.append(result)

        except Exception as e:
            console.print(f"[red]❌ Failed to process {file_path.name}: {str(e)}[/red]")
            if verbose:
                console.print_exception()

    # Display summary
    _display_batch_results(results, dry_run)

@cli.command()
@click.option('--limit', '-l', type=int, default=20, help='Number of recent imports to show')
@click.option('--status', '-s', type=click.Choice(['ALL', 'COMPLETED', 'FAILED', 'PENDING']),
              default='ALL', help='Filter by status')
@click.pass_context
def history(ctx, limit, status):
    """Show import history"""

    org_id = ctx.obj['org_id']

    try:
        pipeline = IngestionPipeline(org_id=org_id)
        history_records = pipeline.get_import_history(limit=limit)

        if status != 'ALL':
            history_records = [r for r in history_records if r.get('status') == status]

        if not history_records:
            console.print("[yellow]No import history found[/yellow]")
            return

        _display_import_history(history_records)

    except Exception as e:
        console.print(f"[red]❌ Error fetching history: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@click.argument('batch_id', type=int)
@click.pass_context
def retry(ctx, batch_id):
    """Retry a failed import batch"""

    org_id = ctx.obj['org_id']

    try:
        pipeline = IngestionPipeline(org_id=org_id)
        result = pipeline.retry_failed_import(batch_id)

        if result['success']:
            console.print(f"[green]✅ Successfully retried batch {batch_id}[/green]")
        else:
            console.print(f"[red]❌ Failed to retry batch {batch_id}: {result.get('message')}[/red]")

    except Exception as e:
        console.print(f"[red]❌ Error retrying batch: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, file_path):
    """Validate a bank statement file without importing"""

    org_id = ctx.obj['org_id']

    console.print(f"\n[bold]Validating file:[/bold] {file_path}")

    try:
        pipeline = IngestionPipeline(org_id=org_id)

        # Perform validation only
        result = _validate_file_only(pipeline, file_path)
        _display_validation_results(result)

    except Exception as e:
        console.print(f"[red]❌ Validation failed: {str(e)}[/red]")
        sys.exit(1)

def _dry_run_import(pipeline, file_path):
    """Perform a dry run import without saving to database"""

    # Mock the database operations
    original_save_transaction = pipeline._save_transaction
    original_save_duplicate_flags = pipeline._save_duplicate_flags

    pipeline._save_transaction = lambda tx: True  # Mock success
    pipeline._save_duplicate_flags = lambda flags: True  # Mock success

    try:
        result = pipeline.ingest_file(file_path, auto_process=False)
        result['dry_run'] = True
        return result
    finally:
        # Restore original methods
        pipeline._save_transaction = original_save_transaction
        pipeline._save_duplicate_flags = original_save_duplicate_flags

def _validate_file_only(pipeline, file_path):
    """Validate file and parse transactions without processing"""

    from ingestion.validators import FileValidator, TransactionValidator

    file_validator = FileValidator()
    transaction_validator = TransactionValidator()

    result = {
        'file_validation': file_validator.validate_file(file_path),
        'transactions': [],
        'validation_summary': {}
    }

    if result['file_validation']['is_valid']:
        # Parse file
        file_format = pipeline._detect_file_format(file_path)
        if file_format in pipeline.parsers:
            parser = pipeline.parsers[file_format]
            parsed_transactions = parser.parse(file_path)

            # Validate transactions
            validation_result = transaction_validator.validate_batch(parsed_transactions)
            result['transactions'] = validation_result['validated_transactions']
            result['validation_summary'] = validation_result['summary']

    return result

def _display_import_results(result, output_format, dry_run=False):
    """Display import results in specified format"""

    if output_format == 'json':
        # Convert datetime objects to strings for JSON serialization
        json_result = _prepare_for_json(result)
        console.print(json.dumps(json_result, indent=2))
        return

    # Table format
    success_icon = "✅" if result['success'] else "❌"
    status = "DRY RUN" if dry_run else ("SUCCESS" if result['success'] else "FAILED")

    console.print(f"\n[bold]{success_icon} Import {status}[/bold]")

    # Summary table
    table = Table(title="Import Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Transactions", str(result['total_transactions']))
    table.add_row("Successful Imports", str(result['successful_imports']))
    table.add_row("Failed Imports", str(result['failed_imports']))
    table.add_row("Duplicates Found", str(result['duplicate_count']))

    if result.get('validation_errors'):
        table.add_row("Validation Errors", str(len(result['validation_errors'])))

    console.print(table)

    # Show errors if any
    if result.get('validation_errors'):
        console.print("\n[bold red]Validation Errors:[/bold red]")
        for error in result['validation_errors'][:5]:  # Show first 5 errors
            console.print(f"  • {error}")

    # Show duplicate report
    if result.get('duplicate_report') and result['duplicate_report']['total_duplicates'] > 0:
        _display_duplicate_report(result['duplicate_report'])

def _display_batch_results(results, dry_run=False):
    """Display results from batch import"""

    total_files = len(results)
    successful_files = len([r for r in results if r['success']])
    total_transactions = sum(r['total_transactions'] for r in results)
    total_imports = sum(r['successful_imports'] for r in results)

    status = "DRY RUN SUMMARY" if dry_run else "BATCH IMPORT SUMMARY"

    console.print(f"\n[bold cyan]{status}[/bold cyan]")

    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Files Processed", str(total_files))
    summary_table.add_row("Successful Files", str(successful_files))
    summary_table.add_row("Total Transactions", str(total_transactions))
    summary_table.add_row("Total Imports", str(total_imports))

    console.print(summary_table)

    # Detailed results
    if results:
        console.print("\n[bold]File Details:[/bold]")
        detail_table = Table(show_header=True, header_style="bold magenta")
        detail_table.add_column("File", style="cyan")
        detail_table.add_column("Status", style="green")
        detail_table.add_column("Transactions", justify="right")
        detail_table.add_column("Imports", justify="right")
        detail_table.add_column("Duplicates", justify="right")

        for result in results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            detail_table.add_row(
                result['file_name'],
                status,
                str(result['total_transactions']),
                str(result['successful_imports']),
                str(result['duplicate_count'])
            )

        console.print(detail_table)

def _display_import_history(history_records):
    """Display import history"""

    console.print(f"\n[bold cyan]Import History[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", justify="right")
    table.add_column("File", style="cyan")
    table.add_column("Date", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Transactions", justify="right")
    table.add_column("Success Rate", justify="right")

    for record in history_records:
        status_icon = {
            'COMPLETED': '✅',
            'FAILED': '❌',
            'PENDING': '⏳',
            'PROCESSING': '🔄'
        }.get(record.get('status', 'UNKNOWN'), '❓')

        success_rate = f"{record.get('success_rate', 0):.1f}%"

        table.add_row(
            str(record.get('batch_id', '')),
            record.get('filename', ''),
            record.get('import_date', '').strftime('%Y-%m-%d %H:%M') if record.get('import_date') else '',
            f"{status_icon} {record.get('status', 'UNKNOWN')}",
            str(record.get('total_transactions', 0)),
            success_rate
        )

    console.print(table)

def _display_duplicate_report(duplicate_report):
    """Display duplicate detection report"""

    console.print("\n[bold yellow]Duplicate Detection Report[/bold yellow]")

    dup_table = Table(show_header=True, header_style="bold magenta")
    dup_table.add_column("Confidence Level", style="cyan")
    dup_table.add_column("Count", justify="right", style="yellow")

    dup_table.add_row("High (≥95%)", str(duplicate_report['high_confidence']))
    dup_table.add_row("Medium (80-95%)", str(duplicate_report['medium_confidence']))
    dup_table.add_row("Low (<80%)", str(duplicate_report['low_confidence']))
    dup_table.add_row("Total", str(duplicate_report['total_duplicates']))

    console.print(dup_table)

def _display_validation_results(result):
    """Display validation results"""

    file_validation = result['file_validation']

    if file_validation['is_valid']:
        console.print("[green]✅ File validation passed[/green]")
    else:
        console.print("[red]❌ File validation failed[/red]")
        for error in file_validation['errors']:
            console.print(f"  • {error}")
        return

    if result['transactions']:
        console.print(f"\n[green]✅ Parsed {len(result['transactions'])} valid transactions[/green]")

        validation_summary = result['validation_summary']
        console.print(f"Valid: {validation_summary['valid_transactions']}")
        console.print(f"Invalid: {validation_summary['invalid_transactions']}")
    else:
        console.print("[yellow]⚠️  No valid transactions found[/yellow]")

def _prepare_for_json(obj):
    """Prepare object for JSON serialization by converting datetime objects"""
    if isinstance(obj, dict):
        return {k: _prepare_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_prepare_for_json(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

if __name__ == '__main__':
    cli()