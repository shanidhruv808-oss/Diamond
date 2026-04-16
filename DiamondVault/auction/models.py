from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# 🔹 Diamond Model
class Diamond(models.Model):
    name = models.CharField(max_length=100)
    carat = models.FloatField()
    color = models.CharField(max_length=10)
    clarity = models.CharField(max_length=10)
    cut = models.CharField(max_length=10)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='diamonds/', null=True, blank=True)

    def __str__(self):
        return self.name

    # ✅ Current price (highest bid or base price)
    def current_price(self):
        highest_bid = self.bids.first()
        return highest_bid.amount if highest_bid else self.base_price


# 🔹 Auction Model
class Auction(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('completed', 'Completed'),
    ]

    diamond = models.OneToOneField(Diamond, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    winning_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Auction for {self.diamond.name}"

    # ✅ Check if auction is currently active
    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_time <= now and self.end_time > now

    # ✅ Auto-close auction and assign winner
    def check_and_close(self):
        if self.end_time <= timezone.now() and self.status == 'active':
            highest_bid = self.diamond.bids.order_by('-amount').first()
            print(f"DEBUG: Auction {self.id} - Highest bid: {highest_bid}")
            if highest_bid:
                print(f"DEBUG: Assigning winner: {highest_bid.user}")
                self.winner = highest_bid.user
                self.winning_bid = highest_bid.amount
            self.status = 'ended'
            self.save()
            # Refresh from database to ensure winner is properly saved
            self.refresh_from_db()
            print(f"DEBUG: Saved winner: {self.winner}")
            print(f"DEBUG: Winner user after save: {self.winner.user if self.winner else None}")
            print(f"DEBUG: Winner user ID: {self.winner.user.id if self.winner else None}")


# 🔹 Bid Model
class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    diamond = models.ForeignKey(Diamond, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-amount']  # highest bid first

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount}"


# 🔹 Order Model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    diamond = models.ForeignKey('Diamond', on_delete=models.CASCADE)
    amount = models.FloatField()
    status = models.CharField(max_length=20, default='Pending')  # Pending, Paid
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.diamond.name}"
