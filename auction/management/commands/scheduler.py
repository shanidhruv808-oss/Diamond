import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run continuous scheduler for auction management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(f'Starting scheduler with {interval} second interval...')
        self.stdout.write('Press Ctrl+C to stop')
        
        try:
            while True:
                try:
                    self.stdout.write(f'[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Running auction checks...')
                    
                    # Check auction statuses
                    call_command('check_auctions')
                    
                    self.stdout.write(f'[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Check completed. Waiting {interval} seconds...')
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.stdout.write('\nScheduler stopped by user')
                    break
                except Exception as e:
                    logger.error(f'Scheduler error: {str(e)}')
                    self.stdout.write(f'Error occurred: {str(e)}. Continuing...')
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            self.stdout.write('\nScheduler stopped')
