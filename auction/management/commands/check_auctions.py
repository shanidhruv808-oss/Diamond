from django.core.management.base import BaseCommand
from django.utils import timezone
from auction.models import Diamond
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check and update auction statuses automatically'

    def handle(self, *args, **options):
        self.stdout.write('Checking auction statuses...')
        
        # Find auctions that have ended but are still active
        ended_auctions = Diamond.objects.filter(
            auction_end__lt=timezone.now(),
            auction_status='active'
        )
        
        count = ended_auctions.count()
        if count > 0:
            self.stdout.write(f'Found {count} auctions that need to be processed')
            
            # Run the declare_winners command for these auctions
            from django.core.management import call_command
            call_command('declare_winners')
            
            self.stdout.write(self.style.SUCCESS(f'Processed {count} ended auctions'))
        else:
            self.stdout.write('No auctions need processing')
        
        # Check for overdue payments
        overdue_payments = Diamond.objects.filter(
            auction_status='winner_declared',
            payment_deadline__lt=timezone.now()
        )
        
        overdue_count = overdue_payments.count()
        if overdue_count > 0:
            self.stdout.write(f'Found {overdue_count} overdue payments')
            
            for diamond in overdue_payments:
                diamond.auction_status = 'cancelled'
                diamond.save()
                self.stdout.write(f'Cancelled auction {diamond.name} due to overdue payment')
        
        self.stdout.write('Auction status check completed')
