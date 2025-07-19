from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from .models import FAQComment, Booking, TrainingPackage, Weapon, Instructor, Testimonial, RangeLocation
from .forms import (FAQCommentForm, BookingForm, QuickBookingForm, 
                   TestimonialForm, ContactForm, PackageFilterForm,
                   AvailabilityCheckForm)

def home(request):
    """Homepage view with featured packages and testimonials"""
    featured_packages = TrainingPackage.objects.filter(is_active=True).order_by('?')[:3]
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')[:4]
    
    context = {
        'featured_packages': featured_packages,
        'testimonials': testimonials,
    }
    return render(request, 'lessons/home.html', context)

def packages(request):
    """View for listing all training packages"""
    packages = TrainingPackage.objects.filter(is_active=True)
    
    # Handle filtering
    filter_form = PackageFilterForm(request.GET)
    if filter_form.is_valid():
        duration = filter_form.cleaned_data.get('duration')
        price_range = filter_form.cleaned_data.get('price_range')
        sort_by = filter_form.cleaned_data.get('sort_by')
        
        if duration:
            packages = packages.filter(duration=duration)
        
        if price_range:
            min_price, max_price = price_range.split('-') if '-' in price_range else (price_range, None)
            if min_price:
                packages = packages.filter(price__gte=min_price)
            if max_price:
                packages = packages.filter(price__lte=max_price)
        
        if sort_by:
            packages = packages.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(packages, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
    }
    return render(request, 'lessons/packages.html', context)

def package_detail(request, pk):
    """Detailed view for a single training package"""
    package = get_object_or_404(TrainingPackage, pk=pk, is_active=True)
    related_packages = TrainingPackage.objects.filter(
        is_active=True
    ).exclude(pk=pk).order_by('?')[:3]
    
    context = {
        'package': package,
        'related_packages': related_packages,
    }
    return render(request, 'lessons/package_detail.html', context)

def booking(request):
    """Main booking view with form handling"""
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            
            if request.user.is_authenticated:
                booking.user = request.user
            
            # Calculate total price
            package = form.cleaned_data['package']
            duration = form.cleaned_data['duration']
            booking.amount_paid = package.price * (duration / package.duration)
            
            # Handle payment method
            payment_method = form.cleaned_data['payment_method']
            if payment_method == 'paypal':
                # Redirect to PayPal payment flow
                return redirect('process_payment', booking_id=booking.id)
            else:
                # For cash payments, mark as pending
                booking.payment_status = 'pending'
                booking.save()
                messages.success(request, 'Your booking has been submitted!')
                return redirect('booking_confirmation', booking_id=booking.id)
    else:
        form = BookingForm(user=request.user)
    
    # Get available weapons and packages
    weapons = Weapon.objects.filter(is_active=True)
    packages = TrainingPackage.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'weapons': weapons,
        'packages': packages,
    }
    return render(request, 'lessons/booking.html', context)

def quick_booking(request):
    """Simplified booking flow"""
    if request.method == 'POST':
        form = QuickBookingForm(request.POST)
        if form.is_valid():
            request.session['quick_booking_data'] = {
                'package_id': form.cleaned_data['package'].id,
                'date': form.cleaned_data['date'].isoformat(),
            }
            return redirect('booking')
    else:
        form = QuickBookingForm()
    
    return render(request, 'lessons/quick_booking.html', {'form': form})

