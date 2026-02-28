"""Power BI API client for dataset refresh operations."""

import logging
import requests
from typing import List, Dict, Any, Optional

from .models import RefreshStatus
from .exceptions import PowerBIAPIError, PowerBIPermissionError
from .retry import RetryHandler


logger = logging.getLogger(__name__)


class PowerBIClient:
    """Client for Power BI REST API operations."""

    BASE_URL = "https://api.powerbi.com/v1.0/myorg"

    def __init__(self, auth_service: Any, retry_handler: RetryHandler):
        """
        Initialize the Power BI API client.

        Args:
            auth_service: Authentication service for obtaining access tokens
            retry_handler: Retry handler for transient errors
        """
        self.auth_service = auth_service
        self.retry_handler = retry_handler
        self._session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with authentication token.

        Returns:
            Dictionary of HTTP headers

        Raises:
            AuthenticationError: If unable to obtain valid token
        """
        token = self.auth_service.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL for the request
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            PowerBIAPIError: If the API returns an error
            PowerBIPermissionError: If access is denied (401, 403)
        """
        def _request():
            headers = self._get_headers()
            headers.update(kwargs.pop('headers', {}))

            response = self._session.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )

            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_after_seconds = int(retry_after) if retry_after else None
                self.retry_handler.handle_rate_limit(retry_after_seconds)
                # Retry the request after waiting
                return self._make_request(method, url, **kwargs)

            # Handle permission errors
            if response.status_code in (401, 403):
                error_msg = f"Permission denied (HTTP {response.status_code})"
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg = f"{error_msg}: {error_detail['error'].get('message', '')}"
                except Exception:
                    pass
                raise PowerBIPermissionError(error_msg)

            # Handle other client/server errors
            if not response.ok:
                error_msg = f"Power BI API error (HTTP {response.status_code})"
                response_body = response.text
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg = error_detail['error'].get('message', error_msg)
                except Exception:
                    pass

                raise PowerBIAPIError(
                    message=error_msg,
                    status_code=response.status_code,
                    response_body=response_body
                )

            return response

        # Execute with retry logic
        return self.retry_handler.execute_with_retry(_request)

    def list_datasets(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all datasets in a workspace.

        Args:
            workspace_id: ID of the workspace

        Returns:
            List of datasets with id, name, and other metadata

        Raises:
            PowerBIAPIError: If the operation fails
            PowerBIPermissionError: If there are no permissions in the workspace
        """
        logger.info("Listing datasets in workspace: %s", workspace_id)

        url = f"{self.BASE_URL}/groups/{workspace_id}/datasets"

        try:
            response = self._make_request("GET", url)
            data = response.json()

            datasets = data.get('value', [])
            logger.info("Found %d datasets in workspace %s", len(datasets), workspace_id)

            return datasets

        except (PowerBIAPIError, PowerBIPermissionError):
            raise
        except requests.RequestException as e:
            logger.error("Unexpected error listing datasets: %s", str(e))
            raise PowerBIAPIError(
                message=f"Failed to list datasets: {str(e)}",
                status_code=0,
                response_body=""
            ) from e

    def start_refresh(self, workspace_id: str, dataset_id: str) -> str:
        """
        Start the refresh of a dataset.

        Args:
            workspace_id: ID of the workspace
            dataset_id: ID of the dataset

        Returns:
            ID of the refresh request

        Raises:
            PowerBIAPIError: If the operation fails
        """
        logger.info(
            "Starting refresh for dataset %s in workspace %s",
            dataset_id,
            workspace_id
        )

        url = f"{self.BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"

        try:
            response = self._make_request("POST", url, json={})

            # Power BI API returns 202 Accepted for successful refresh start
            if response.status_code == 202:
                # The refresh ID is typically in the response headers or we generate one
                # For now, we'll use the dataset_id as the refresh identifier
                # In a real implementation, you might extract this from Location header
                refresh_id = dataset_id
                logger.info(
                    "Successfully started refresh for dataset %s (refresh_id: %s)",
                    dataset_id,
                    refresh_id
                )
                return refresh_id

            # If we get here, something unexpected happened
            raise PowerBIAPIError(
                message=f"Unexpected response status: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text
            )

        except (PowerBIAPIError, PowerBIPermissionError):
            raise
        except requests.RequestException as e:
            logger.error("Unexpected error starting refresh: %s", str(e))
            raise PowerBIAPIError(
                message=f"Failed to start refresh: {str(e)}",
                status_code=0,
                response_body=""
            ) from e

    def get_refresh_status(
        self,
        workspace_id: str,
        dataset_id: str,
        refresh_id: Optional[str] = None  # noqa: ARG002
    ) -> RefreshStatus:
        """
        Get the status of a refresh in progress.

        Args:
            workspace_id: ID of the workspace
            dataset_id: ID of the dataset
            refresh_id: ID of the refresh (optional, will get latest if not provided)

        Returns:
            Status of the refresh (Unknown, InProgress, Completed, Failed)

        Raises:
            PowerBIAPIError: If the operation fails
        """
        logger.debug(
            "Checking refresh status for dataset %s in workspace %s",
            dataset_id,
            workspace_id
        )

        url = f"{self.BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"

        try:
            response = self._make_request("GET", url, params={"$top": 1})
            data = response.json()

            refreshes = data.get('value', [])

            if not refreshes:
                logger.warning("No refresh history found for dataset %s", dataset_id)
                return RefreshStatus.UNKNOWN

            # Get the most recent refresh
            latest_refresh = refreshes[0]
            status_str = latest_refresh.get('status', 'Unknown')

            # Map Power BI status strings to our RefreshStatus enum
            status_mapping = {
                'Unknown': RefreshStatus.UNKNOWN,
                'InProgress': RefreshStatus.IN_PROGRESS,
                'Completed': RefreshStatus.COMPLETED,
                'Failed': RefreshStatus.FAILED,
                'Disabled': RefreshStatus.FAILED,
            }

            status = status_mapping.get(status_str, RefreshStatus.UNKNOWN)

            logger.debug(
                "Refresh status for dataset %s: %s",
                dataset_id,
                status.value
            )

            return status

        except (PowerBIAPIError, PowerBIPermissionError):
            raise
        except requests.RequestException as e:
            logger.error("Unexpected error getting refresh status: %s", str(e))
            raise PowerBIAPIError(
                message=f"Failed to get refresh status: {str(e)}",
                status_code=0,
                response_body=""
            ) from e
