from django.shortcuts import render, get_object_or_404,redirect
from .models import Diamond,Bid,Payment
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

def get_razorpay_client():
    """Import and initialize Razorpay client when available."""
    try:
        import razorpay
    except ModuleNotFoundError:
        return None, None

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    return razorpay, client

# Create your views here.
def home(request):
    """Home page view"""
    return render(request, 'index.html')

def diamonds(request):
    """Diamonds collection page view"""
    diamonds = Diamond.objects.all()
    return render(request, 'diamonds.html', {'diamonds': diamonds})

def browse(request):
    """Browse diamonds page view"""
    return render(request, 'browse.html')

def bid(request):
    """Bidding page view"""
    return render(request, 'bid.html')

def secure(request):
    """Security and insurance page view"""
    return render(request, 'secure.html')

def place_bid_api(request):
    """Handle bid placement via AJAX"""
    return JsonResponse({'success': False, 'message': 'Static page - bid functionality not implemented'})

def search_diamonds(request):
    """Handle diamond search via AJAX"""
    if request.method == 'GET':
        diamonds = [
            {
                'id': 1,
                'name': 'Round Brilliant',
                'carat': 2.5,
                'color': 'D',
                'clarity': 'VVS1',
                'cut': 'Excellent',
                'price': 50000,
                'image': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400&h=300&fit=crop',
                'certification': 'GIA',
                'time_left': '2h 45m',
                'rating': 5
            }
        ]
        
        return JsonResponse({
            'success': True,
            'diamonds': diamonds,
            'total_count': len(diamonds)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def declare_winner(request, diamond_id):
    """Manual winner declaration view"""
    diamond = get_object_or_404(Diamond, id=diamond_id)
    
    # Check if user has permission (admin or staff)
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to declare winners.')
        return redirect('admin:auction_diamond_changelist')
    
    if diamond.auction_status != 'active':
        messages.warning(request, f'Auction is not active. Current status: {diamond.get_auction_status_display()}')
        return redirect('admin:auction_diamond_changelist')
    
    if diamond.auction_end > timezone.now():
        messages.warning(request, 'Auction has not ended yet.')
        return redirect('admin:auction_diamond_changelist')
    
    if diamond.declare_winner():
        messages.success(request, f'Winner declared successfully: {diamond.winner.username}')
    else:
        messages.error(request, 'Failed to declare winner.')
    
    return redirect('admin:auction_diamond_changelist')

@login_required
def winner_dashboard(request):
    """Winner dashboard for users to see their won auctions"""
    # Get auctions user has won
    won_auctions = Diamond.objects.filter(winner=request.user).order_by('-winner_declared_at')
    
    # Separate by status
    payment_pending = won_auctions.filter(auction_status='payment_pending')
    completed = won_auctions.filter(auction_status='completed')
    overdue = won_auctions.filter(
        auction_status='payment_pending',
        payment_deadline__lt=timezone.now()
    )
    
    context = {
        'won_auctions': won_auctions,
        'payment_pending': payment_pending,
        'completed': completed,
        'overdue': overdue,
        'total_won': won_auctions.count(),
        'total_value': sum(d.winning_bid.amount for d in won_auctions if d.winning_bid),
    }
    
    return render(request, 'winner_dashboard.html', context)

@csrf_exempt
@require_POST
def create_payment_order(request, diamond_id):
    """Create Razorpay order for payment"""
    diamond = get_object_or_404(Diamond, id=diamond_id)
    
    # Validate user is the winner
    if diamond.winner != request.user:
        return JsonResponse({
            'success': False,
            'message': 'You are not the winner of this auction.'
        })
    
    if diamond.auction_status != 'winner_declared':
        return JsonResponse({
            'success': False,
            'message': 'This auction is not ready for payment.'
        })
    
    razorpay, client = get_razorpay_client()
    if client is None:
        return JsonResponse({
            'success': False,
            'message': 'Razorpay is not installed or available. Please activate the correct environment and install razorpay.'
        })

    try:
        # Amount in paise (Razorpay uses paise)
        amount = diamond.winning_bid.amount * 100
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1',
            'notes': {
                'diamond_id': diamond.id,
                'user_id': request.user.id,
                'diamond_name': diamond.name
            }
        })
        
        # Create payment record
        payment = Payment.objects.create(
            diamond=diamond,
            user=request.user,
            razorpay_order_id=razorpay_order['id'],
            amount=amount,
            status='created'
        )
        
        return JsonResponse({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': amount,
            'key': settings.RAZORPAY_KEY_ID,
            'name': 'DiamondVault',
            'description': f'Payment for {diamond.name}',
            'prefill': {
                'name': request.user.username,
                'email': request.user.email
            },
            'notes': {
                'diamond_id': diamond.id,
                'payment_id': payment.id
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to create payment order: {str(e)}'
        })

@csrf_exempt
@require_POST
def verify_payment(request, diamond_id):
    """Verify Razorpay payment and update auction status"""
    diamond = get_object_or_404(Diamond, id=diamond_id)
    
    # Validate user is the winner
    if diamond.winner != request.user:
        return JsonResponse({
            'success': False,
            'message': 'You are not the winner of this auction.'
        })
    
    try:
        payment_data = json.loads(request.body)
        razorpay_order_id = payment_data.get('razorpay_order_id')
        razorpay_payment_id = payment_data.get('razorpay_payment_id')
        razorpay_signature = payment_data.get('razorpay_signature')
        
        razorpay, client = get_razorpay_client()
        if client is None:
            return JsonResponse({
                'success': False,
                'message': 'Razorpay is not installed or available. Please activate the correct environment and install razorpay.'
            })
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({
                'success': False,
                'message': 'Payment verification failed. Invalid signature.'
            })
        
        # Update payment record
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'captured'
        payment.save()
        
        # Update diamond status
        diamond.auction_status = 'completed'
        diamond.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment verified successfully!',
            'redirect_url': reverse('winner_dashboard')
        })
        
    except Payment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment record not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Payment verification failed: {str(e)}'
        })

