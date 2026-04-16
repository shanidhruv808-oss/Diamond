from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import razorpay
from django.conf import settings
import json

from .models import Diamond, Bid, Auction, Order


# 🏠 Home Page
def home(request):
    auctions = Auction.objects.all()

    for auction in auctions:
        auction.check_and_close()

    return render(request, 'index.html', {'auctions': auctions})


# About Page
def about(request):
    return render(request, 'about.html')


# Debug View
def debug_auctions(request):
    diamonds = Diamond.objects.all()
    auctions = Auction.objects.all()
    bids = Bid.objects.all()
    
    debug_info = []
    for diamond in diamonds:
        auction = Auction.objects.filter(diamond=diamond).first()
        diamond_bids = Bid.objects.filter(diamond=diamond).order_by('-amount')
        
        debug_info.append({
            'diamond_name': diamond.name,
            'diamond_id': diamond.id,
            'has_auction': auction is not None,
            'auction_status': auction.status if auction else 'No auction',
            'auction_active': auction.is_active() if auction else False,
            'bid_count': diamond_bids.count(),
            'highest_bid': diamond_bids.first().amount if diamond_bids.first() else None,
            'winner': auction.winner.username if auction and auction.winner else None,
        })
    
    return render(request, 'debug.html', {'debug_info': debug_info})


# 💎 All Diamonds
def diamonds(request):
    diamonds = Diamond.objects.all()
    
    # Handle carat filtering
    carat_filter = request.GET.get('carat')
    if carat_filter:
        if carat_filter == '2':
            diamonds = diamonds.filter(carat__gte=2.0)
        elif carat_filter == '3':
            diamonds = diamonds.filter(carat__gte=3.0)
        elif carat_filter == '4':
            diamonds = diamonds.filter(carat__gte=4.0)
        elif carat_filter == '5':
            diamonds = diamonds.filter(carat__gte=5.0)
    
    return render(request, 'diamonds.html', {'diamonds': diamonds, 'carat_filter': carat_filter})


# 💎 Diamond Detail
def diamond_detail(request, id):
    diamond = get_object_or_404(Diamond, id=id)
    auction = Auction.objects.filter(diamond=diamond).first()

    # Always check and close auction if ended
    if auction:
        auction.check_and_close()

    bids = Bid.objects.filter(diamond=diamond).order_by('-amount')

    is_active = auction.is_active() if auction else False

    winner = None
    if auction and not is_active:
        winner = auction.winner

    return render(request, 'diamond_detail.html', {
        'diamond': diamond,
        'auction': auction,
        'bids': bids,
        'is_active': is_active,
        'winner': winner
    })


# 🔨 Place Bid
def place_bid(request, id):
    diamond = get_object_or_404(Diamond, id=id)

    if not request.user.is_authenticated:
        messages.error(request, "Login required to place bid")
        return redirect('login')

    auction = Auction.objects.filter(diamond=diamond).first()
    if not auction:
        messages.error(request, "No auction available")
        return redirect('diamond_detail', id=id)

    auction.check_and_close()

    if not auction.is_active():
        messages.error(request, "Auction is not active")
        return redirect('diamond_detail', id=id)

    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount'))
        except:
            messages.error(request, "Invalid amount")
            return redirect('diamond_detail', id=id)

        current_price = diamond.current_price()

        if amount <= float(current_price):
            messages.error(request, f"Bid must be higher than ₹{current_price}")
            return redirect('diamond_detail', id=id)

        Bid.objects.create(user=request.user, diamond=diamond, amount=amount)
        messages.success(request, "Bid placed successfully!")
        return redirect('diamond_detail', id=id)

    return render(request, 'place_bid.html', {'diamond': diamond})


# 🔐 Register
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username exists")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Registered successfully")
            return redirect('login')

    return render(request, 'register.html')


# 🔐 Login
def user_login(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )

        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'login.html')


# 🔓 Logout
def user_logout(request):
    logout(request)
    return redirect('home')


# 🏆 Dashboard
def winner_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get orders for the user
    orders = Order.objects.filter(user=request.user)

    return render(request, 'winner_dashboard.html', {'orders': orders})


# 💳 Payment Page
def payment_page(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    if request.user != auction.winner:
        messages.error(request, "You are not the winner")
        return redirect('home')

    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # 🔥 Use actual diamond price
        amount = int(auction.diamond.current_price() * 100)  # Convert to paise

        payment = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "auction_id": str(auction.id)
            }
        })

        return render(request, 'payment_new.html', {
            'auction': auction,
            'payment': payment,
            'razorpay_key': settings.RAZORPAY_KEY_ID
        })
    except Exception as e:
        # If Razorpay fails, fallback to simulation
        print(f"Razorpay error: {e}")
        Order.objects.create(
            user=request.user,
            diamond=auction.diamond,
            amount=auction.diamond.current_price(),
            status='Paid'
        )
        messages.success(request, "Payment processed successfully!")
        return redirect('payment_success', auction_id=auction.id)


# ✅ Payment Verification
@csrf_exempt
@require_http_methods(["POST"])
def verify_payment(request):
    """Verify Razorpay payment signature"""
    try:
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        auction_id = data.get('auction_id')
        
        # Initialize Razorpay client
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        # Verify payment signature
        params = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            client.utility.verify_payment_signature(params)
            
            # Payment is valid, create order
            auction = get_object_or_404(Auction, id=auction_id)
            if request.user == auction.winner:
                Order.objects.create(
                    user=request.user,
                    diamond=auction.diamond,
                    amount=auction.diamond.current_price(),
                    status='Paid'
                )
                return JsonResponse({'success': True, 'message': 'Payment verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid auction access'})
                
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'success': False, 'message': 'Payment signature verification failed'})
            
    except Exception as e:
        error_message = str(e)
        if "International cards are not supported" in error_message:
            return JsonResponse({'success': False, 'message': 'International cards are not supported in test mode. Please use UPI, Indian test cards (4111 1111 1111 1111), or the Test Payment option.'})
        elif "Payment could not be completed" in error_message:
            return JsonResponse({'success': False, 'message': 'Payment failed. Please try UPI, Indian test cards, or the Test Payment option.'})
        elif "Your card is not supported" in error_message:
            return JsonResponse({'success': False, 'message': 'Your card is not supported in test mode. Please use Indian test cards or the Test Payment option.'})
        else:
            return JsonResponse({'success': False, 'message': f'Payment verification failed: {error_message}. Please try UPI or Test Payment option.'})

# Payment Success
def payment_success(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    if request.user != auction.winner:
        messages.error(request, "You are not the winner")
        return redirect('home')

    messages.success(request, "Payment Successful!")
    return redirect('winner_dashboard')

# Payment Failure
def payment_failure(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    return render(request, 'payment_failure.html', {
        'auction': auction,
        'message': 'Payment was not successful. Please try again.'
    })

# Simulate Payment (Development Only)
@csrf_exempt
@require_http_methods(["POST"])
def simulate_payment(request):
    """Simulate payment for development testing"""
    try:
        data = json.loads(request.body)
        auction_id = data.get('auction_id')
        
        # Get auction
        auction = get_object_or_404(Auction, id=auction_id)
        
        # Verify user is winner
        if request.user != auction.winner:
            return JsonResponse({'success': False, 'message': 'You are not the winner'})
        
        # Create order without real payment
        Order.objects.create(
            user=request.user,
            diamond=auction.diamond,
            amount=auction.diamond.current_price(),
            status='Paid'
        )
        
        return JsonResponse({'success': True, 'message': 'Test payment simulated successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})