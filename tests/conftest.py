"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def mock_config():
    """Fixture providing a mock configuration object."""
    from unittest.mock import MagicMock

    config = MagicMock()
    config.tenant_id = "00000000-0000-0000-0000-000000000001"
    config.client_id = "00000000-0000-0000-0000-000000000002"
    config.client_secret = "test-secret"
    config.workspace_ids = ["00000000-0000-0000-0000-000000000003"]
    config.dataset_ids = None
    config.poll_interval = 30
    config.max_retries = 3
    config.retry_backoff = [5, 10, 20]
    config.log_level = "INFO"
    config.log_file = None
    config.timeout = 3600

    return config
