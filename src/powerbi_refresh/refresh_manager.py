"""Refresh manager for Power BI dataset refresh operations."""

import logging
import time
from datetime import datetime

from .models import RefreshResult, RefreshStatus
from .exceptions import RefreshTimeoutError, PowerBIAPIError


logger = logging.getLogger(__name__)


class RefreshManager:
    """Manages the lifecycle of dataset refresh operations."""

    def __init__(
        self,
        client: 'PowerBIClient',  # type: ignore
        poll_interval: int = 30,
        timeout: int = 3600
    ):
        """
        Initialize the refresh manager.

        Args:
            client: PowerBIClient instance for API operations
            poll_interval: Seconds between status checks (default: 30)
            timeout: Maximum seconds to wait for refresh completion (default: 3600)
        """
        self.client = client
        self.poll_interval = poll_interval
        self.timeout = timeout

    def refresh_dataset(
        self,
        workspace_id: str,
        dataset_id: str
    ) -> RefreshResult:
        """
        Refresh a dataset and wait for completion.

        This method:
        1. Starts the refresh operation
        2. Polls the status every poll_interval seconds
        3. Returns when the refresh completes, fails, or times out

        Args:
            workspace_id: ID of the workspace containing the dataset
            dataset_id: ID of the dataset to refresh

        Returns:
            RefreshResult with success/failure details and timing information

        Raises:
            PowerBIAPIError: If API operations fail
        """
        start_time = datetime.now()
        dataset_name = dataset_id  # Will be updated if we can get the actual name

        logger.info(
            "Starting refresh for dataset %s in workspace %s",
            dataset_id,
            workspace_id
        )

        try:
            # Get dataset name for better reporting
            try:
                datasets = self.client.list_datasets(workspace_id)
                for ds in datasets:
                    if ds.get('id') == dataset_id:
                        dataset_name = ds.get('name', dataset_id)
                        break
            except PowerBIAPIError as e:
                logger.warning(
                    "Could not retrieve dataset name: %s. Using ID instead.",
                    str(e)
                )

            # Start the refresh
            refresh_id = self.client.start_refresh(workspace_id, dataset_id)

            logger.info(
                "Refresh started for dataset %s (refresh_id: %s). Monitoring status...",
                dataset_name,
                refresh_id
            )

            # Poll for status until completion or timeout
            final_status = self._poll_refresh_status(
                workspace_id,
                dataset_id,
                refresh_id
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Determine success and error message
            success = final_status == RefreshStatus.COMPLETED
            error_message = None

            if final_status == RefreshStatus.FAILED:
                error_message = "Refresh failed according to Power BI API"
            elif final_status == RefreshStatus.UNKNOWN:
                error_message = "Refresh status unknown"

            logger.info(
                "Refresh %s for dataset %s. Duration: %.2fs",
                "completed successfully" if success else "failed",
                dataset_name,
                duration
            )

            return RefreshResult(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                workspace_id=workspace_id,
                success=success,
                duration=duration,
                error_message=error_message,
                start_time=start_time,
                end_time=end_time
            )

        except RefreshTimeoutError as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(
                "Timeout waiting for refresh of dataset %s after %.2fs",
                dataset_name,
                duration
            )

            return RefreshResult(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                workspace_id=workspace_id,
                success=False,
                duration=duration,
                error_message=str(e),
                start_time=start_time,
                end_time=end_time
            )

        except PowerBIAPIError as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(
                "API error during refresh of dataset %s: %s",
                dataset_name,
                str(e)
            )

            return RefreshResult(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                workspace_id=workspace_id,
                success=False,
                duration=duration,
                error_message=f"API Error: {str(e)}",
                start_time=start_time,
                end_time=end_time
            )

        except Exception as e:  # noqa: BLE001
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(
                "Unexpected error during refresh of dataset %s: %s",
                dataset_name,
                str(e),
                exc_info=True
            )

            return RefreshResult(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                workspace_id=workspace_id,
                success=False,
                duration=duration,
                error_message=f"Unexpected error: {str(e)}",
                start_time=start_time,
                end_time=end_time
            )

    def _poll_refresh_status(
        self,
        workspace_id: str,
        dataset_id: str,
        refresh_id: str
    ) -> RefreshStatus:
        """
        Monitor refresh status until completion or timeout.

        Polls the Power BI API every poll_interval seconds to check
        the status of the refresh operation.

        Args:
            workspace_id: ID of the workspace
            dataset_id: ID of the dataset
            refresh_id: ID of the refresh operation

        Returns:
            Final RefreshStatus (COMPLETED, FAILED, or UNKNOWN)

        Raises:
            RefreshTimeoutError: If refresh exceeds timeout duration
        """
        start_time = time.time()
        elapsed = 0

        while elapsed < self.timeout:
            # Check current status
            status = self.client.get_refresh_status(
                workspace_id,
                dataset_id,
                refresh_id
            )

            logger.debug(
                "Refresh status for dataset %s: %s (elapsed: %.0fs)",
                dataset_id,
                status.value,
                elapsed
            )

            # Check if refresh is complete
            if status == RefreshStatus.COMPLETED:
                logger.info(
                    "Refresh completed successfully for dataset %s",
                    dataset_id
                )
                return status

            if status == RefreshStatus.FAILED:
                logger.error(
                    "Refresh failed for dataset %s",
                    dataset_id
                )
                return status

            # If still in progress, wait before next check
            if status == RefreshStatus.IN_PROGRESS:
                logger.debug(
                    "Refresh in progress for dataset %s. Waiting %ds before next check...",
                    dataset_id,
                    self.poll_interval
                )
                time.sleep(self.poll_interval)
                elapsed = time.time() - start_time
            else:
                # Unknown status - wait and retry
                logger.warning(
                    "Unknown refresh status for dataset %s. Waiting %ds before retry...",
                    dataset_id,
                    self.poll_interval
                )
                time.sleep(self.poll_interval)
                elapsed = time.time() - start_time

        # Timeout reached
        raise RefreshTimeoutError(
            f"Refresh timeout after {self.timeout}s for dataset {dataset_id}. "
            f"The refresh may still be running in Power BI."
        )
