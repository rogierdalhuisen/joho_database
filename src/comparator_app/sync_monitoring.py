"""
Sync monitoring and alerting utilities.

This module provides logging and alerting functionality for sync operations.
Can be extended to send emails, Slack notifications, or other alerts.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SyncMetrics:
    """
    Metrics for a sync operation.
    """
    sync_type: str  # 'egrip' or 'assuportal_relaties' or 'assuportal_contracten'
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    success_count: int = 0
    error_count: int = 0
    skipped_count: int = 0
    dry_run: bool = False

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate sync duration in seconds."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None

    @property
    def total_processed(self) -> int:
        """Total number of records processed."""
        return self.success_count + self.error_count + self.skipped_count

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        total = self.total_processed
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100

    def finish(self):
        """Mark sync as finished."""
        self.ended_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'sync_type': self.sync_type,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_seconds': self.duration_seconds,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'skipped_count': self.skipped_count,
            'total_processed': self.total_processed,
            'success_rate': f"{self.success_rate:.1f}%",
            'dry_run': self.dry_run,
        }


def log_sync_start(sync_type: str, dry_run: bool = False, **kwargs) -> SyncMetrics:
    """
    Log the start of a sync operation and return metrics tracker.

    Args:
        sync_type: Type of sync ('egrip', 'assuportal_relaties', etc.)
        dry_run: Whether this is a dry run
        **kwargs: Additional context to log

    Returns:
        SyncMetrics object to track the sync
    """
    metrics = SyncMetrics(sync_type=sync_type, dry_run=dry_run)

    context = {
        'sync_type': sync_type,
        'dry_run': dry_run,
        **kwargs
    }

    logger.info(f"Sync started: {sync_type}", extra=context)

    return metrics


def log_sync_complete(metrics: SyncMetrics, alert_on_errors: bool = True):
    """
    Log sync completion and alert if there were errors.

    Args:
        metrics: SyncMetrics object with sync results
        alert_on_errors: Whether to send alerts if errors occurred
    """
    metrics.finish()

    log_data = metrics.to_dict()

    # Determine log level
    if metrics.error_count == 0:
        log_level = logging.INFO
        status = "SUCCESS"
    elif metrics.error_count < metrics.success_count:
        log_level = logging.WARNING
        status = "PARTIAL_SUCCESS"
    else:
        log_level = logging.ERROR
        status = "FAILED"

    log_data['status'] = status

    # Log completion
    logger.log(
        log_level,
        f"Sync completed: {metrics.sync_type} - {status} "
        f"({metrics.success_count} success, {metrics.error_count} errors, "
        f"{metrics.skipped_count} skipped in {metrics.duration_seconds:.1f}s)",
        extra=log_data
    )

    # Alert on errors (can be extended to send emails/Slack notifications)
    if alert_on_errors and metrics.error_count > 0 and not metrics.dry_run:
        send_error_alert(metrics)


def send_error_alert(metrics: SyncMetrics):
    """
    Send alert about sync errors.

    Currently just logs a critical message.
    Can be extended to send emails, Slack notifications, etc.

    Args:
        metrics: SyncMetrics object with error details
    """
    alert_message = (
        f"ALERT: {metrics.sync_type} sync completed with {metrics.error_count} errors. "
        f"Success: {metrics.success_count}, Skipped: {metrics.skipped_count}. "
        f"Duration: {metrics.duration_seconds:.1f}s. "
        f"Success rate: {metrics.success_rate:.1f}%"
    )

    logger.critical(alert_message, extra=metrics.to_dict())

    # TODO: Extend this to send actual alerts:
    # - Email notifications
    # - Slack/Teams webhooks
    # - PagerDuty/Opsgenie integration
    # - Write to monitoring database


def log_validation_error(sync_type: str, record_id: str, error_details: str):
    """
    Log a validation error for a specific record.

    Args:
        sync_type: Type of sync operation
        record_id: Identifier of the record that failed
        error_details: Details of the validation error
    """
    logger.error(
        f"Validation error in {sync_type} for record {record_id}: {error_details}",
        extra={
            'sync_type': sync_type,
            'record_id': record_id,
            'error_type': 'validation_error',
            'error_details': error_details
        }
    )


def log_api_error(sync_type: str, endpoint: str, error_details: str):
    """
    Log an API communication error.

    Args:
        sync_type: Type of sync operation
        endpoint: API endpoint that failed
        error_details: Details of the API error
    """
    logger.error(
        f"API error in {sync_type} for endpoint {endpoint}: {error_details}",
        extra={
            'sync_type': sync_type,
            'endpoint': endpoint,
            'error_type': 'api_error',
            'error_details': error_details
        }
    )


# ============================================================================
# Usage Example (for documentation)
# ============================================================================

"""
Example usage in sync functions:

from .sync_monitoring import log_sync_start, log_sync_complete

def sync_egrip_formulieren(form_id: str = '2', dry_run: bool = False):
    # Start tracking
    metrics = log_sync_start('egrip', dry_run=dry_run, form_id=form_id)

    try:
        # ... do sync work ...

        for result in results:
            if success:
                metrics.success_count += 1
            elif skipped:
                metrics.skipped_count += 1
            else:
                metrics.error_count += 1

        return metrics.success_count, metrics.error_count, metrics.skipped_count

    finally:
        # Always log completion (even if exception occurs)
        log_sync_complete(metrics)
"""
