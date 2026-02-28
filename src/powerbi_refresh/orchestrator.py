"""Orchestrator for coordinating Power BI dataset refresh operations."""

import logging
from datetime import datetime
from typing import List

from .config import Config
from .models import ExecutionSummary, RefreshResult
from .refresh_manager import RefreshManager


logger = logging.getLogger(__name__)


class RefreshOrchestrator:
    """Orchestrates the refresh of multiple Power BI datasets."""

    def __init__(
        self,
        config: Config,
        refresh_manager: RefreshManager,
        logger_instance: logging.Logger
    ):
        """
        Initialize the orchestrator.

        Args:
            config: Configuration object with workspace and dataset information
            refresh_manager: RefreshManager instance for executing refreshes
            logger_instance: Logger instance for logging operations
        """
        self.config = config
        self.refresh_manager = refresh_manager
        self.logger = logger_instance

    def execute(self) -> ExecutionSummary:
        """
        Execute refresh operations for all configured datasets.

        This method processes all datasets across all configured workspaces.
        If specific dataset IDs are configured, only those are refreshed.
        Otherwise, all datasets in the workspaces are refreshed.

        The orchestrator continues processing even if individual refreshes fail,
        ensuring all datasets are attempted.

        Returns:
            ExecutionSummary with results for all refresh operations

        Raises:
            No exceptions are raised - all errors are captured in results
        """
        self.logger.info("Starting refresh orchestration")
        self.logger.info(
            "Configuration: %d workspace(s), poll_interval=%ds, timeout=%ds",
            len(self.config.workspace_ids),
            self.config.poll_interval,
            self.config.timeout
        )

        start_time = datetime.now()
        results: List[RefreshResult] = []

        # Determine which datasets to refresh
        datasets_to_refresh = self._get_datasets_to_refresh()

        self.logger.info(
            "Found %d dataset(s) to refresh",
            len(datasets_to_refresh)
        )

        # Check if we found any datasets
        if len(datasets_to_refresh) == 0:
            self.logger.error(
                "No datasets found to refresh. This may be due to:"
            )
            self.logger.error("  - Permission errors accessing workspaces")
            self.logger.error("  - Invalid workspace or dataset IDs")
            self.logger.error("  - Service principal not added to workspaces")
            self.logger.error(
                "  - Service principals not enabled in Power BI tenant settings"
            )
            self.logger.error(
                "Please check the logs above for specific errors and refer to docs/azure-setup.md"
            )

        # Process each dataset
        for workspace_id, dataset_id in datasets_to_refresh:
            self.logger.info(
                "Processing dataset %s in workspace %s",
                dataset_id,
                workspace_id
            )

            try:
                # Refresh the dataset
                result = self.refresh_manager.refresh_dataset(
                    workspace_id=workspace_id,
                    dataset_id=dataset_id
                )
                results.append(result)

                if result.success:
                    self.logger.info(
                        "Successfully refreshed dataset %s (duration: %.2fs)",
                        result.dataset_name,
                        result.duration
                    )
                else:
                    self.logger.error(
                        "Failed to refresh dataset %s: %s",
                        result.dataset_name,
                        result.error_message
                    )

            except Exception as e:  # noqa: BLE001
                # Catch any unexpected errors and continue with next dataset
                self.logger.error(
                    "Unexpected error processing dataset %s in workspace %s: %s",
                    dataset_id,
                    workspace_id,
                    str(e),
                    exc_info=True
                )

                # Create a failed result for this dataset
                error_result = RefreshResult(
                    dataset_id=dataset_id,
                    dataset_name=dataset_id,
                    workspace_id=workspace_id,
                    success=False,
                    duration=0.0,
                    error_message=f"Orchestration error: {str(e)}",
                    start_time=datetime.now(),
                    end_time=datetime.now()
                )
                results.append(error_result)

        # Calculate summary statistics
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        summary = ExecutionSummary(
            total_datasets=len(results),
            successful=successful,
            failed=failed,
            total_duration=total_duration,
            results=results
        )

        self.logger.info(
            "Orchestration complete: %d total, %d successful, %d failed (%.2fs)",
            summary.total_datasets,
            summary.successful,
            summary.failed,
            summary.total_duration
        )

        return summary

    def _get_datasets_to_refresh(self) -> List[tuple[str, str]]:
        """
        Determine which datasets to refresh based on configuration.

        If specific dataset IDs are configured, returns those with their
        corresponding workspace IDs. Otherwise, returns all datasets from
        all configured workspaces.

        Returns:
            List of (workspace_id, dataset_id) tuples
        """
        datasets: List[tuple[str, str]] = []

        if self.config.dataset_ids:
            # Specific datasets configured - refresh only those
            self.logger.debug(
                "Using configured dataset IDs: %s",
                ", ".join(self.config.dataset_ids)
            )

            # For each dataset, we need to find which workspace it belongs to
            # For now, we'll try each workspace until we find the dataset
            for dataset_id in self.config.dataset_ids:
                # Try to find the dataset in one of the configured workspaces
                found = False
                for workspace_id in self.config.workspace_ids:
                    try:
                        # Check if dataset exists in this workspace
                        workspace_datasets = self.refresh_manager.client.list_datasets(
                            workspace_id
                        )
                        dataset_ids_in_workspace = [
                            ds.get('id') for ds in workspace_datasets
                        ]

                        if dataset_id in dataset_ids_in_workspace:
                            datasets.append((workspace_id, dataset_id))
                            found = True
                            self.logger.debug(
                                "Found dataset %s in workspace %s",
                                dataset_id,
                                workspace_id
                            )
                            break

                    except Exception as e:  # noqa: BLE001
                        self.logger.error(
                            "Could not list datasets in workspace %s: %s",
                            workspace_id,
                            str(e)
                        )
                        # Check if it's a permission error
                        error_str = str(e).lower()
                        if "401" in error_str or "permission" in error_str or "unauthorized" in error_str:
                            self.logger.error(
                                "Permission denied for workspace %s. "
                                "Ensure the service principal has Member or Contributor role.",
                                workspace_id
                            )
                        continue

                if not found:
                    self.logger.error(
                        "Dataset %s not found in any configured workspace. "
                        "This may be due to permission errors or invalid dataset ID.",
                        dataset_id
                    )

        else:
            # No specific datasets - refresh all datasets in all workspaces
            self.logger.debug(
                "No specific datasets configured - will refresh all datasets in workspaces"
            )

            for workspace_id in self.config.workspace_ids:
                try:
                    workspace_datasets = self.refresh_manager.client.list_datasets(
                        workspace_id
                    )

                    for dataset in workspace_datasets:
                        dataset_id = dataset.get('id')
                        if dataset_id:
                            datasets.append((workspace_id, dataset_id))
                            self.logger.debug(
                                "Added dataset %s from workspace %s",
                                dataset.get('name', dataset_id),
                                workspace_id
                            )

                except Exception as e:  # noqa: BLE001
                    self.logger.error(
                        "Failed to list datasets in workspace %s: %s",
                        workspace_id,
                        str(e),
                        exc_info=True
                    )
                    continue

        return datasets
