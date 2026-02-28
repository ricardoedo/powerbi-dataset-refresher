"""Integration tests for CLI functionality."""

import json
import subprocess
import sys


class TestCLIIntegration:
    """Integration tests for the CLI."""

    def test_help_command(self):
        """Test that --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "powerbi_refresh.main", "--help"],
            capture_output=True,
            text=True,
            check=False
        )

        assert result.returncode == 0
        assert "powerbi-refresh" in result.stdout
        assert "Automated Power BI dataset refresh" in result.stdout

    def test_missing_config_returns_error(self):
        """Test that missing configuration returns exit code 1."""
        result = subprocess.run(
            [sys.executable, "-m", "powerbi_refresh.main"],
            capture_output=True,
            text=True,
            check=False
        )

        # Should fail with configuration error
        assert result.returncode == 1
        assert "Configuration Error" in result.stderr or "Missing required field" in result.stderr

    def test_invalid_log_level_rejected(self):
        """Test that invalid log level is rejected by argparse."""
        result = subprocess.run(
            [
                sys.executable, "-m", "powerbi_refresh.main",
                "--log-level", "INVALID"
            ],
            capture_output=True,
            text=True,
            check=False
        )

        # Should fail with argument error
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()
