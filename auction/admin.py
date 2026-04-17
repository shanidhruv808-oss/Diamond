from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Diamond, Bid, AuctionHistory
from django.utils import timezone
from datetime import timedelta

@admin.register(Diamond)
class DiamondAdmin(admin.ModelAdmin):
    list_display = ('name', 'carat', 'color', 'clarity', 'cut', 'price', 'auction_status', 'winner', 'auction_end')
    list_filter = ('auction_status', 'color', 'clarity', 'cut', 'auction_end')
    search_fields = ('name', 'winner__username')
    list_editable = ('carat', 'color', 'clarity', 'cut', 'price')
    readonly_fields = ('winner', 'winning_bid', 'winner_declared_at', 'payment_deadline')
    date_hierarchy = 'auction_end'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'carat', 'color', 'clarity', 'cut', 'price')
        }),
        ('Auction Details', {
            'fields': ('auction_end', 'auction_status', 'image')
        }),
        ('Winner Information', {
            'fields': ('winner', 'winning_bid', 'winner_declared_at', 'payment_deadline'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['declare_winner_action', 'mark_as_completed', 'extend_auction']
    
    def winner(self, obj):
        if obj.winner:
            url = reverse('admin:auth_user_change', args=[obj.winner.id])
            return format_html('<a href="{}">{}</a>', url, obj.winner.username)
        return '-'
    winner.short_description = 'Winner'
    
    def declare_winner_action(self, request, queryset):
        """Admin action to declare winners"""
        count = 0
        for diamond in queryset:
            if diamond.auction_status == 'active' and diamond.auction_end <= timezone.now():
                if diamond.declare_winner():
                    count += 1
        
        self.message_user(request, f'Successfully declared {count} winner(s).')
    declare_winner_action.short_description = 'Declare winner for selected auctions'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected auctions as completed"""
        updated = queryset.update(auction_status='completed')
        self.message_user(request, f'Marked {updated} auction(s) as completed.')
    mark_as_completed.short_description = 'Mark as completed'
    
    def extend_auction(self, request, queryset):
        """Extend auction end time by 7 days"""
        updated = queryset.update(auction_end=timezone.now() + timedelta(days=7))
        self.message_user(request, f'Extended {updated} auction(s) by 7 days.')
    extend_auction.short_description = 'Extend auction by 7 days'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'payment_min' in request.GET:
            qs = qs.filter(price__gte=request.GET['payment_min'])
        if 'payment_max' in request.GET:
            qs = qs.filter(price__lte=request.GET['payment_max'])
        return qs.select_related('winner', 'winning_bid')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('user', 'diamond', 'amount', 'created_at', 'is_winning_bid')
    list_filter = ('diamond', 'created_at', 'amount')
    search_fields = ('user__username', 'diamond__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def is_winning_bid(self, obj):
        if obj.is_winning_bid():
            return format_html('<span style="color: green;">✓ Winning</span>')
        return '-'
    is_winning_bid.short_description = 'Winning Bid'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'diamond')

@admin.register(AuctionHistory)
class AuctionHistoryAdmin(admin.ModelAdmin):
    list_display = ('diamond', 'winner', 'winning_amount', 'total_bids', 'ended_at', 'was_paid')
    list_filter = ('was_paid', 'ended_at')
    search_fields = ('diamond__name', 'winner__username')
    readonly_fields = ('diamond', 'winner', 'winning_amount', 'total_bids', 'ended_at')
    date_hierarchy = 'ended_at'
    
    def has_add_permission(self, request):
        return False  # History should not be manually added
    
    def has_change_permission(self, request, obj=None):
        return False  # History should not be changed