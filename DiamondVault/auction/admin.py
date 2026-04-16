from django.contrib import admin
from .models import Diamond, Auction, Bid


# 🔹 Diamond Admin
@admin.register(Diamond)
class DiamondAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'carat', 'color', 'clarity', 'cut', 'base_price')
    search_fields = ('name', 'color', 'clarity', 'cut')
    list_filter = ('color', 'clarity', 'cut')


# 🔹 Auction Admin
@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('id', 'diamond', 'start_time', 'end_time', 'status', 'winner', 'winning_bid')
    search_fields = ('diamond__name',)
    list_filter = ('status', 'start_time', 'end_time')
    readonly_fields = ('winner', 'winning_bid')

    def has_add_permission(self, request):
        # Prevent duplicate auction creation for same diamond
        return True


# 🔹 Bid Admin
@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'diamond', 'amount', 'timestamp')
    search_fields = ('user__username', 'diamond__name')
    list_filter = ('timestamp',)
    ordering = ('-amount',)


# # 🔹 Payment Admin
# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'auction', 'amount', 'status', 'payment_date')
#     search_fields = ('user__username',)
#     list_filter = ('status', 'payment_date')