@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhooks for payment status updates"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        webhook_data = json.loads(request.body)
        event = webhook_data.get('event')
        
        razorpay, client = get_razorpay_client()
        if client is None:
            return HttpResponse(status=503)
        
        # Verify webhook signature
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET  # Add this to settings
        received_signature = request.headers.get('X-Razorpay-Signature')
        
        try:
            client.utility.verify_webhook_signature(request.body, received_signature, webhook_secret)
        except:
            return HttpResponse(status=400)
        
        # Handle different webhook events
        if event == 'payment.captured':
            payment_entity = webhook_data.get('payload', {}).get('payment', {})
            order_id = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            
            # Update payment record
            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.razorpay_payment_id = payment_id
                payment.status = 'captured'
                payment.save()
                
                # Update diamond status
                payment.diamond.auction_status = 'completed'
                payment.diamond.save()
                
            except Payment.DoesNotExist:
                pass
        
        elif event == 'payment.failed':
            payment_entity = webhook_data.get('payload', {}).get('payment', {})
            order_id = payment_entity.get('order_id')
            
            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.status = 'failed'
                payment.save()
            except Payment.DoesNotExist:
                pass
        
        return HttpResponse(status=200)
        
    except Exception as e:
        return HttpResponse(status=400)

def diamond_detail(request, diamond_id):
    """Detailed view for a single diamond"""
    diamond = get_object_or_404(Diamond, id=diamond_id)
    bids = Bid.objects.filter(diamond=diamond).order_by('-amount')[:10]
    
    context = {
        'diamond': diamond,
        'bids': bids,
        'is_winning_bid': False,  # Would check if current user has winning bid
        'now': timezone.now(),  # Add current time for template
    }
    
    return render(request, 'diamond_detail.html', context)

def winner_page(request, diamond_id):
    """Winner announcement page for a specific diamond"""
    diamond = get_object_or_404(Diamond, id=diamond_id)
    
    context = {
        'diamond': diamond,
        'winner': diamond.winner,
        'winning_bid': diamond.winning_bid,
    }
    
    return render(request, 'winner_page.html', context)

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists")
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, "Account created successfully")
                return redirect('login')
        else:
            messages.error(request, "Passwords do not match")

    return render(request, 'register.html')

def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Check if user came from admin or frontend
            next_url = request.POST.get('next', request.GET.get('next', ''))
            if next_url:
                return redirect(next_url)
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')


# Logout
@csrf_protect
def user_logout(request):
    logout(request)
    return redirect('login')

# Admin Authentication Views
@csrf_protect
def admin_login(request):
    """Custom admin login view that handles non-staff users"""
    # If user is already logged in as regular user, show error
    if request.user.is_authenticated and not request.user.is_staff:
        messages.error(request, f"'{request.user.username}' is not an admin account. Please logout and login with admin credentials.")
        return redirect('login')
    
    # If user is already logged in as staff, redirect to admin panel
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/admin/')
    
    # Otherwise, redirect to Django admin login
    return redirect('/admin/login/')

@csrf_protect
def admin_logout(request):
    """Admin logout view"""
    logout(request)
    return redirect('admin_login')

@login_required
def place_bid(request, id):

    diamond = get_object_or_404(Diamond, id=id)

    if request.method == "POST":
        try:
            amount = int(request.POST['amount'])
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid bid amount!")
            return render(request, 'place_bid.html', {'diamond': diamond})

        if amount <= diamond.price:
            messages.error(request, f"Bid must be higher than current price of ₹{diamond.price}!")
            return render(request, 'place_bid.html', {'diamond': diamond})

        if amount <= 0:
            messages.error(request, "Bid amount must be positive!")
            return render(request, 'place_bid.html', {'diamond': diamond})

        # Check if auction is still active
        if not diamond.is_auction_active:
            messages.error(request, "This auction has ended!")
            return render(request, 'place_bid.html', {'diamond': diamond})

        Bid.objects.create(
            user=request.user,
            diamond=diamond,
            amount=amount
        )

        diamond.price = amount
        diamond.save()

        messages.success(request, f"Bid of ₹{amount} placed successfully!")
        return redirect('diamond_detail', diamond_id=id)

    return render(request, 'place_bid.html', {'diamond': diamond})

def winner_summary(request, diamond_id):

    diamond = get_object_or_404(Diamond, id=diamond_id)
    highest_bid = diamond.get_highest_bid()

    context = {
        'diamond': diamond,
        'winner': highest_bid.user if highest_bid else None,
        'amount': highest_bid.amount if highest_bid else None
    }

    return render(request, 'winner.html', context)