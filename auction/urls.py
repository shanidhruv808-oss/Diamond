from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.browse, name='browse'),
    path('diamonds/', views.diamonds, name='diamonds'),
    path('diamonds/<int:diamond_id>/', views.diamond_detail, name='diamond_detail'),
    path('diamond/<int:id>/', views.diamond_detail, name='diamond_detail_alt'),
    path('bid/', views.bid, name='bid'),
    path('place-bid/<int:id>/', views.place_bid, name='place_bid'),
    path('secure/', views.secure, name='secure'),
    path('api/place-bid/', views.place_bid_api, name='place_bid_api'),
    path('api/search-diamonds/', views.search_diamonds, name='search_diamonds'),
    path('auctions/', views.bid, name='auctions'),
    path('security/', views.secure, name='security'),
    
    # Winner declaration and payment URLs
    path('declare-winner/<int:diamond_id>/', views.declare_winner, name='declare_winner'),
    path('winner-dashboard/', views.winner_dashboard, name='winner_dashboard'),
    path('winner/<int:diamond_id>/', views.winner_page, name='winner_page'),
    path('api/create-payment-order/<int:diamond_id>/', views.create_payment_order, name='create_payment_order'),
    path('api/verify-payment/<int:diamond_id>/', views.verify_payment, name='verify_payment'),
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
    
    # Auth URLs - User Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Admin Authentication
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
]
