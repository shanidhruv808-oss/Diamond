from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # ADD THIS (IMPORTANT)
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('debug/', views.debug_auctions, name='debug_auctions'),
    path('auctions/', views.diamonds, name='auctions'),

    path('diamonds/', views.diamonds, name='diamonds'),
    path('diamond/<int:id>/', views.diamond_detail, name='diamond_detail'),

    path('place_bid/<int:id>/', views.place_bid, name='place_bid'),

    #path('winner/', views.winner_page, name='winner_page'),
    path('winner-dashboard/', views.winner_dashboard, name='winner_dashboard'),

    # Payment URLs
    path('payment/<int:auction_id>/', views.payment_page, name='payment'),
    path('payment-success/<int:auction_id>/', views.payment_success, name='payment_success'),
    path('payment-failure/<int:auction_id>/', views.payment_failure, name='payment_failure'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('simulate-payment/', views.simulate_payment, name='simulate_payment'),

    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    ]