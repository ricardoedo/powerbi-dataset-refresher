"""Data models for Power BI refresh script."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class RefreshStatus(Enum):
    """Possible states of a refresh operation."""
    UNKNOWN = "Unknown"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class Dataset:
    """Represents a Power BI dataset."""
    id: str
    name: str
    workspace_id: str
    configured_by: Optional[str] = None
    is_refreshable: bool = True


@dataclass
class Workspace:
    """Represents a Power BI workspace."""
    id: str
    name: str
    type: str  # "Workspace" or "Group"


@dataclass
class RefreshRequest:
    """Refresh request information."""
    workspace_id: str
    dataset_id: str
    request_id: str
    start_time: datetime


@dataclass
class RefreshHistory:
    """History of a refresh operation."""
    refresh_id: str
    status: RefreshStatus
    start_time: datetime
    end_time: Optional[datetime]
    error_message: Optional[str]


@dataclass
class RefreshResult:
    """Result of a refresh operation."""
    dataset_id: str
    dataset_name: str
    workspace_id: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for serialization.
        
        Returns:
            Dictionary representation of the result
        """
        return {
            'dataset_id': self.dataset_id,
            'dataset_name': self.dataset_name,
            'workspace_id': self.workspace_id,
            'success': self.success,
            'duration': self.duration,
            'error_message': self.error_message,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }
    
    def to_text(self) -> str:
        """
        Generate human-readable text representation.
        
        Returns:
            Formatted text string
        """
        status = "SUCCESS" if self.success else "FAILED"
        text = f"[{status}] {self.dataset_name} (ID: {self.dataset_id})\n"
        text += f"  Workspace: {self.workspace_id}\n"
        text += f"  Duration: {self.duration:.2f}s\n"
        text += f"  Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if self.end_time:
            text += f"  End: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if self.error_message:
            text += f"  Error: {self.error_message}\n"
        
        return text


@dataclass
class ExecutionSummary:
    """Summary of script execution."""
    total_datasets: int
    successful: int
    failed: int
    total_duration: float
    results: List[RefreshResult]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert summary to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the summary
        """
        return {
            'total_datasets': self.total_datasets,
            'successful': self.successful,
            'failed': self.failed,
            'total_duration': self.total_duration,
            'results': [result.to_dict() for result in self.results]
        }
    
    def to_text(self) -> str:
        """
        Generate human-readable summary report.
        
        Returns:
            Formatted text report
        """
        text = "=" * 60 + "\n"
        text += "EXECUTION SUMMARY\n"
        text += "=" * 60 + "\n\n"
        
        text += f"Total Datasets: {self.total_datasets}\n"
        text += f"Successful: {self.successful}\n"
        text += f"Failed: {self.failed}\n"
        text += f"Total Duration: {self.total_duration:.2f}s\n\n"
        
        if self.results:
            text += "RESULTS:\n"
            text += "-" * 60 + "\n"
            for result in self.results:
                text += result.to_text()
                text += "-" * 60 + "\n"
        
        return text
