from django.core.management.base import BaseCommand
from django.utils import timezone
from auction.models import Auction, Bid


class Command(BaseCommand):
    help = 'Declare winners for ended auctions'

    def handle(self, *args, **kwargs):
        auctions = Auction.objects.filter(
            status='active',
            end_time__lt=timezone.now()
        )

        if not auctions.exists():
            self.stdout.write("No auctions to process")
            return

        for auction in auctions:
            highest_bid = Bid.objects.filter(
                diamond=auction.diamond
            ).order_by('-amount').first()

            if highest_bid:
                auction.winner = highest_bid.user
                auction.winning_bid = highest_bid.amount
                auction.status = 'completed'
                auction.save()

                self.stdout.write(
                    f"Winner declared for {auction.diamond.name}: {highest_bid.user.username}"
                )
            else:
                auction.status = 'ended'
                auction.save()

                self.stdout.write(
                    f"No bids for {auction.diamond.name}"
                )