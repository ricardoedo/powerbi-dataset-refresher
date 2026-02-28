"""Unit tests for main CLI module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from powerbi_refresh.main import main, parse_arguments
from powerbi_refresh.models import ExecutionSummary, RefreshResult


class TestParseArguments:
    """Tests for argument parsing."""

    def test_parse_config_argument(self):
        """Test parsing --config argument."""
        args = parse_arguments(["--config", "config.yaml"])
        assert args.config == "config.yaml"

    def test_parse_workspace_id_single(self):
        """Test parsing single --workspace-id argument."""
        args = parse_arguments(["--workspace-id", "abc-123"])
        assert args.workspace_id == ["abc-123"]

    def test_parse_workspace_id_multiple(self):
        """Test parsing multiple --workspace-id arguments."""
        args = parse_arguments([
            "--workspace-id", "abc-123",
            "--workspace-id", "def-456"
        ])
        assert args.workspace_id == ["abc-123", "def-456"]

    def test_parse_dataset_id_single(self):
        """Test parsing single --dataset-id argument."""
        args = parse_arguments(["--dataset-id", "dataset-1"])
        assert args.dataset_id == ["dataset-1"]

    def test_parse_log_level(self):
        """Test parsing --log-level argument."""
        args = parse_arguments(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_parse_output_format_text(self):
        """Test parsing --output-format text."""
        args = parse_arguments(["--output-format", "text"])
        assert args.output_format == "text"

    def test_parse_output_format_json(self):
        """Test parsing --output-format json."""
        args = parse_arguments(["--output-format", "json"])
        assert args.output_format == "json"

    def test_default_output_format(self):
        """Test default output format is text."""
        args = parse_arguments([])
        assert args.output_format == "text"


class TestMainExitCodes:
    """Tests for main function exit codes."""

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    def test_exit_code_0_all_successful(
        self,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """Test exit code 0 when all refreshes are successful."""
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

        # Create successful summary
        summary = ExecutionSummary(
            total_datasets=2,
            successful=2,
            failed=0,
            total_duration=120.5,
            results=[]
        )
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Execute
        exit_code = main(["--config", "config.yaml"])

        # Verify
        assert exit_code == 0

    @patch("powerbi_refresh.main.ConfigManager")
    def test_exit_code_1_configuration_error(self, mock_config_manager_class):
        """Test exit code 1 when configuration is invalid."""
        from powerbi_refresh.exceptions import ConfigurationError

        # Setup mock to raise configuration error
        mock_config_manager_class.load.side_effect = ConfigurationError(
            "Missing required field: tenant_id"
        )

        # Execute
        exit_code = main(["--config", "config.yaml"])

        # Verify
        assert exit_code == 1

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    def test_exit_code_1_authentication_error(
        self,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """Test exit code 1 when authentication fails."""
        from powerbi_refresh.exceptions import AuthenticationError

        # Setup mocks
        mock_config = MagicMock()
        mock_config.log_level = "INFO"
        mock_config.log_file = None
        mock_config.max_retries = 3
        mock_config.retry_backoff = [5, 10, 20]
        mock_config.tenant_id = "tenant-123"
        mock_config.client_id = "client-123"
        mock_config.client_secret = "invalid-secret"
        mock_config_manager_class.load.return_value = mock_config

        mock_logger = MagicMock()
        mock_logger_class.setup.return_value = mock_logger

        # Setup auth to fail
        mock_auth = MagicMock()
        mock_auth.get_access_token.side_effect = AuthenticationError(
            "Invalid credentials"
        )
        mock_auth_class.return_value = mock_auth

        # Execute
        exit_code = main(["--config", "config.yaml"])

        # Verify
        assert exit_code == 1

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    def test_exit_code_2_partial_success(
        self,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """Test exit code 2 when some refreshes fail (partial success)."""
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

        # Create partial success summary
        summary = ExecutionSummary(
            total_datasets=3,
            successful=2,
            failed=1,
            total_duration=150.0,
            results=[]
        )
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Execute
        exit_code = main(["--config", "config.yaml"])

        # Verify
        assert exit_code == 2

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    def test_exit_code_1_all_failed(
        self,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """Test exit code 1 when all refreshes fail."""
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

        # Create all failed summary
        summary = ExecutionSummary(
            total_datasets=2,
            successful=0,
            failed=2,
            total_duration=60.0,
            results=[]
        )
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute.return_value = summary
        mock_orchestrator_class.return_value = mock_orchestrator

        # Execute
        exit_code = main(["--config", "config.yaml"])

        # Verify
        assert exit_code == 1


class TestMainOutputFormats:
    """Tests for output format handling."""

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
        """Test text output format."""
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

        # Execute with text format
        exit_code = main(["--config", "config.yaml", "--output-format", "text"])

        # Verify print was called with text output
        assert exit_code == 0
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        assert "EXECUTION SUMMARY" in output

    @patch("powerbi_refresh.main.ConfigManager")
    @patch("powerbi_refresh.main.ScriptLogger")
    @patch("powerbi_refresh.main.AuthenticationService")
    @patch("powerbi_refresh.main.PowerBIClient")
    @patch("powerbi_refresh.main.RefreshManager")
    @patch("powerbi_refresh.main.RefreshOrchestrator")
    @patch("builtins.print")
    def test_json_output_format(
        self,
        mock_print,
        mock_orchestrator_class,
        mock_refresh_manager_class,
        mock_client_class,
        mock_auth_class,
        mock_logger_class,
        mock_config_manager_class,
    ):
        """Test JSON output format."""
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

        # Execute with JSON format
        exit_code = main(["--config", "config.yaml", "--output-format", "json"])

        # Verify print was called with JSON output
        assert exit_code == 0
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]

        # Verify it's valid JSON
        parsed = json.loads(output)
        assert parsed["total_datasets"] == 1
        assert parsed["successful"] == 1
        assert parsed["failed"] == 0
