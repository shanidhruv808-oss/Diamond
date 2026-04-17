from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

class Diamond(models.Model):

    AUCTION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('winner_declared', 'Winner Declared'),
        ('payment_pending', 'Payment Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='diamonds/')
    carat = models.FloatField()
    color = models.CharField(max_length=10)
    clarity = models.CharField(max_length=20)
    cut = models.CharField(max_length=20)
    price = models.IntegerField()
    
    def auction_default():
        return timezone.now() + timedelta(days=30)

    auction_end = models.DateTimeField(default=auction_default)
    auction_status = models.CharField(
        max_length=20, 
        choices=AUCTION_STATUS_CHOICES, 
        default='active',
        help_text="Current status of the auction"
    )
    
    # Winner-related fields
    winner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='won_auctions',
        help_text="User who won this auction"
    )
    winning_bid = models.ForeignKey(
        'Bid', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='winning_auctions',
        help_text="The winning bid for this auction"
    )
    winner_declared_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When winner was declared"
    )
    payment_deadline = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Payment deadline for winner"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this diamond was last updated"
    )

    class Meta:
        verbose_name = "Diamond"
        verbose_name_plural = "Diamonds"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['auction_status', 'auction_end']),
            models.Index(fields=['winner']),
            models.Index(fields=['auction_end']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/diamonds/{self.id}/"

    def is_auction_active(self):
        """Check if auction is still active"""
        return self.auction_status == 'active' and self.auction_end > timezone.now()

    def get_highest_bid(self):
        """Get the highest bid for this diamond"""
        return self.bid_set.order_by('-amount').first()

    def declare_winner(self):
        """Declare winner for this auction"""
        if self.auction_status != 'active':
            logger.warning(f"Attempted to declare winner for non-active auction: {self.id}")
            return False

        highest_bid = self.get_highest_bid()
        
        if not highest_bid:
            # No bids - mark as ended without winner
            self.auction_status = 'ended'
            self.save()
            logger.info(f"Auction {self.id} ended with no bids")
            return True

        # Set winner
        self.winner = highest_bid.user
        self.winning_bid = highest_bid
        self.auction_status = 'winner_declared'
        self.winner_declared_at = timezone.now()
        self.payment_deadline = timezone.now() + timedelta(days=7)
        self.save()

        logger.info(f"Winner declared for auction {self.id}: {highest_bid.user.username}")
        return True

    def get_payment_status(self):
        """Get payment status for winner"""
        if not self.winner:
            return "No winner"
        elif self.auction_status == 'completed':
            return "Paid"
        elif self.auction_status == 'payment_pending':
            return "Payment pending"
        elif timezone.now() > self.payment_deadline:
            return "Payment overdue"
        else:
            return "Awaiting payment"

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    diamond = models.ForeignKey(Diamond, on_delete=models.CASCADE)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bid"
        verbose_name_plural = "Bids"
        ordering = ['-amount', 'created_at']
        indexes = [
            models.Index(fields=['diamond', '-amount']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount}"

    def is_winning_bid(self):
        """Check if this is the winning bid"""
        return self == self.diamond.get_highest_bid()

class AuctionHistory(models.Model):
    """Track auction history and winner declarations"""
    diamond = models.ForeignKey(Diamond, on_delete=models.CASCADE)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    winning_amount = models.IntegerField(null=True, blank=True)
    total_bids = models.IntegerField(default=0)
    ended_at = models.DateTimeField(auto_now_add=True)
    was_paid = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Auction History"
        verbose_name_plural = "Auction Histories"
        ordering = ['-ended_at']

    def __str__(self):
        return f"{self.diamond.name} - {self.winner.username if self.winner else 'No winner'}"

class Payment(models.Model):
    """Track Razorpay payments for won auctions"""
    PAYMENT_STATUS_CHOICES = [
        ('created', 'Payment Created'),
        ('pending', 'Payment Pending'),
        ('captured', 'Payment Captured'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Payment Refunded'),
    ]
    
    diamond = models.ForeignKey(Diamond, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    amount = models.IntegerField()  # Amount in paise (Razorpay uses paise)
    status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['diamond']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.diamond.name} - {self.status}"
    
    def get_amount_in_rupees(self):
        """Convert amount from paise to rupees"""
        return self.amount / 100

@receiver(post_save, sender=Diamond)
def log_auction_history(sender, instance, created, **kwargs):
    """Log auction history when auction ends"""
    if not created and instance.auction_status in ['ended', 'completed']:
        # Create history record if auction ended
        if not AuctionHistory.objects.filter(diamond=instance, ended_at=instance.winner_declared_at).exists():
            AuctionHistory.objects.create(
                diamond=instance,
                winner=instance.winner,
                winning_amount=instance.winning_bid.amount if instance.winning_bid else None,
                total_bids=instance.bid_set.count(),
                was_paid=instance.auction_status == 'completed'
            )