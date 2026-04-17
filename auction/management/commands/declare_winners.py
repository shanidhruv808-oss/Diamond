from django.core.management.base import BaseCommand
from django.utils import timezone
from auction.models import Diamond, Bid, AuctionHistory
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Declare winners for ended auctions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run command without actually declaring winners',
        )
        parser.add_argument(
            '--diamond-id',
            type=int,
            help='Declare winner for specific diamond ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        diamond_id = options.get('diamond_id')
        
        self.stdout.write(self.style.SUCCESS('Starting winner declaration process...'))
        
        if diamond_id:
            # Process specific diamond
            diamonds = Diamond.objects.filter(id=diamond_id)
            self.stdout.write(f"Processing specific diamond ID: {diamond_id}")
        else:
            # Process all ended active auctions
            diamonds = Diamond.objects.filter(
                auction_end__lt=timezone.now(),
                auction_status='active'
            )
            self.stdout.write(f"Found {diamonds.count()} auctions to process")
        
        winners_declared = 0
        auctions_ended = 0
        errors = 0

        for diamond in diamonds:
            try:
                if dry_run:
                    self.stdout.write(f"[DRY RUN] Would process: {diamond.name}")
                    continue

                # Declare winner
                if diamond.declare_winner():
                    winners_declared += 1
                    
                    # Send notification to winner
                    if diamond.winner:
                        self.send_winner_notification(diamond)
                        
                        # Send notifications to losers (optional)
                        self.send_loser_notifications(diamond)
                        
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"SUCCESS: Winner declared for {diamond.name}: {diamond.winner.username if diamond.winner else 'No bids'}"
                        )
                    )
                else:
                    auctions_ended += 1
                    self.stdout.write(
                        self.style.WARNING(f"WARNING: Auction ended with no bids: {diamond.name}")
                    )
                    
            except Exception as e:
                errors += 1
                logger.error(f"Error processing auction {diamond.id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"ERROR: Error processing {diamond.name}: {str(e)}")
                )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== SUMMARY ==='))
        self.stdout.write(f"Winners declared: {winners_declared}")
        self.stdout.write(f"Auctions ended (no bids): {auctions_ended}")
        self.stdout.write(f"Errors: {errors}")
        self.stdout.write(f"Total processed: {winners_declared + auctions_ended + errors}")

    def send_winner_notification(self, diamond):
        """Send email notification to winner"""
        try:
            subject = f'🎉 Congratulations! You won the auction for {diamond.name}'
            
            message = f'''
Dear {diamond.winner.username},

Congratulations! You have won the auction for {diamond.name}.

📋 Auction Details:
• Diamond: {diamond.name}
• Carat: {diamond.carat}
• Color: {diamond.color}
• Clarity: {diamond.clarity}
• Cut: {diamond.cut}
• Winning Amount: ₹{diamond.winning_bid.amount}

💳 Payment Information:
• Payment Deadline: {diamond.payment_deadline.strftime('%B %d, %Y at %I:%M %p')}
• Amount Due: ₹{diamond.winning_bid.amount}

📞 Next Steps:
1. Login to your DiamondVault account
2. Go to "Won Auctions" in your dashboard
3. Complete payment within 7 days
4. Receive your certified diamond

⚠️ Important:
- Payment must be completed within 7 days
- If payment is not received, the auction may be re-listed
- All diamonds come with certification and insurance

Thank you for choosing DiamondVault!

Best regards,
DiamondVault Team
            '''.strip()

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [diamond.winner.email],
                fail_silently=False,
            )
            
            logger.info(f"Winner notification sent to {diamond.winner.email}")
            
        except Exception as e:
            logger.error(f"Failed to send winner notification: {str(e)}")

    def send_loser_notifications(self, diamond):
        """Send email notifications to losing bidders (optional)"""
        try:
            losing_bidders = Bid.objects.filter(
                diamond=diamond
            ).exclude(user=diamond.winner).values_list('user__email', flat=True).distinct()
            
            if not losing_bidders:
                return

            subject = f'Auction ended: {diamond.name}'
            
            message = f'''
Dear Bidder,

The auction for {diamond.name} has ended.

Unfortunately, you were not the winning bidder.
The winning bid was ₹{diamond.winning_bid.amount}.

Thank you for participating in DiamondVault auctions.
We invite you to browse other active auctions on our website.

Best regards,
DiamondVault Team
            '''.strip()

            for email in losing_bidders:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,  # Don't fail if loser emails fail
                )
            
            logger.info(f"Loser notifications sent for {diamond.name}")
            
        except Exception as e:
            logger.error(f"Failed to send loser notifications: {str(e)}")
