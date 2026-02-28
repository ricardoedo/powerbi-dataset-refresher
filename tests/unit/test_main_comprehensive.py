"""Comprehensive tests for main module requirements."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from powerbi_refresh.main import main
from powerbi_refresh.models import ExecutionSummary, RefreshResult


class TestMainRequirements:
    """Tests validating task requirements for main.py."""

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    def test_requirement_7_2_cli_args_override_config(
        self,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """
        Test Requirement 7.2: CLI arguments override configuration file.

        Validates that command-line arguments have precedence over config file.
        """
        # Setup mocks
        mock_config = MagicMock()
        mock_config.log_level = "DEBUG"  # Overridden from CLI
        mock_config.log_file = None
        mock_config.max_retries = 3
        mock_config.retry_backoff = [5, 10, 20]
        mock_config.tenant_id = "tenant-123"
        mock_config.client_id = "client-123"
        mock_config.client_secret = "secret"
        mock_config.poll_interval = 30
        mock_config.timeout = 3600
        mock_config_manager_class.load.return_value = mock_config

        mock_logger = MagicMock()
        mock_logger_class.setup.return_value = mock_logger

        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth

        summary = ExecutionSummary(
            total_datasets=1,
            successful=1,
            failed=0,
            total_duration=60.0,
            results=[]
        )
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Execute with CLI override
        exit_code = main([
            "--config", "config.yaml",
            "--log-level", "DEBUG"
        ])

        # Verify ConfigManager.load was called with CLI args
        call_args = mock_config_manager_class.load.call_args
        assert call_args[1]["config_path"] == "config.yaml"
        assert call_args[1]["cli_args"]["log_level"] == "DEBUG"
        assert exit_code == 0

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    @patch("builtins.print")
    def test_requirement_9_5_json_output_format(
        self,
        mock_print,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """
        Test Requirement 9.5: JSON output format for summary.

        Validates that summary can be output in JSON format.
        """
        # Setup mocks
        mock_config = MagicMock()
        mock_config.log_level = "INFO"
        mock_config.log_file = None
        mock_config.max_retries = 3
        mock_config.retry_backoff = [5, 10, 20]
        mock_config.tenant_id = "tenant-123"
        mock_config.client_id = "client-123"
        mock_config.client_secret = "secret"
        mock_config.poll_interval = 30
        mock_config.timeout = 3600
        mock_config_manager_class.load.return_value = mock_config

        mock_logger = MagicMock()
        mock_logger_class.setup.return_value = mock_logger

        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth

        # Create summary with detailed results
        result1 = RefreshResult(
            dataset_id="dataset-1",
            dataset_name="Sales Data",
            workspace_id="workspace-1",
            success=True,
            duration=45.5,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 0, 45)
        )

        result2 = RefreshResult(
            dataset_id="dataset-2",
            dataset_name="Marketing Data",
            workspace_id="workspace-1",
            success=False,
            duration=30.0,
            error_message="Timeout waiting for refresh",
            start_time=datetime(2024, 1, 1, 10, 1, 0),
            end_time=datetime(2024, 1, 1, 10, 1, 30)
        )

        summary = ExecutionSummary(
            total_datasets=2,
            successful=1,
            failed=1,
            total_duration=75.5,
            results=[result1, result2]
        )

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Execute with JSON format
        exit_code = main(["--config", "config.yaml", "--output-format", "json"])

        # Verify JSON output
        assert exit_code == 2  # Partial success
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]

        # Verify it's valid JSON with expected structure
        import json
        parsed = json.loads(output)
        assert parsed["total_datasets"] == 2
        assert parsed["successful"] == 1
        assert parsed["failed"] == 1
        assert parsed["total_duration"] == 75.5
        assert len(parsed["results"]) == 2

        # Verify result details
        assert parsed["results"][0]["dataset_name"] == "Sales Data"
        assert parsed["results"][0]["success"] is True
        assert parsed["results"][1]["dataset_name"] == "Marketing Data"
        assert parsed["results"][1]["success"] is False
        assert parsed["results"][1]["error_message"] == "Timeout waiting for refresh"

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    @patch("builtins.print")
    def test_text_output_format(
        self,
        mock_print,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """
        Test text output format for summary.

        Validates that summary can be output in human-readable text format.
        """
        # Setup mocks
        mock_config = MagicMock()
        mock_config.log_level = "INFO"
        mock_config.log_file = None
        mock_config.max_retries = 3
        mock_config.retry_backoff = [5, 10, 20]
        mock_config.tenant_id = "tenant-123"
        mock_config.client_id = "client-123"
        mock_config.client_secret = "secret"
        mock_config.poll_interval = 30
        mock_config.timeout = 3600
        mock_config_manager_class.load.return_value = mock_config

        mock_logger = MagicMock()
        mock_logger_class.setup.return_value = mock_logger

        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth

        # Create summary
        result = RefreshResult(
            dataset_id="dataset-1",
            dataset_name="Sales Data",
            workspace_id="workspace-1",
            success=True,
            duration=45.5,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 0, 45)
        )

        summary = ExecutionSummary(
            total_datasets=1,
            successful=1,
            failed=0,
            total_duration=45.5,
            results=[result]
        )

        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Execute with text format (default)
        exit_code = main(["--config", "config.yaml"])

        # Verify text output
        assert exit_code == 0
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]

        # Verify text format structure
        assert "EXECUTION SUMMARY" in output
        assert "Total Datasets: 1" in output
        assert "Successful: 1" in output
        assert "Failed: 0" in output
        assert "Sales Data" in output

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    def test_exit_codes_comprehensive(
        self,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """
        Test all three exit codes: 0 (success), 1 (fatal error), 2 (partial success).

        Validates proper exit code handling as per requirements.
        """
        # Setup common mocks
        mock_config = MagicMock()
        mock_config.log_level = "INFO"
        mock_config.log_file = None
        mock_config.max_retries = 3
        mock_config.retry_backoff = [5, 10, 20]
        mock_config.tenant_id = "tenant-123"
        mock_config.client_id = "client-123"
        mock_config.client_secret = "secret"
        mock_config.poll_interval = 30
        mock_config.timeout = 3600
        mock_config_manager_class.load.return_value = mock_config

        mock_logger = MagicMock()
        mock_logger_class.setup.return_value = mock_logger

        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth

        # Test Case 1: Exit code 0 (all successful)
        summary_success = ExecutionSummary(
            total_datasets=3,
            successful=3,
            failed=0,
            total_duration=120.0,
            results=[]
        )
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary_success
        mock_orchestrator_class.return_value = mock_orchestrator

        exit_code = main(["--config", "config.yaml"])
        assert exit_code == 0, "Exit code should be 0 when all refreshes succeed"

        # Test Case 2: Exit code 2 (partial success)
        summary_partial = ExecutionSummary(
            total_datasets=3,
            successful=2,
            failed=1,
            total_duration=120.0,
            results=[]
        )
        mock_orchestrator.execute.return_value = summary_partial

        exit_code = main(["--config", "config.yaml"])
        assert exit_code == 2, "Exit code should be 2 when some refreshes fail"

        # Test Case 3: Exit code 1 (all failed)
        summary_failed = ExecutionSummary(
            total_datasets=3,
            successful=0,
            failed=3,
            total_duration=120.0,
            results=[]
        )
        mock_orchestrator.execute.return_value = summary_failed

        exit_code = main(["--config", "config.yaml"])
        assert exit_code == 1, "Exit code should be 1 when all refreshes fail"

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    def test_orchestration_coordination(
        self,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """
        Test that main() properly coordinates all components.

        Validates that main() loads config, authenticates, and executes orchestration.
        """
        # Setup mocks
        mock_config = MagicMock()
        mock_config.log_level = "INFO"
        mock_config.log_file = None
        mock_config.max_retries = 3
        mock_config.retry_backoff = [5, 10, 20]
        mock_config.tenant_id = "tenant-123"
        mock_config.client_id = "client-123"
        mock_config.client_secret = "secret"
        mock_config.poll_interval = 30
        mock_config.timeout = 3600
        mock_config_manager_class.load.return_value = mock_config

        mock_logger = MagicMock()
        mock_logger_class.setup.return_value = mock_logger

        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_refresh_mgr = MagicMock()
        mock_refresh_manager_class.return_value = mock_refresh_mgr

        summary = ExecutionSummary(
            total_datasets=1,
            successful=1,
            failed=0,
            total_duration=60.0,
            results=[]
        )
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Execute
        exit_code = main(["--config", "config.yaml"])

        # Verify coordination
        # 1. Config loaded
        mock_config_manager_class.load.assert_called_once()

        # 2. Logger setup
        mock_logger_class.setup.assert_called_once_with(
            log_level="INFO",
            log_file=None
        )

        # 3. Authentication service created and authenticated
        mock_auth_class.assert_called_once_with(
            tenant_id="tenant-123",
            client_id="client-123",
            client_secret="secret"
        )
        mock_auth.get_access_token.assert_called_once()

        # 4. PowerBI client created
        mock_client_class.assert_called_once()

        # 5. Refresh manager created
        mock_refresh_manager_class.assert_called_once()

        # 6. Orchestrator created and executed
        mock_orchestrator_class.assert_called_once()
        mock_orchestrator.execute.assert_called_once()

        assert exit_code == 0
