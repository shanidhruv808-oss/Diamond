from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_auction_statuses():
    """
    Periodic task to check and update auction statuses
    """
    try:
        logger.info("Starting auction status check...")
        call_command('check_auctions')
        logger.info("Auction status check completed successfully")
    except Exception as e:
        logger.error(f"Error in auction status check: {str(e)}")

@shared_task
def declare_winners():
    """
    Periodic task to declare winners for ended auctions
    """
    try:
        logger.info("Starting winner declaration...")
        call_command('declare_winners')
        logger.info("Winner declaration completed successfully")
    except Exception as e:
        logger.error(f"Error in winner declaration: {str(e)}")
