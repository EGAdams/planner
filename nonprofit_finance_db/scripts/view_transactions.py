#!/usr/bin/env python3
"""
Enhanced CLI Dashboard for viewing transaction data

Usage:
    python scripts/view_transactions.py [options]

Features:
    - Interactive filtering and search
    - Summary statistics
    - Pagination
    - Export capabilities
    - Rich terminal formatting
"""

import sys
import os
import argparse
import json
import csv
import subprocess
import socket
import shutil
import time
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich import box

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mysql.connector import Error as MySQLError
from app.config import settings
from app.db import get_connection

class DatabaseManager:
    """Utility wrapper for managing the local MySQL service from the dashboard."""

    def __init__(self, console):
        self.console = console
        self.base_dir = Path(__file__).resolve().parent.parent
        default_data_dir = self.base_dir / "tmp_mysql"
        self.data_dir = Path(os.getenv("LOCAL_MYSQL_DATA_DIR", default_data_dir))
        self.socket_path = Path(os.getenv("LOCAL_MYSQL_SOCKET", self.data_dir / "mysql.sock"))
        self.error_log = Path(os.getenv("LOCAL_MYSQL_LOG", self.data_dir / "error.log"))
        self.pid_file = Path(os.getenv("LOCAL_MYSQL_PID", self.data_dir / "mysql.pid"))
        self.bind_address = os.getenv("LOCAL_MYSQL_BIND_ADDRESS", "127.0.0.1")
        self.host = settings.host
        self.port = settings.port
        self.user = settings.user
        self.password = settings.password
        self.database = settings.database
        self._user_port_override = "DB_PORT" in os.environ
        self.mysqld = shutil.which("mysqld")
        self.mysqladmin = shutil.which("mysqladmin")
        self.mysql_client = shutil.which("mysql")
        self._last_process: Optional[subprocess.Popen] = None

    def supports_local_control(self) -> bool:
        """Return True when local start/stop controls are available."""
        return self.host in ("127.0.0.1", "localhost") and self.mysqld is not None and self.mysqladmin is not None

    def _socket_exists(self) -> bool:
        try:
            return self.socket_path.exists()
        except OSError:
            return False

    def _mysqladmin_base(self) -> Optional[List[str]]:
        if not self.mysqladmin:
            return None

        cmd: List[str] = [self.mysqladmin, "--no-defaults"]
        if self._socket_exists():
            cmd.append(f"--socket={self.socket_path}")
        else:
            cmd.append(f"--host={self.host}")
            cmd.append(f"--port={self.port}")
        cmd.append(f"--user={self.user}")
        if self.password:
            cmd.append(f"--password={self.password}")
        return cmd

    def _mysql_client_base(self) -> Optional[List[str]]:
        if not self.mysql_client:
            return None

        cmd: List[str] = [self.mysql_client, "--no-defaults"]
        if self._socket_exists():
            cmd.append(f"--socket={self.socket_path}")
        else:
            cmd.append(f"--host={self.host}")
            cmd.append(f"--port={self.port}")
        cmd.append(f"--user={self.user}")
        if self.password:
            cmd.append(f"--password={self.password}")
        return cmd

    def get_status(self) -> Dict[str, Any]:
        """Return current server status and management availability."""
        status: Dict[str, Any] = {
            "running": False,
            "message": "",
            "manageable": self.supports_local_control(),
            "host": self.host,
            "port": self.port,
        }

        base_cmd = self._mysqladmin_base()
        if not base_cmd:
            status["message"] = "mysqladmin not found; status unavailable"
            status["manageable"] = False
            return status

        try:
            result = subprocess.run(
                base_cmd + ["ping"],
                capture_output=True,
                text=True,
                timeout=3,
            )
        except FileNotFoundError:
            status["message"] = "mysqladmin not available on PATH"
            status["manageable"] = False
            return status
        except subprocess.TimeoutExpired:
            status["message"] = "Ping timed out"
            return status

        if result.returncode == 0 and "alive" in result.stdout.lower():
            status["running"] = True
            status["message"] = result.stdout.strip() or "Server responding"
        else:
            status["message"] = (result.stderr or result.stdout or "Server not responding").strip()

        return status

    def _ensure_data_dir(self) -> Tuple[bool, str]:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return False, f"Unable to create data directory {self.data_dir}: {exc}"

        if not (self.data_dir / "mysql").exists():
            init_cmd = [
                self.mysqld,
                "--initialize-insecure",
                f"--datadir={self.data_dir}",
                f"--log-error={self.error_log}",
            ]
            init_result = subprocess.run(init_cmd, capture_output=True, text=True)
            if init_result.returncode != 0:
                message = (init_result.stderr or init_result.stdout or "Unknown error").strip()
                return False, f"Failed to initialize data directory: {message}"
        return True, ""

    def _port_in_use(self, port: int) -> bool:
        """Return True when a listener is already bound to the requested port."""
        hosts = {self.bind_address, "127.0.0.1", "localhost"}
        for host in hosts:
            if not host:
                continue
            try:
                with socket.create_connection((host, port), timeout=0.5):
                    return True
            except OSError:
                continue
        return False

    def _find_available_port(self, start: int, end: int) -> Optional[int]:
        """Locate an available port between start and end (inclusive)."""
        for candidate in range(start, end + 1):
            if not self._port_in_use(candidate):
                return candidate
        return None

    def _apply_runtime_port(self, new_port: int) -> None:
        """Adjust settings and connection pool to use a newly-selected port."""
        import app.config as config_module  # Local import to avoid cycles

        self.port = new_port
        os.environ["DB_PORT"] = str(new_port)
        config_module.settings = config_module.Settings()

        global settings
        settings = config_module.settings

        # Ensure subsequent connections use refreshed settings.
        try:
            from app.db import pool as pool_module

            pool_module.settings = config_module.settings
            pool_module._pool = None  # type: ignore[attr-defined]
        except ImportError:
            pass

        # Keep manager credentials aligned with refreshed settings.
        self.host = settings.host
        self.user = settings.user
        self.password = settings.password
        self.database = settings.database

    def _escape_sql_literal(self, value: str) -> str:
        """Escape single quotes and backslashes for insertion into SQL literal."""
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def _ensure_user_credentials(self) -> Optional[str]:
        """Align local MySQL credentials with dashboard settings when using root."""
        if not self.supports_local_control():
            return None

        client_cmd = self._mysql_client_base()
        if not client_cmd:
            return None

        if self.user != "root":
            return None

        check = subprocess.run(
            client_cmd + ["-N", "-e", "SELECT plugin FROM mysql.user WHERE user='root' AND host='localhost';"],
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            return None

        plugin = check.stdout.strip()
        desired_plugin = "mysql_native_password"
        if plugin == desired_plugin:
            return None

        escaped_password = self._escape_sql_literal(self.password or "")
        alter_stmt = (
            f"ALTER USER 'root'@'localhost' IDENTIFIED WITH {desired_plugin} BY '{escaped_password}';"
        )
        alter = subprocess.run(
            client_cmd + ["-e", alter_stmt],
            capture_output=True,
            text=True,
        )
        if alter.returncode != 0:
            return None

        subprocess.run(
            client_cmd + ["-e", "FLUSH PRIVILEGES;"],
            capture_output=True,
            text=True,
        )
        return "Updated root authentication plugin for local dashboard access."

    def start_server(self) -> Tuple[bool, str]:
        if not self.supports_local_control():
            return False, "Start controls are only available for a local MySQL install (mysqld/mysqladmin required)."

        status = self.get_status()
        if status["running"]:
            return False, "Server is already running."

        notes: List[str] = []
        if self._port_in_use(self.port):
            if self._user_port_override:
                return False, (
                    f"Port {self.port} is already in use. Stop the other MySQL service or set DB_PORT to a free port."
                )
            candidate = self._find_available_port(self.port + 1, self.port + 20)
            if candidate is None:
                return False, (
                    f"Port {self.port} is in use and no fallback ports are available nearby. "
                    "Set DB_PORT to a custom value and retry."
                )
            previous_port = self.port
            self._apply_runtime_port(candidate)
            notes.append(f"Port {previous_port} busy; switched to {candidate}.")

        ok, message = self._ensure_data_dir()
        if not ok:
            return False, message

        start_cmd = [
            self.mysqld,
            f"--datadir={self.data_dir}",
            f"--socket={self.socket_path}",
            f"--port={self.port}",
            f"--bind-address={self.bind_address}",
            f"--log-error={self.error_log}",
            f"--pid-file={self.pid_file}",
            "--skip-mysqlx",
        ]
        try:
            self._last_process = subprocess.Popen(
                start_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            return False, f"Failed to start mysqld: {exc}"

        for _ in range(30):
            time.sleep(1)
            current = self.get_status()
            if current["running"]:
                cred_note = self._ensure_user_credentials()
                if cred_note:
                    notes.append(cred_note)
                success_message = "MySQL server started successfully."
                if notes:
                    success_message = " ".join(notes + [success_message])
                return True, success_message
            if self._last_process and self._last_process.poll() is not None:
                break

        failure_message = f"Server did not report ready. Check log at {self.error_log}"
        if notes:
            failure_message = " ".join(notes + [failure_message])
        return False, failure_message

    def stop_server(self) -> Tuple[bool, str]:
        if not self.supports_local_control():
            return False, "Stop controls are only available for the local server."

        status = self.get_status()
        if not status["running"]:
            return False, "Server is already stopped."

        base_cmd = self._mysqladmin_base()
        if not base_cmd:
            return False, "mysqladmin unavailable; cannot stop server."

        try:
            result = subprocess.run(
                base_cmd + ["shutdown"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return False, "Shutdown request timed out."

        if result.returncode != 0:
            message = (result.stderr or result.stdout or "Unknown error").strip()
            return False, f"Shutdown failed: {message}"

        for _ in range(20):
            time.sleep(0.5)
            if not self.get_status()["running"]:
                return True, "MySQL server stopped."

        return True, "Shutdown requested; awaiting server exit."

    def initialize_schema(self) -> Tuple[bool, str]:
        status = self.get_status()
        if not status["running"]:
            return False, "Database server must be running before initializing the schema."

        cmd = [sys.executable, "scripts/init_db.py"]
        env = self._db_env()

        result = subprocess.run(
            cmd,
            cwd=self.base_dir,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            output_lines = [result.stdout.strip() or "Database initialized."]

            client_cmd = self._mysql_client_base()
            schema_path = self.base_dir / "transaction_schema.sql"
            if client_cmd and schema_path.exists():
                with schema_path.open("r") as schema_file:
                    schema_result = subprocess.run(
                        client_cmd + [self.database],
                        cwd=self.base_dir,
                        env=env,
                        stdin=schema_file,
                        capture_output=True,
                        text=True,
                    )
                if schema_result.returncode != 0:
                    message = (schema_result.stderr or schema_result.stdout or "Unknown error").strip()
                    return False, f"Applying transaction schema failed: {message}"
                output_lines.append("Applied transaction schema.")
            elif not schema_path.exists():
                output_lines.append(f"⚠️ transaction_schema.sql not found at {schema_path}.")
            else:
                output_lines.append("⚠️ mysql client not available; transaction schema not applied.")

            return True, " ".join(line for line in output_lines if line)

        combined = (result.stdout + result.stderr).strip()
        return False, f"init_db.py failed:\n{combined}"

    def load_demo_data(self) -> Tuple[bool, str]:
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM transactions WHERE bank_reference LIKE 'DASH-%'")
                    sample_rows = [
                        (1, "2025-01-05", 150.25, "Donation from local sponsor", "CREDIT", "1111", "DASH-001", 5150.25),
                        (1, "2025-01-08", -75.00, "Office supplies purchase", "DEBIT", "1111", "DASH-002", 5075.25),
                        (1, "2025-01-12", -200.00, "Rent payment", "DEBIT", "1111", "DASH-003", 4875.25),
                        (1, "2025-01-20", 500.00, "Grant disbursement", "CREDIT", "1111", "DASH-004", 5375.25),
                        (1, "2025-01-25", -120.75, "Community event expenses", "DEBIT", "1111", "DASH-005", 5254.50),
                    ]
                    insert_sql = """
                        INSERT INTO transactions (
                            org_id, transaction_date, amount, description, transaction_type,
                            account_number, bank_reference, balance_after
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.executemany(insert_sql, sample_rows)
                    conn.commit()
            return True, f"Loaded {len(sample_rows)} demo transactions."
        except Exception as exc:
            return False, f"Failed to load demo data: {exc}"

    def purge_data_directory(self) -> Tuple[bool, str]:
        if not self.supports_local_control():
            return False, "Reset is only available for the managed local server."

        if not self.data_dir.exists():
            return False, f"No data directory found at {self.data_dir}"

        status = self.get_status()
        if status["running"]:
            success, message = self.stop_server()
            if not success:
                return False, f"Unable to stop server before cleanup: {message}"

        try:
            resolved = self.data_dir.resolve()
            if not resolved.is_relative_to(self.base_dir):
                return False, f"Refusing to remove directory outside project: {resolved}"
        except AttributeError:
            resolved = self.data_dir.resolve()
            if str(self.base_dir) not in str(resolved):
                return False, f"Refusing to remove directory outside project: {resolved}"

        try:
            shutil.rmtree(self.data_dir)
        except Exception as exc:
            return False, f"Failed to remove data directory: {exc}"

        return True, f"Removed data directory at {self.data_dir}"

    def _db_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env["DB_HOST"] = self.host
        env["DB_PORT"] = str(self.port)
        env["NON_PROFIT_USER"] = self.user
        env["NON_PROFIT_PASSWORD"] = self.password
        env["NON_PROFIT_DB_NAME"] = self.database

        pythonpath = env.get("PYTHONPATH", "")
        paths = [p for p in pythonpath.split(os.pathsep) if p]
        base_str = str(self.base_dir)
        if base_str not in paths:
            paths.insert(0, base_str)
        env["PYTHONPATH"] = os.pathsep.join(paths)
        return env

    def build_controls_panel(self, status: Optional[Dict[str, Any]] = None) -> Optional[Panel]:
        status = status or self.get_status()
        indicator = "[green]● RUNNING[/green]" if status["running"] else "[red]● STOPPED[/red]"
        host_info = f"{status['host']}:{status['port']}"
        message = status.get("message", "")
        if len(message) > 60:
            message = message[:57] + "..."

        table = Table(show_header=False, box=box.SIMPLE, pad_edge=True)
        table.add_column("Key", style="bold cyan", width=12)
        table.add_column("Action", style="white")

        table.add_row("Status", f"{indicator}  [dim]{host_info}[/dim]")
        if message:
            table.add_row("", f"[dim]{message}[/dim]")

        table.add_row("[1]", "Start local MySQL server")
        table.add_row("[2]", "Stop local MySQL server")
        table.add_row("[3]", "Rebuild schema (drops & recreates DB)")
        table.add_row("[4]", "Load demo transactions")

        if status["manageable"]:
            table.add_row("[5]", "Stop & remove local data directory")
        else:
            table.add_row("", "[dim]Local start/stop controls unavailable[/dim]")

        return Panel(
            table,
            title="⚙️  System Controls",
            border_style="magenta",
        )

class TransactionViewer:
    """Enhanced transaction data viewer with CLI interface"""

    def __init__(self, org_id: int = 1):
        self.org_id = org_id
        self.page_size = 20
        self.current_page = 1
        self.filters = {}
        self.sort_by = 'transaction_date'
        self.sort_order = 'DESC'
        self.console = Console()
        self.db_manager = DatabaseManager(self.console)

    def get_transactions(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get transactions with current filters and pagination"""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = ["org_id = %s"]
            params = [self.org_id]

            if self.filters.get('start_date'):
                where_conditions.append("transaction_date >= %s")
                params.append(self.filters['start_date'])

            if self.filters.get('end_date'):
                where_conditions.append("transaction_date <= %s")
                params.append(self.filters['end_date'])

            if self.filters.get('transaction_type'):
                where_conditions.append("transaction_type = %s")
                params.append(self.filters['transaction_type'])

            if self.filters.get('min_amount'):
                where_conditions.append("amount >= %s")
                params.append(self.filters['min_amount'])

            if self.filters.get('max_amount'):
                where_conditions.append("amount <= %s")
                params.append(self.filters['max_amount'])

            if self.filters.get('search'):
                where_conditions.append("description LIKE %s")
                params.append(f"%{self.filters['search']}%")

            if self.filters.get('account_number'):
                where_conditions.append("account_number = %s")
                params.append(self.filters['account_number'])

            where_clause = " AND ".join(where_conditions)

            # Build ORDER BY clause
            order_clause = f"ORDER BY {self.sort_by} {self.sort_order}"

            # Build LIMIT clause
            limit_clause = ""
            if limit:
                limit_clause = f"LIMIT {limit}"
                if offset > 0:
                    limit_clause += f" OFFSET {offset}"

            query = f"""
            SELECT id, transaction_date, amount, description, transaction_type,
                   account_number, bank_reference, balance_after, import_batch_id,
                   created_at
            FROM transactions
            WHERE {where_clause}
            {order_clause}
            {limit_clause}
            """

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]

            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_transaction_count(self) -> int:
        """Get total count of transactions matching current filters"""
        with get_connection() as conn:
            cursor = conn.cursor()

            where_conditions = ["org_id = %s"]
            params = [self.org_id]

            if self.filters.get('start_date'):
                where_conditions.append("transaction_date >= %s")
                params.append(self.filters['start_date'])

            if self.filters.get('end_date'):
                where_conditions.append("transaction_date <= %s")
                params.append(self.filters['end_date'])

            if self.filters.get('transaction_type'):
                where_conditions.append("transaction_type = %s")
                params.append(self.filters['transaction_type'])

            if self.filters.get('min_amount'):
                where_conditions.append("amount >= %s")
                params.append(self.filters['min_amount'])

            if self.filters.get('max_amount'):
                where_conditions.append("amount <= %s")
                params.append(self.filters['max_amount'])

            if self.filters.get('search'):
                where_conditions.append("description LIKE %s")
                params.append(f"%{self.filters['search']}%")

            if self.filters.get('account_number'):
                where_conditions.append("account_number = %s")
                params.append(self.filters['account_number'])

            where_clause = " AND ".join(where_conditions)

            query = f"SELECT COUNT(*) FROM transactions WHERE {where_clause}"
            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for current filtered data"""
        with get_connection() as conn:
            cursor = conn.cursor()

            where_conditions = ["org_id = %s"]
            params = [self.org_id]

            if self.filters.get('start_date'):
                where_conditions.append("transaction_date >= %s")
                params.append(self.filters['start_date'])

            if self.filters.get('end_date'):
                where_conditions.append("transaction_date <= %s")
                params.append(self.filters['end_date'])

            if self.filters.get('transaction_type'):
                where_conditions.append("transaction_type = %s")
                params.append(self.filters['transaction_type'])

            if self.filters.get('min_amount'):
                where_conditions.append("amount >= %s")
                params.append(self.filters['min_amount'])

            if self.filters.get('max_amount'):
                where_conditions.append("amount <= %s")
                params.append(self.filters['max_amount'])

            if self.filters.get('search'):
                where_conditions.append("description LIKE %s")
                params.append(f"%{self.filters['search']}%")

            if self.filters.get('account_number'):
                where_conditions.append("account_number = %s")
                params.append(self.filters['account_number'])

            where_clause = " AND ".join(where_conditions)

            # Get overall stats
            query = f"""
            SELECT
                COUNT(*) as total_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount,
                MIN(transaction_date) as earliest_date,
                MAX(transaction_date) as latest_date
            FROM transactions
            WHERE {where_clause}
            """

            cursor.execute(query, params)
            stats = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))

            # Get breakdown by type
            type_query = f"""
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
            FROM transactions
            WHERE {where_clause}
            GROUP BY transaction_type
            """

            cursor.execute(type_query, params)
            type_breakdown = {}
            for row in cursor.fetchall():
                type_breakdown[row[0]] = {'count': row[1], 'total': float(row[2]) if row[2] else 0}

            stats['type_breakdown'] = type_breakdown
            return stats

    def print_header(self):
        """Print application header with Rich formatting"""
        header_text = Text("🏦 TRANSACTION VIEWER DASHBOARD", style="bold bright_white")
        header_panel = Panel(
            Align.center(header_text),
            style="bold bright_blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(header_panel)

    def print_system_controls(self, status: Optional[Dict[str, Any]] = None):
        """Render database/system control panel with status indicator."""
        panel = self.db_manager.build_controls_panel(status=status)
        if panel:
            self.console.print(panel)

    def handle_system_action(self, choice: str) -> bool:
        """Execute system-level action based on the choice key."""
        actions = {
            '1': {
                "label": "Start local MySQL server",
                "fn": self.db_manager.start_server,
                "confirm": False,
            },
            '2': {
                "label": "Stop local MySQL server",
                "fn": self.db_manager.stop_server,
                "confirm": False,
            },
            '3': {
                "label": "Rebuild database schema",
                "fn": self.db_manager.initialize_schema,
                "confirm": True,
                "prompt": (
                    "This will DROP and recreate the database defined in your settings.\n"
                    "All existing data will be lost. Continue?"
                ),
            },
            '4': {
                "label": "Load demo transactions",
                "fn": self.db_manager.load_demo_data,
                "confirm": False,
            },
            '5': {
                "label": "Stop and remove local data directory",
                "fn": self.db_manager.purge_data_directory,
                "confirm": True,
                "prompt": (
                    "This will stop the local MySQL server (if running) and delete "
                    f"{self.db_manager.data_dir}.\n"
                    "You will lose any data stored there. Continue?"
                ),
            },
        }

        if choice not in actions:
            return False

        action = actions[choice]
        if choice == '5' and not self.db_manager.supports_local_control():
            self.console.print("\n❌ Local reset is only available when using the managed local server.", style="red")
            input("\nPress Enter to continue...")
            return True

        if action.get("confirm"):
            prompt = action.get("prompt") or f"{action['label']}?"
            if not Confirm.ask(f"\n{prompt}", default=False):
                self.console.print("\n⚠️  Action cancelled.", style="yellow")
                input("\nPress Enter to continue...")
                return True

        success, message = action["fn"]()
        icon = "✅" if success else "❌"
        style = "green" if success else "red"
        self.console.print(f"\n{icon} {message}", style=style)
        input("\nPress Enter to continue...")
        return True

    def print_database_error(self, err: MySQLError):
        """Display structured database error messaging with helpful hints."""
        code = getattr(err, "errno", None)
        message = str(err).strip()

        info_table = Table(show_header=False, box=box.SIMPLE)
        info_table.add_column("", style="bold red", width=12)
        info_table.add_column("Details", style="white")

        info_table.add_row("Error Code", str(code) if code is not None else "Unknown")
        info_table.add_row("Message", message or "No error message available.")

        hints: List[str] = []
        if code == 1049:
            hints.append("Database not found. Use [3] Rebuild schema to create it.")
        elif code == 1146:
            hints.append("Required tables missing. Run [3] Rebuild schema.")
        elif code in (2002, 2003):
            hints.append("Cannot reach MySQL server. Verify it's running or press [1] Start server.")

        if hints:
            info_table.add_row("", "")
            info_table.add_row("Guidance", "")
            for hint in hints:
                info_table.add_row("", f"[yellow]{hint}[/yellow]")

        panel = Panel(
            info_table,
            title="❌ Database Error",
            border_style="red",
        )
        self.console.print(panel)

    def print_summary(self, stats: Dict[str, Any]):
        """Print summary statistics with Rich formatting"""
        # Create main summary table
        summary_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        summary_table.add_column("Metric", style="bold cyan", width=20)
        summary_table.add_column("Value", style="bold green")

        summary_table.add_row("Total Transactions", f"{stats['total_count']:,}")

        if stats['total_amount']:
            summary_table.add_row("Total Amount", f"${stats['total_amount']:,.2f}")
            summary_table.add_row("Average Amount", f"${stats['avg_amount']:,.2f}")
            summary_table.add_row("Min Amount", f"${stats['min_amount']:,.2f}")
            summary_table.add_row("Max Amount", f"${stats['max_amount']:,.2f}")

        if stats['earliest_date'] and stats['latest_date']:
            summary_table.add_row("Date Range", f"{stats['earliest_date']} to {stats['latest_date']}")

        # Create type breakdown table if available
        if stats['type_breakdown']:
            type_table = Table(box=box.MINIMAL, show_header=True)
            type_table.add_column("Transaction Type", style="cyan")
            type_table.add_column("Count", style="yellow", justify="right")
            type_table.add_column("Total Amount", style="green", justify="right")

            for txn_type, data in stats['type_breakdown'].items():
                type_table.add_row(
                    txn_type,
                    f"{data['count']:,}",
                    f"${data['total']:,.2f}"
                )

            # Combine both tables in panels
            self.console.print(Panel(
                summary_table,
                title="📊 Summary Statistics",
                title_align="left",
                border_style="blue"
            ))
            self.console.print(Panel(
                type_table,
                title="📈 Breakdown by Type",
                title_align="left",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                summary_table,
                title="📊 Summary Statistics",
                title_align="left",
                border_style="blue"
            ))

    def print_filters(self):
        """Print current active filters with Rich formatting"""
        if not any(self.filters.values()):
            return

        filter_table = Table(box=box.MINIMAL, show_header=False)
        filter_table.add_column("Filter", style="cyan", width=15)
        filter_table.add_column("Value", style="yellow")

        for key, value in self.filters.items():
            if value:
                display_key = key.replace('_', ' ').title()
                filter_table.add_row(display_key, str(value))

        panel = Panel(
            filter_table,
            title="🔍 Active Filters",
            title_align="left",
            border_style="yellow"
        )
        self.console.print(panel)

    def print_transactions(self, transactions: List[Dict[str, Any]], start_index: int = 0):
        """Print transaction table with Rich formatting"""
        if not transactions:
            self.console.print("\n❌ No transactions found matching current filters.", style="bold red")
            return

        # Create beautiful table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Type", style="yellow", width=10)
        table.add_column("Amount", style="green", width=15, justify="right")
        table.add_column("Description", style="white", min_width=30, max_width=50)
        table.add_column("Account", style="blue", width=12)

        # Add transactions with color coding
        for i, tx in enumerate(transactions):
            index = start_index + i + 1
            date_str = str(tx['transaction_date'])
            type_str = tx['transaction_type']
            amount = tx['amount']

            # Color code amount based on positive/negative
            if amount >= 0:
                amount_str = f"[green]+${amount:,.2f}[/green]"
            else:
                amount_str = f"[red]-${abs(amount):,.2f}[/red]"

            desc = tx['description'] or 'N/A'
            # Truncate description intelligently
            if len(desc) > 47:
                desc = desc[:44] + "..."

            account_str = tx['account_number'] or 'N/A'

            # Alternate row colors for better readability
            if i % 2 == 0:
                table.add_row(
                    str(index), date_str, type_str, amount_str, desc, account_str,
                    style="on grey11"
                )
            else:
                table.add_row(
                    str(index), date_str, type_str, amount_str, desc, account_str
                )

        # Print with panel
        panel = Panel(
            table,
            title="📋 Transactions",
            title_align="left",
            border_style="bright_blue"
        )
        self.console.print(panel)

    def print_pagination_info(self, total_count: int, status: Optional[Dict[str, Any]] = None):
        """Print pagination information with Rich formatting"""
        total_pages = (total_count + self.page_size - 1) // self.page_size
        start_record = (self.current_page - 1) * self.page_size + 1
        end_record = min(self.current_page * self.page_size, total_count)

        # Page info
        page_info = Text()
        page_info.append("Page ", style="dim")
        page_info.append(f"{self.current_page}", style="bold cyan")
        page_info.append(" of ", style="dim")
        page_info.append(f"{total_pages}", style="bold cyan")
        page_info.append(" | Records ", style="dim")
        page_info.append(f"{start_record}-{end_record}", style="bold yellow")
        page_info.append(" of ", style="dim")
        page_info.append(f"{total_count}", style="bold yellow")

        # Navigation options with proper Rich Text formatting
        options_text = Text("Options: ")

        nav_options = []
        if self.current_page > 1:
            nav_options.append(("p", "green", "Previous page"))
        if self.current_page < total_pages:
            nav_options.append(("n", "green", "Next page"))

        nav_options.extend([
            ("f", "blue", "Filter"),
            ("s", "blue", "Sort"),
            ("e", "blue", "Export"),
            ("r", "yellow", "Reset"),
            ("1", "magenta", "Start server"),
            ("2", "magenta", "Stop server"),
            ("3", "magenta", "Init schema"),
            ("4", "magenta", "Load demo data"),
            ("q", "red", "Quit")
        ])

        status = status or self.db_manager.get_status()
        if status.get("manageable"):
            nav_options.insert(-1, ("5", "magenta", "Reset data dir"))

        for i, (key, color, desc) in enumerate(nav_options):
            if i > 0:
                options_text.append(" | ")
            options_text.append(key, style=f"bold {color}")
            options_text.append(f") {desc}")

        # Create panel for navigation
        nav_content = Text()
        nav_content.append(page_info)
        nav_content.append("\n\n")
        nav_content.append(options_text)

        nav_panel = Panel(
            Align.center(nav_content),
            title="Navigation",
            border_style="cyan"
        )
        self.console.print(nav_panel)

    def handle_filter_menu(self):
        """Handle filter configuration"""
        print(f"\n🔍 FILTER MENU")
        print("-" * 40)
        print("1) Date range")
        print("2) Transaction type")
        print("3) Amount range")
        print("4) Search description")
        print("5) Account number")
        print("6) Clear all filters")
        print("0) Back to main menu")

        choice = input("\nSelect filter option: ").strip()

        if choice == '1':
            start_date = input("Start date (YYYY-MM-DD) [Enter to skip]: ").strip()
            end_date = input("End date (YYYY-MM-DD) [Enter to skip]: ").strip()
            if start_date:
                self.filters['start_date'] = start_date
            if end_date:
                self.filters['end_date'] = end_date

        elif choice == '2':
            print("Transaction types: CREDIT, DEBIT, TRANSFER")
            txn_type = input("Transaction type [Enter to skip]: ").strip().upper()
            if txn_type in ['CREDIT', 'DEBIT', 'TRANSFER']:
                self.filters['transaction_type'] = txn_type
            elif txn_type:
                print("❌ Invalid transaction type")

        elif choice == '3':
            min_amount = input("Minimum amount [Enter to skip]: ").strip()
            max_amount = input("Maximum amount [Enter to skip]: ").strip()
            if min_amount:
                try:
                    self.filters['min_amount'] = float(min_amount)
                except ValueError:
                    print("❌ Invalid minimum amount")
            if max_amount:
                try:
                    self.filters['max_amount'] = float(max_amount)
                except ValueError:
                    print("❌ Invalid maximum amount")

        elif choice == '4':
            search_term = input("Search description [Enter to skip]: ").strip()
            if search_term:
                self.filters['search'] = search_term

        elif choice == '5':
            account = input("Account number [Enter to skip]: ").strip()
            if account:
                self.filters['account_number'] = account

        elif choice == '6':
            self.filters.clear()
            print("✅ All filters cleared")

        # Reset to first page when filters change
        self.current_page = 1

    def handle_sort_menu(self):
        """Handle sort configuration"""
        print(f"\n📊 SORT MENU")
        print("-" * 40)
        print("1) Transaction date")
        print("2) Amount")
        print("3) Description")
        print("4) Transaction type")
        print("0) Back to main menu")

        choice = input("\nSelect sort field: ").strip()

        sort_fields = {
            '1': 'transaction_date',
            '2': 'amount',
            '3': 'description',
            '4': 'transaction_type'
        }

        if choice in sort_fields:
            self.sort_by = sort_fields[choice]

            order = input("Sort order (a)scending or (d)escending [d]: ").strip().lower()
            self.sort_order = 'ASC' if order == 'a' else 'DESC'

            print(f"✅ Sorting by {self.sort_by} ({self.sort_order})")
            self.current_page = 1

    def export_transactions(self, format_type: str):
        """Export transactions to file"""
        transactions = self.get_transactions()

        if not transactions:
            print("❌ No transactions to export")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_export_{timestamp}.{format_type}"

        try:
            if format_type == 'csv':
                with open(filename, 'w', newline='') as csvfile:
                    if transactions:
                        writer = csv.DictWriter(csvfile, fieldnames=transactions[0].keys())
                        writer.writeheader()
                        for tx in transactions:
                            # Convert date objects to strings
                            row = {}
                            for key, value in tx.items():
                                if isinstance(value, date):
                                    row[key] = value.isoformat()
                                else:
                                    row[key] = value
                            writer.writerow(row)

            elif format_type == 'json':
                def json_serializer(obj):
                    if isinstance(obj, date):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                with open(filename, 'w') as jsonfile:
                    json.dump(transactions, jsonfile, indent=2, default=json_serializer)

            print(f"✅ Exported {len(transactions)} transactions to {filename}")

        except Exception as e:
            print(f"❌ Export failed: {str(e)}")

    def handle_export_menu(self):
        """Handle export options"""
        print(f"\n💾 EXPORT MENU")
        print("-" * 40)
        print("1) Export to CSV")
        print("2) Export to JSON")
        print("0) Back to main menu")

        choice = input("\nSelect export format: ").strip()

        if choice == '1':
            self.export_transactions('csv')
        elif choice == '2':
            self.export_transactions('json')

    def reset_all(self):
        """Reset filters, sorting, and pagination"""
        self.filters.clear()
        self.current_page = 1
        self.sort_by = 'transaction_date'
        self.sort_order = 'DESC'
        print("✅ Reset to default view")

    def run_interactive(self):
        """Run interactive dashboard with system management controls"""
        while True:
            try:
                status = self.db_manager.get_status()

                os.system('clear' if os.name == 'posix' else 'cls')
                self.print_header()
                self.print_system_controls(status=status)

                if not status["running"]:
                    self.console.print("\n[bold red]Database server is not reachable.[/bold red]")
                    self.console.print("[dim]Use the controls above to start the service or adjust credentials.[/dim]")
                    self.console.print("[dim]Options: 1) Start | 2) Stop | 3) Init | 4) Demo | 5) Reset | q) Quit[/dim]")

                    choice = input("\nEnter your choice: ").strip().lower()
                    if self.handle_system_action(choice):
                        continue
                    if choice == 'q':
                        break

                    self.console.print("\n❌ Invalid choice. Press Enter to continue...", style="red")
                    input()
                    continue

                try:
                    total_count = self.get_transaction_count()
                    stats = self.get_summary_stats()
                except MySQLError as db_error:
                    self.print_database_error(db_error)
                    choice = input("\nEnter your choice ([1-5]/q or Enter to retry): ").strip().lower()
                    if self.handle_system_action(choice):
                        continue
                    if choice == 'q':
                        break
                    # Empty choice falls through to retry loop
                    continue

                self.print_summary(stats)
                self.print_filters()

                if total_count == 0:
                    self.console.print("\n❌ No transactions found.", style="bold red")
                    self.console.print("[dim]Options: f) Filter | r) Reset | 4) Demo | q) Quit[/dim]")

                    choice = input("\nEnter your choice: ").strip().lower()
                    if self.handle_system_action(choice):
                        continue
                    if choice == 'f':
                        self.handle_filter_menu()
                    elif choice == 'r':
                        self.reset_all()
                    elif choice == 'q':
                        break
                    else:
                        self.console.print("\n❌ Invalid choice. Press Enter to continue...", style="red")
                        input()
                    continue

                offset = (self.current_page - 1) * self.page_size
                transactions = self.get_transactions(limit=self.page_size, offset=offset)

                self.print_transactions(transactions, offset)
                self.print_pagination_info(total_count, status=status)

                choice = input("\nEnter your choice: ").strip().lower()

                if self.handle_system_action(choice):
                    continue
                if choice == 'q':
                    break
                elif choice == 'n':
                    total_pages = (total_count + self.page_size - 1) // self.page_size
                    if self.current_page < total_pages:
                        self.current_page += 1
                elif choice == 'p':
                    if self.current_page > 1:
                        self.current_page -= 1
                elif choice == 'f':
                    self.handle_filter_menu()
                elif choice == 's':
                    self.handle_sort_menu()
                elif choice == 'e':
                    self.handle_export_menu()
                elif choice == 'r':
                    self.reset_all()
                else:
                    self.console.print("\n❌ Invalid choice. Press Enter to continue...", style="red")
                    input()

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                input("Press Enter to continue...")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced Transaction Viewer Dashboard')
    parser.add_argument('--org-id', type=int, default=1, help='Organization ID (default: 1)')
    parser.add_argument('--page-size', type=int, default=20, help='Records per page (default: 20)')
    parser.add_argument('--export', choices=['csv', 'json'], help='Export all data and exit')
    parser.add_argument('--summary-only', action='store_true', help='Show summary statistics only')

    args = parser.parse_args()

    viewer = TransactionViewer(org_id=args.org_id)
    viewer.page_size = args.page_size

    if args.export:
        # Non-interactive export mode
        viewer.export_transactions(args.export)
        return

    if args.summary_only:
        # Summary only mode
        viewer.print_header()
        stats = viewer.get_summary_stats()
        viewer.print_summary(stats)
        return

    # Interactive mode
    viewer.run_interactive()

if __name__ == "__main__":
    main()
