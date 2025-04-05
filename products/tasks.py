import logging

from celery import shared_task
from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone

# Configure logging
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)  # 5 minutes
def rebuild_product_index_task(self, reason: str):
    """
    Celery task to rebuild the product index.
    Includes retry logic and prevents multiple simultaneous rebuilds.
    """
    logger.info("Starting product index rebuild task. Reason: %s", reason)

    # Check if rebuild is already in progress
    if cache.get("rebuild_index_scheduled"):
        logger.warning("Another rebuild is in progress. Retrying in 5 minutes. Reason: %s", reason)
        raise self.retry(
            exc=Exception("Another rebuild is in progress"), countdown=300  # Retry in 5 minutes
        )

    try:
        # Set rebuild in progress flag
        cache.set("rebuild_index_scheduled", True, timeout=300)  # 5 minutes timeout
        logger.info("Rebuild in progress flag set. Reason: %s", reason)

        # Perform the rebuild
        call_command("rebuild_product_index")
        logger.info("Product index rebuild completed successfully. Reason: %s", reason)

        # Log the rebuild reason with timestamp
        timestamp = timezone.now().isoformat()
        cache.set("last_rebuild_reason", f"{timestamp}: {reason}", timeout=86400)  # 24 hours
        logger.info("Rebuild reason logged: %s: %s", timestamp, reason)

    except Exception as e:
        # Clear the rebuild flag on error
        cache.delete("rebuild_index_scheduled")
        logger.error("Error during product index rebuild: %s. Reason: %s", str(e), reason)
        raise self.retry(exc=e)

    finally:
        # Always clear the rebuild flag when done
        cache.delete("rebuild_index_scheduled")
        logger.info("Rebuild in progress flag cleared. Reason: %s", reason)