def booking_confirmation(request, booking_id):
    """Booking confirmation page"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Verify user owns this booking if logged in
    if request.user.is_authenticated and booking.user != request.user:
        messages.error(request, "You don't have permission to view this booking.")
        return redirect('home')
    
    context = {
        'booking': booking,
    }
    return render(request, 'lessons/booking_confirmation.html', context)

def check_availability(request):
    """AJAX endpoint for checking available time slots"""
    if request.method == 'POST':
        form = AvailabilityCheckForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            package = form.cleaned_data.get('package')
            
            # Get existing bookings for this date
            existing_bookings = Booking.objects.filter(
                date=date,
                is_confirmed=True
            ).values_list('time', flat=True)
            
            # Generate available time slots (simplified example)
            available_slots = [
                '09:00', '10:30', '12:00', '13:30', '15:00', '16:30', '18:00'
            ]
            
            # Filter out booked slots
            available_slots = [slot for slot in available_slots if slot not in existing_bookings]
            
            return JsonResponse({
                'success': True,
                'available_slots': available_slots,
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def about(request):
    """About page with instructor information"""
    instructors = Instructor.objects.filter(is_active=True).annotate(
        num_reviews=Count('testimonials')
    ).order_by('-years_experience')
    
    context = {
        'instructors': instructors,
    }
    return render(request, 'lessons/about.html', context)

def instructor_detail(request, pk):
    """Detailed view for an instructor"""
    instructor = get_object_or_404(Instructor, pk=pk, is_active=True)
    testimonials = Testimonial.objects.filter(
        user__instructor_profile=instructor,
        is_approved=True
    ).order_by('-created_at')[:5]
    
    context = {
        'instructor': instructor,
        'testimonials': testimonials,
    }
    return render(request, 'lessons/instructor_detail.html', context)

def faq(request):
    """FAQ page with static questions and user comments"""
    # Static FAQ questions
    faqs = [
        {"q": "Do I need to bring my own firearm or ammo?", 
         "a": "No. All necessary firearms, ammunition, eye and ear protection, and targets are provided."},
        {"q": "Is it safe for beginners with no experience?", 
         "a": "Absolutely. Our lessons are tailored for beginners with step-by-step safety instruction."},
        {"q": "Do you offer training for couples or small groups?", 
         "a": "Yes, we specialize in couples training and small group sessions upon request."},
        {"q": "What should I wear to the lesson?", 
         "a": "Closed-toe shoes and modest, comfortable clothes. Avoid low-cut tops or loose clothing."},
        {"q": "How long is each lesson?", 
         "a": "Each lesson is typically 60-90 minutes depending on your selected package."},
        {"q": "Is there an age requirement?", 
         "a": "Participants must be 18+. Teens (13-17) may join with parental permission."},
        {"q": "Where is the training location?", 
         "a": "Private range in Los Angeles. Full details provided after booking."},
        {"q": "Do I need a firearm license or permit?", 
         "a": "No permit is required. All instruction is legal and supervised."},
    ]

    # Get all active parent comments (not replies) ordered by newest first
    comments = FAQComment.objects.filter(parent__isnull=True, is_active=True).order_by('-created_at')

    # Handle comment submission
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to post a comment.")
            return redirect('login?next=' + request.path)
        
        form = FAQCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.is_active = True
            
            # Handle parent comment if this is a reply
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = FAQComment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except FAQComment.DoesNotExist:
                    messages.error(request, "Invalid comment reference.")
                    return redirect('faq')
            
            comment.save()
            messages.success(request, "Your comment has been posted successfully!")
            return redirect('faq')
    else:
        form = FAQCommentForm()

    context = {
        'faqs': faqs,
        'comments': comments,
        'form': form,
    }
    return render(request, 'lessons/faq.html', context)

def contact(request):
    """Contact page with form submission"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In a real app, you would send an email here
            messages.success(request, "Thank you for your message! We'll respond within 24 hours.")
            return redirect('contact')
    else:
        form = ContactForm()
    
    locations = RangeLocation.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'locations': locations,
    }
    return render(request, 'lessons/contact.html', context)

def legal(request):
    """Legal information page"""
    return render(request, 'lessons/legal.html')

def privacy(request):
    """Privacy policy page"""
    return render(request, 'lessons/privacy.html')

def testimonials(request):
    """View all testimonials"""
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.user = request.user
            testimonial.save()
            messages.success(request, "Thank you for your testimonial! It will be reviewed before publishing.")
            return redirect('testimonials')
    else:
        form = TestimonialForm()
    
    context = {
        'testimonials': testimonials,
        'form': form,
    }
    return render(request, 'lessons/testimonials.html', context)

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! You are now logged in.")
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def user_login(request):
    """Custom login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Redirect to next page if specified
            next_page = request.GET.get('next', 'home')
            return redirect(next_page)
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

@login_required
def user_dashboard(request):
    """User account dashboard"""
    upcoming_bookings = Booking.objects.filter(
        user=request.user,
        date__gte=timezone.now().date()
    ).order_by('date', 'time')
    
    past_bookings = Booking.objects.filter(
        user=request.user,
        date__lt=timezone.now().date()
    ).order_by('-date', '-time')[:5]
    
    context = {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
    }
    return render(request, 'account/dashboard.html', context)

@login_required
def booking_detail(request, booking_id):
    """Detailed view of a specific booking"""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    context = {
        'booking': booking,
    }
    return render(request, 'account/booking_detail.html', context)

@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    if booking.date < timezone.now().date():
        messages.error(request, "Cannot cancel past bookings.")
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        booking.delete()
        messages.success(request, "Your booking has been cancelled.")
        return redirect('user_dashboard')
    
    return render(request, 'account/cancel_booking.html', {'booking': booking})

@login_required
def delete_comment(request, comment_id):
    """Delete a user's FAQ comment"""
    try:
        comment = FAQComment.objects.get(id=comment_id, user=request.user)
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
    except FAQComment.DoesNotExist:
        messages.error(request, "Comment not found or you don't have permission to delete it.")
    
    return redirect('faq')

def process_payment(request, booking_id):
    """Handle payment processing (would integrate with PayPal API)"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # In a real implementation, this would:
    # 1. Create a PayPal order
    # 2. Redirect to PayPal for payment
    # 3. Handle the return/notification
    
    # For demo purposes, we'll just mark as paid
    booking.payment_status = 'completed'
    booking.is_confirmed = True
    booking.save()
    
    messages.success(request, "Payment processed successfully!")
    return redirect('booking_confirmation', booking_id=booking.id)