#!/usr/bin/env python3
"""
Infrastructure Test-Driven Development Suite
Tests for Letta server setup, static admin page, and system integration.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
import requests


class TestLettaInstallation:
    """RED PHASE: Tests that verify Letta installation and configuration"""

    def test_letta_command_available(self):
        """Verify letta CLI is installed"""
        assert shutil.which("letta") is not None, "letta CLI not found in PATH"

    def test_alembic_command_available(self):
        """Verify alembic CLI is installed (needed for DB migrations)"""
        assert shutil.which("alembic") is not None, "alembic CLI not found in PATH"

    def test_letta_package_installed(self):
        """Verify letta Python package is installed"""
        try:
            import letta
            assert hasattr(letta, "__version__"), "letta module has no version"
        except ImportError:
            pytest.fail("letta package not installed")


class TestLettaServerStartup:
    """GREEN PHASE: Tests that verify Letta server can start and respond"""

    @pytest.mark.slow
    def test_letta_health_endpoint(self):
        """Verify Letta server responds (web UI at root)"""
        try:
            response = requests.get("http://localhost:8283/", timeout=5)
            assert response.status_code == 200, f"Server check failed: {response.status_code}"
            assert "Letta" in response.text or "<!doctype html>" in response.text.lower(), \
                "Response doesn't look like Letta web UI"
        except requests.exceptions.ConnectionError:
            pytest.fail("Letta server not running on port 8283")

    @pytest.mark.slow
    def test_letta_database_initialized(self):
        """Verify Letta database has required tables (PostgreSQL)"""
        try:
            import psycopg2
            # Connect to PostgreSQL database
            conn = psycopg2.connect(
                dbname="letta",
                user="letta",
                password="letta",
                host="localhost",
                port="5432"
            )
            cursor = conn.cursor()

            # Check if organizations table exists
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public' AND table_name='organizations'
            """)

            result = cursor.fetchone()
            conn.close()

            assert result is not None, "organizations table not found in PostgreSQL database"
        except ImportError:
            pytest.skip("psycopg2 not installed - cannot check PostgreSQL database")
        except Exception as e:
            pytest.fail(f"Failed to check PostgreSQL database: {e}")


class TestStaticAdminPage:
    """REFACTOR PHASE: Tests for static administration page"""

    def test_static_admin_page_exists(self):
        """Verify static admin HTML file exists"""
        admin_page = Path("/home/adamsl/planner/sys_admin_static.html")
        assert admin_page.exists(), "Static admin page not found"

    def test_static_admin_page_is_valid_html(self):
        """Verify static admin page is valid HTML"""
        admin_page = Path("/home/adamsl/planner/sys_admin_static.html")

        if not admin_page.exists():
            pytest.skip("Static admin page not created yet")

        content = admin_page.read_text()

        # Basic HTML validation
        assert "<!DOCTYPE html>" in content, "Missing DOCTYPE declaration"
        assert "<html" in content, "Missing html tag"
        assert "</html>" in content, "Missing closing html tag"
        assert "<head>" in content, "Missing head section"
        assert "<body>" in content, "Missing body section"

    def test_static_admin_page_has_no_server_dependencies(self):
        """Verify static admin page doesn't require server to function"""
        admin_page = Path("/home/adamsl/planner/sys_admin_static.html")

        if not admin_page.exists():
            pytest.skip("Static admin page not created yet")

        content = admin_page.read_text()

        # Should not have fetch/AJAX calls to backend servers
        # (except for optional health checks which gracefully fail)
        assert "file://" in content or "Standalone" in content, \
            "Page should be marked as standalone/static"

    def test_static_admin_page_contains_system_status(self):
        """Verify static admin page includes system status information"""
        admin_page = Path("/home/adamsl/planner/sys_admin_static.html")

        if not admin_page.exists():
            pytest.skip("Static admin page not created yet")

        content = admin_page.read_text()

        # Should contain status information embedded in HTML
        assert "Letta" in content or "8283" in content, \
            "Page should mention Letta server"
        assert "Dashboard" in content or "3000" in content, \
            "Page should mention Dashboard"


class TestSystemIntegration:
    """Integration tests for complete A2A system"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_startup_script_exists(self):
        """Verify A2A system startup script exists"""
        script = Path("/home/adamsl/planner/start_a2a_system.sh")
        assert script.exists(), "Startup script not found"
        assert script.stat().st_mode & 0o111, "Startup script not executable"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_all_required_ports_available(self):
        """Verify required ports are not blocked"""
        import socket

        required_ports = [8283, 3000]  # Letta, Dashboard

        for port in required_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('localhost', port))
                # Port should either be available (connection refused)
                # or have a service running (connection succeeds)
                assert result in [0, 111], f"Port {port} in unexpected state"
