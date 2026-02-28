"""Main CLI module for Power BI refresh script."""

import argparse
import json
import sys
from typing import List, Optional

from .auth import AuthenticationService
from .config import ConfigManager
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    PowerBIScriptError,
)
from .logger import ScriptLogger
from .orchestrator import RefreshOrchestrator
from .powerbi_client import PowerBIClient
from .refresh_manager import RefreshManager
from .retry import RetryHandler


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: List of arguments to parse (defaults to sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="powerbi-refresh",
        description="Automated Power BI dataset refresh using Azure service principal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using configuration file
  powerbi-refresh --config config.yaml

  # Override specific settings
  powerbi-refresh --config config.yaml --log-level DEBUG

  # Specify workspace and dataset directly
  powerbi-refresh --workspace-id abc-123 --dataset-id def-456

  # Output in JSON format
  powerbi-refresh --config config.yaml --output-format json

Environment Variables:
  AZURE_TENANT_ID       Azure AD tenant ID
  AZURE_CLIENT_ID       Service principal client ID
  AZURE_CLIENT_SECRET   Service principal client secret
  POWERBI_WORKSPACE_IDS Comma-separated workspace IDs
  POWERBI_DATASET_IDS   Comma-separated dataset IDs (optional)
  LOG_LEVEL             Logging level (DEBUG, INFO, WARNING, ERROR)
  LOG_FILE              Path to log file
        """
    )

    # Configuration file
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON or YAML)"
    )

    # Workspace and dataset IDs
    parser.add_argument(
        "--workspace-id",
        type=str,
        action="append",
        dest="workspace_id",
        help="Workspace ID (can be specified multiple times)"
    )

    parser.add_argument(
        "--dataset-id",
        type=str,
        action="append",
        dest="dataset_id",
        help="Dataset ID to refresh (can be specified multiple times)"
    )

    # Azure credentials (for override)
    parser.add_argument(
        "--tenant-id",
        type=str,
        help="Azure AD tenant ID"
    )

    parser.add_argument(
        "--client-id",
        type=str,
        help="Service principal client ID"
    )

    parser.add_argument(
        "--client-secret",
        type=str,
        help="Service principal client secret"
    )

    # Execution parameters
    parser.add_argument(
        "--poll-interval",
        type=int,
        help="Polling interval in seconds (default: 30)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout for refresh operations in seconds (default: 3600)"
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        help="Maximum number of retries for transient errors (default: 3)"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (logs to console only if not specified)"
    )

    # Output format
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format for summary (default: text)"
    )

    return parser.parse_args(args)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the Power BI refresh script.

    This function coordinates the entire refresh process:
    1. Parse command-line arguments
    2. Load and validate configuration
    3. Set up logging
    4. Authenticate with Azure AD
    5. Execute refresh operations
    6. Output summary
    7. Return appropriate exit code

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code:
        - 0: All refreshes successful
        - 1: Fatal error (configuration, authentication, etc.)
        - 2: Partial success (some refreshes failed)
    """
    # Parse arguments
    try:
        args = parse_arguments(argv)
    except SystemExit as e:
        # argparse calls sys.exit() on error or --help
        return e.code if isinstance(e.code, int) else 1

    # Convert args to dictionary for ConfigManager
    cli_args = {
        "workspace_id": args.workspace_id,
        "dataset_id": args.dataset_id,
        "tenant_id": args.tenant_id,
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "poll_interval": args.poll_interval,
        "timeout": args.timeout,
        "max_retries": args.max_retries,
        "log_level": args.log_level,
        "log_file": args.log_file,
    }

    # Load configuration
    try:
        config = ConfigManager.load(
            config_path=args.config,
            cli_args=cli_args
        )
    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"Unexpected error loading configuration: {e}", file=sys.stderr)
        return 1

    # Set up logging
    try:
        logger = ScriptLogger.setup(
            log_level=config.log_level,
            log_file=config.log_file
        )
    except Exception as e:  # noqa: BLE001
        print(f"Error setting up logging: {e}", file=sys.stderr)
        return 1

    logger.info("=" * 60)
    logger.info("Power BI Refresh Script - Starting")
    logger.info("=" * 60)

    # Initialize components
    try:
        # Retry handler
        retry_handler = RetryHandler(
            max_retries=config.max_retries,
            backoff_delays=config.retry_backoff
        )

        # Authentication service
        logger.info("Initializing authentication service")
        auth_service = AuthenticationService(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret
        )

        # Authenticate
        logger.info("Authenticating with Azure AD")
        try:
            auth_service.get_access_token()
            logger.info("Authentication successful")
        except AuthenticationError as e:
            logger.error("Authentication failed: %s", str(e))
            return 1

        # Power BI client
        logger.info("Initializing Power BI client")
        powerbi_client = PowerBIClient(
            auth_service=auth_service,
            retry_handler=retry_handler
        )

        # Refresh manager
        logger.info("Initializing refresh manager")
        refresh_manager = RefreshManager(
            client=powerbi_client,
            poll_interval=config.poll_interval,
            timeout=config.timeout
        )

        # Orchestrator
        logger.info("Initializing orchestrator")
        orchestrator = RefreshOrchestrator(
            config=config,
            refresh_manager=refresh_manager,
            logger_instance=logger
        )

    except Exception as e:  # noqa: BLE001
        logger.error("Error initializing components: %s", str(e), exc_info=True)
        return 1

    # Execute refresh operations
    try:
        logger.info("Starting refresh execution")
        summary = orchestrator.execute()
        logger.info("Refresh execution completed")

    except PowerBIScriptError as e:
        logger.error("Script error during execution: %s", str(e), exc_info=True)
        return 1
    except Exception as e:  # noqa: BLE001
        logger.error("Unexpected error during execution: %s", str(e), exc_info=True)
        return 1

    # Output summary
    logger.info("=" * 60)
    logger.info("Generating summary")
    logger.info("=" * 60)

    try:
        if args.output_format == "json":
            # JSON output
            summary_dict = summary.to_dict()
            json_output = json.dumps(summary_dict, indent=2)
            print(json_output)
        else:
            # Text output
            text_output = summary.to_text()
            print(text_output)

    except Exception as e:  # noqa: BLE001
        logger.error("Error generating summary output: %s", str(e), exc_info=True)
        # Continue to return appropriate exit code based on results

    # Determine exit code
    if summary.total_datasets == 0:
        # No datasets were processed - this is an error condition
        logger.error("No datasets were processed - check configuration and permissions")
        return 1
    elif summary.failed == 0:
        # All successful
        logger.info("All refreshes completed successfully")
        return 0
    elif summary.successful > 0:
        # Partial success
        logger.warning(
            "Partial success: %d successful, %d failed",
            summary.successful,
            summary.failed
        )
        return 2
    else:
        # All failed
        logger.error("All refreshes failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
