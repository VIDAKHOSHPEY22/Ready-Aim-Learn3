from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Q
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.models import PayPalIPN
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
import logging
from datetime import time as dt_time, datetime, date
from .models import (
    FAQComment, Booking, TrainingPackage, Instructor,
    Testimonial, RangeLocation, Weapon, Availability
)
from .forms import (
    FAQCommentForm, BookingForm, QuickBookingForm,
    TestimonialForm, ContactForm, PackageFilterForm,
    AvailabilityCheckForm
)

# Initialize logger
logger = logging.getLogger(__name__)

# Constants
TIME_SLOTS = [
    ('09:00:00', '9:00 AM'),
    ('10:30:00', '10:30 AM'),
    ('12:00:00', '12:00 PM'),
    ('13:30:00', '1:30 PM'),
    ('15:00:00', '3:00 PM'),
    ('16:30:00', '4:30 PM'),
    ('18:00:00', '6:00 PM'),
]

def parse_date(date_input):
    """Convert string or date to date object"""
    if isinstance(date_input, date):
        return date_input
    try:
        return datetime.strptime(date_input, '%Y-%m-%d').date()
    except (TypeError, ValueError) as e:
        logger.error(f"Date parsing error: {e}")
        raise ValueError("Invalid date format")

def parse_time(time_input):
    """Convert string or time to time object"""
    if isinstance(time_input, dt_time):
        return time_input
    try:
        return dt_time.fromisoformat(time_input)
    except (TypeError, ValueError) as e:
        logger.error(f"Time parsing error: {e}")
        raise ValueError("Invalid time format")

def get_active_resources():
    """Helper function to get all active resources"""
    return {
        'packages': TrainingPackage.objects.filter(is_active=True),
        'weapons': Weapon.objects.filter(is_active=True),
        'instructors': Instructor.objects.filter(is_active=True),
        'locations': RangeLocation.objects.filter(is_active=True),
    }

def home(request):
    """Homepage view with featured packages and testimonials"""
    context = {
        'featured_packages': TrainingPackage.objects.filter(is_active=True).order_by('?')[:3],
        'testimonials': Testimonial.objects.filter(is_approved=True).order_by('-created_at')[:4],
    }
    return render(request, 'lessons/home.html', context)

def packages(request):
    """View for listing all training packages with filtering"""
    packages = TrainingPackage.objects.filter(is_active=True)
    filter_form = PackageFilterForm(request.GET)
    
    if filter_form.is_valid():
        packages = apply_package_filters(packages, filter_form.cleaned_data)
    
    paginator = Paginator(packages, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'lessons/packages.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
    })

def apply_package_filters(packages, cleaned_data):
    """Apply filters to packages queryset"""
    duration = cleaned_data.get('duration')
    price_range = cleaned_data.get('price_range')
    sort_by = cleaned_data.get('sort_by')
    
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
    
    return packages

def package_detail(request, pk):
    """Detailed view for a single training package"""
    package = get_object_or_404(TrainingPackage, pk=pk, is_active=True)
    return render(request, 'lessons/package_detail.html', {
        'package': package,
        'related_packages': TrainingPackage.objects.filter(
            is_active=True
        ).exclude(pk=pk).order_by('?')[:3],
    })

def quick_booking(request):
    """Simplified booking flow that redirects to main booking with package preselected"""
    if request.method == 'POST':
        form = QuickBookingForm(request.POST)
        if form.is_valid():
            request.session['quick_booking_date'] = form.cleaned_data['date'].isoformat()
            return redirect('booking_with_package', package_id=form.cleaned_data['package'].id)
    
    return render(request, 'lessons/quick_booking.html', {
        'form': QuickBookingForm()
    })

@login_required
def booking(request, package_id=None):
    """Main booking view that handles both direct access and package-specific booking"""
    resources = get_active_resources()
    min_date = (timezone.now() + timezone.timedelta(days=1)).date()
    quick_booking_date = request.session.pop('quick_booking_date', None)
    
    if request.method == 'POST':
        return handle_booking_post(request, resources, min_date)
    
    return render_booking_form(request, package_id, quick_booking_date, resources, min_date)

def handle_booking_post(request, resources, min_date):
    """Process booking form submission"""
    form = BookingForm(request.POST, user=request.user)
    if not form.is_valid():
        return handle_invalid_form(form, resources, min_date)
    
    try:
        booking = form.save(commit=False)
        booking.user = request.user
        booking.duration = booking.duration or booking.package.duration
        
        if not validate_booking_availability(booking):
            messages.error(request, "The selected time slot is not available.")
            return render_booking_form_with_context(request, form, resources, min_date)
        
        return process_booking_confirmation(request, booking)
    
    except Exception as e:
        logger.error(f"Booking error: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred. Please try again.")
        return render_booking_form_with_context(request, form, resources, min_date)

def validate_booking_availability(booking):
    """Validate instructor availability and time slot"""
    try:
        if not is_instructor_available(booking.instructor, booking.date, booking.time):
            return False
        
        return not Booking.objects.filter(
            date=booking.date,
            time=booking.time,
            instructor=booking.instructor,
            status__in=['pending', 'confirmed']
        ).exists()
    except Exception as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        return False

def process_booking_confirmation(request, booking):
    """Process booking confirmation based on payment method"""
    booking.status = 'pending'
    
    if booking.payment_method == 'paypal':
        return handle_paypal_payment(request, booking)
    
    booking.save()
    send_booking_confirmation(booking, request.user)
    messages.success(request, "Your booking has been confirmed!")
    return redirect('booking_confirmation', booking_id=booking.id)

def handle_paypal_payment(request, booking):
    """Prepare session data for PayPal payment"""
    request.session['pending_booking'] = {
        'package_id': booking.package.id,
        'weapon_id': booking.weapon.id if booking.weapon else None,
        'instructor_id': booking.instructor.id,
        'location_id': booking.location.id if booking.location else None,
        'date': booking.date.isoformat(),
        'time': booking.time.isoformat(),
        'duration': booking.duration,
        'payment_method': 'paypal',
        'notes': booking.notes,
    }
    return redirect('process_payment')

def render_booking_form(request, package_id, quick_booking_date, resources, min_date):
    """Render booking form with initial data"""
    initial = {}
    if package_id:
        package = get_object_or_404(TrainingPackage, pk=package_id)
        initial.update({
            'package': package,
            'duration': package.duration,
        })
        if quick_booking_date:
            try:
                initial['date'] = parse_date(quick_booking_date)
            except ValueError:
                logger.warning(f"Invalid quick booking date format: {quick_booking_date}")
    
    form = BookingForm(initial=initial, user=request.user)
    return render_booking_form_with_context(request, form, resources, min_date)

def render_booking_form_with_context(request, form, resources, min_date):
    """Render booking template with context"""
    context = {
        'form': form,
        'available_times': TIME_SLOTS,
        'min_date': min_date,
    }
    context.update(resources)
    return render(request, 'booking/booking.html', context)

def handle_invalid_form(form, resources, min_date):
    """Handle invalid form submission"""
    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f"{field}: {error}")
    return render_booking_form_with_context(None, form, resources, min_date)

def is_instructor_available(instructor, date, time):
    """Check if instructor is available for given date and time"""
    try:
        # Ensure date is a date object
        date_obj = parse_date(date)
        
        # Check available days
        weekday = date_obj.weekday()
        available_days = [int(d) for d in instructor.available_days.split(',') if d.strip()]
        if weekday not in available_days:
            return False
        
        # Ensure time is a time object
        time_obj = parse_time(time)
        
        # Check working hours
        if (time_obj < instructor.start_time or 
            time_obj > instructor.end_time):
            return False
        
        # Check special availability exceptions
        try:
            availability = Availability.objects.get(
                instructor=instructor,
                date=date_obj
            )
            return availability.is_available
        except Availability.DoesNotExist:
            return True
            
    except Exception as e:
        logger.error(f"Instructor availability check failed: {str(e)}", exc_info=True)
        return False

def send_booking_confirmation(booking, user):
    """Send booking confirmation email"""
    try:
        # Get admin email from settings or use default
        admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
        
        # User email
        send_mail(
            subject=f"Booking Confirmation: {booking.package.name}",
            message=generate_user_email_content(booking),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        # Admin notification - only if ADMIN_EMAIL is different from DEFAULT_FROM_EMAIL
        if admin_email != settings.DEFAULT_FROM_EMAIL:
            send_mail(
                subject=f"New Booking: {user.get_full_name()}",
                message=generate_admin_email_content(booking, user),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False,
            )
            
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {str(e)}", exc_info=True)

def generate_user_email_content(booking):
    """Generate content for user confirmation email"""
    message = f"""Thank you for booking with us!

Booking Details:
Package: {booking.package.name}
Instructor: {booking.instructor.user.get_full_name()}
Date: {booking.date.strftime('%A, %B %d, %Y')}
Time: {booking.time.strftime('%I:%M %p')}
Duration: {booking.duration} minutes
Location: {booking.location.name if booking.location else 'To be determined'}
Total: ${booking.package.price}

Payment Method: {booking.get_payment_method_display()}
Status: {booking.get_status_display()}
"""
    if booking.payment_method == 'cash':
        message += "\nPlease bring cash to your lesson.\n"
    
    message += "\nIf you need to cancel or reschedule, please contact us at least 24 hours in advance."
    return message

def generate_admin_email_content(booking, user):
    """Generate content for admin notification email"""
    return f"""New Booking:

User: {user.get_full_name()} ({user.email})
Package: {booking.package.name}
Instructor: {booking.instructor.user.get_full_name()}
Date: {booking.date} at {booking.time.strftime('%I:%M %p')}
Duration: {booking.duration} minutes
Payment Method: {booking.get_payment_method_display()}
Status: {booking.get_status_display()}
"""

@login_required
def process_payment(request):
    """Handle PayPal payment processing"""
    pending_booking = request.session.get('pending_booking')
    if not pending_booking:
        messages.error(request, "No booking found to process payment.")
        return redirect('packages')
    
    try:
        # Convert session data to proper types
        booking_data = {
            'date': parse_date(pending_booking['date']),
            'time': parse_time(pending_booking['time']),
            'package_id': pending_booking['package_id'],
            'instructor_id': pending_booking['instructor_id'],
            'location_id': pending_booking.get('location_id'),
            'weapon_id': pending_booking.get('weapon_id'),
            'duration': pending_booking['duration'],
            'payment_method': 'paypal',
            'notes': pending_booking['notes'],
        }

        package = get_object_or_404(TrainingPackage, id=booking_data['package_id'])
        
        # Create PayPal payment
        paypal_dict = {
            "business": settings.PAYPAL_RECEIVER_EMAIL,
            "amount": str(package.price),
            "item_name": f"Training: {package.name}",
            "invoice": f"booking-{timezone.now().timestamp()}",
            "currency_code": "USD",
            "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
            "return_url": request.build_absolute_uri(reverse('booking_confirmation', args=[0])),  # Temp booking ID
            "cancel_return": request.build_absolute_uri(reverse('booking')),
        }

        # Create form instance
        paypal_form = PayPalPaymentsForm(initial=paypal_dict)
        
        context = {
            'package': package,
            'paypal_form': paypal_form,
            'pending_booking': pending_booking,
        }
        
        return render(request, 'booking/paypal_payment.html', context)
        
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}", exc_info=True)
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('booking')

@login_required
def booking_confirmation(request, booking_id):
    """Handle PayPal return and show confirmation"""
    if booking_id == "0":  # PayPal return before booking created
        # Get transaction details from IPN
        try:
            latest_ipn = PayPalIPN.objects.latest('id')
            if latest_ipn.payment_status == "Completed":
                # Create the actual booking
                pending_booking = request.session.get('pending_booking')
                if pending_booking:
                    booking = create_actual_booking(request.user, pending_booking)
                    del request.session['pending_booking']
                    return render(request, 'booking/confirmation.html', {'booking': booking})
        except PayPalIPN.DoesNotExist:
            pass
        
        messages.warning(request, "We're processing your payment. You'll receive a confirmation email shortly.")
        return redirect('user_dashboard')
    
    # Normal confirmation flow
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'booking/confirmation.html', {'booking': booking})

def create_actual_booking(user, booking_data):
    """Create booking after successful PayPal payment"""
    package = get_object_or_404(TrainingPackage, id=booking_data['package_id'])
    instructor = get_object_or_404(Instructor, id=booking_data['instructor_id'])
    location = get_object_or_404(RangeLocation, id=booking_data['location_id']) if booking_data.get('location_id') else None
    weapon = get_object_or_404(Weapon, id=booking_data['weapon_id']) if booking_data.get('weapon_id') else None
    
    booking = Booking.objects.create(
        user=user,
        package=package,
        weapon=weapon,
        instructor=instructor,
        location=location,
        date=parse_date(booking_data['date']),
        time=parse_time(booking_data['time']),
        duration=booking_data['duration'],
        payment_method='paypal',
        notes=booking_data['notes'],
        status='confirmed',
        payment_status='completed',
    )
    
    send_booking_confirmation(booking, user)
    return booking

def check_availability(request):
    """AJAX endpoint for checking available time slots"""
    if request.method == 'POST':
        form = AvailabilityCheckForm(request.POST)
        if form.is_valid():
            try:
                date_obj = parse_date(form.cleaned_data['date'])
                instructor_id = request.POST.get('instructor_id')
                
                if not instructor_id:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Instructor not specified'
                    }, status=400)
                
                try:
                    instructor = Instructor.objects.get(id=instructor_id)
                except Instructor.DoesNotExist:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Invalid instructor'
                    }, status=400)
                
                # Get existing bookings
                existing_bookings = Booking.objects.filter(
                    date=date_obj,
                    instructor=instructor,
                    status__in=['pending', 'confirmed']
                ).values_list('time', flat=True)
                
                # Get instructor's working hours
                available_slots = []
                for slot_value, slot_display in TIME_SLOTS:
                    if slot_value not in existing_bookings:
                        try:
                            slot_time = parse_time(slot_value)
                            if (slot_time >= instructor.start_time and 
                                slot_time <= instructor.end_time):
                                available_slots.append({
                                    'value': slot_value,
                                    'display': slot_display
                                })
                        except ValueError:
                            continue
                
                return JsonResponse({
                    'success': True,
                    'available_slots': available_slots,
                })
            except ValueError as e:
                return JsonResponse({
                    'success': False, 
                    'error': str(e)
                }, status=400)
        
        return JsonResponse({
            'success': False, 
            'errors': form.errors
        }, status=400)
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=405)

# ... (rest of your views remain unchanged)

def about(request):
    """About page with instructor information"""
    instructors = Instructor.objects.filter(is_active=True).annotate(
        num_reviews=Count('testimonials')
    ).order_by('-years_experience')
    return render(request, 'lessons/about.html', {'instructors': instructors})

def instructor_detail(request, pk):
    """Detailed view for an instructor"""
    instructor = get_object_or_404(Instructor, pk=pk, is_active=True)
    testimonials = Testimonial.objects.filter(
        instructor=instructor,
        is_approved=True
    ).order_by('-created_at')[:5]
    return render(request, 'lessons/instructor_detail.html', {
        'instructor': instructor,
        'testimonials': testimonials,
    })

def faq(request):
    """FAQ page with static questions and user comments"""
    faqs = [
        {"q": "Do I need to bring my own firearm or ammo?", 
         "a": "No. All necessary firearms, ammunition, eye and ear protection, and targets are provided."},
        {"q": "Is it safe for beginners with no experience?", 
         "a": "Absolutely. Our lessons are tailored for beginners with step-by-step safety instruction."},
    ]

    comments = FAQComment.objects.filter(parent__isnull=True, is_active=True).order_by('-created_at')
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to post a comment.")
            return redirect('login')
        
        form = FAQCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.is_active = True
            
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    comment.parent = FAQComment.objects.get(id=parent_id)
                except FAQComment.DoesNotExist:
                    messages.error(request, "Invalid comment reference.")
                    return redirect('faq')
            
            comment.save()
            messages.success(request, "Your comment has been posted successfully!")
            return redirect('faq')
    else:
        form = FAQCommentForm()

    return render(request, 'lessons/faq.html', {
        'faqs': faqs,
        'comments': comments,
        'form': form,
    })

def contact(request):
    """Contact page with form submission"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send email
            send_mail(
                subject=f"New Contact Form Submission from {form.cleaned_data['name']}",
                message=f"Name: {form.cleaned_data['name']}\nEmail: {form.cleaned_data['email']}\n\nMessage:\n{form.cleaned_data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            messages.success(request, "Thank you for your message! We'll respond within 24 hours.")
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'lessons/contact.html', {
        'form': form,
        'locations': RangeLocation.objects.filter(is_active=True),
    })

def legal(request):
    """Legal information page"""
    return render(request, 'lessons/legal.html')

def privacy(request):
    """Privacy policy page"""
    return render(request, 'lessons/privacy.html')

def testimonials(request):
    """View all testimonials"""
    if request.method == 'POST' and request.user.is_authenticated:
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.user = request.user
            testimonial.is_approved = False  # Requires admin approval
            testimonial.save()
            messages.success(request, "Thank you for your testimonial! It will be reviewed before publishing.")
            return redirect('testimonials')
    else:
        form = TestimonialForm()
    
    return render(request, 'lessons/testimonials.html', {
        'testimonials': Testimonial.objects.filter(is_approved=True).order_by('-created_at'),
        'form': form,
    })

def signup(request):
    """Handle user registration with proper authentication"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Authenticate and login the user
            authenticated_user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            
            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, "Account created successfully! You are now logged in.")
                return redirect('home')
            else:
                messages.error(request, "Authentication failed. Please try logging in.")
                return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def user_login(request):
    """Handle user authentication with next URL validation"""
    if request.user.is_authenticated:
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Safe redirect handling
            next_url = request.POST.get('next', '')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('user_dashboard')
    else:
        form = AuthenticationForm()
        next_url = request.GET.get('next', '')

    return render(request, 'registration/login.html', {
        'form': form,
        'next': next_url
    })

def user_logout(request):
    """Handle user logout with confirmation"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect('home')

@login_required
def user_dashboard(request):
    """User dashboard with booking management and pagination"""
    now = timezone.now().date()
    
    # Upcoming bookings
    upcoming_bookings = Booking.objects.filter(
        user=request.user,
        date__gte=now
    ).order_by('date', 'time')
    
    # Past bookings (paginated)
    past_bookings = Booking.objects.filter(
        user=request.user,
        date__lt=now
    ).order_by('-date', '-time')
    
    paginator = Paginator(past_bookings, 5)
    page_number = request.GET.get('page')
    past_bookings_page = paginator.get_page(page_number)
    
    return render(request, 'account/dashboard.html', {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings_page,
        'now': now
    })

@login_required
def booking_detail(request, booking_id):
    """Detailed booking view with permission check"""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    # Check if cancellation is allowed (at least 24 hours before)
    cutoff_time = timezone.make_aware(datetime.combine(booking.date, dt_time(0, 0)))
    can_cancel = (cutoff_time - timezone.now()) > timezone.timedelta(hours=24)
    
    return render(request, 'account/booking_detail.html', {
        'booking': booking,
        'can_cancel': can_cancel,
        'cutoff_time': cutoff_time
    })

@login_required
def cancel_booking(request, booking_id):
    """Handle booking cancellation with validation"""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    # Check cancellation policy
    cutoff_time = timezone.make_aware(datetime.combine(booking.date, dt_time(0, 0)))
    if timezone.now() > cutoff_time - timezone.timedelta(hours=24):
        messages.error(request, "Cancellations must be made at least 24 hours in advance.")
        return redirect('booking_detail', booking_id=booking.id)
    
    if request.method == 'POST':
        # Send cancellation email
        send_mail(
            'Booking Cancellation Confirmation',
            f'Your booking on {booking.date} at {booking.time} has been cancelled.',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=True,
        )
        
        booking.delete()
        messages.success(request, "Your booking has been cancelled successfully.")
        return redirect('user_dashboard')
    
    return render(request, 'account/cancel_booking.html', {'booking': booking})

@login_required
def delete_comment(request, comment_id):
    """Handle FAQ comment deletion with confirmation"""
    comment = get_object_or_404(FAQComment, id=comment_id, user=request.user)
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Your comment has been deleted.")
        return redirect('faq')
    
    return render(request, 'account/confirm_delete.html', {
        'object': comment,
        'object_type': 'comment',
        'cancel_url': reverse('faq')
    })

def handler404(request, exception):
    """Custom 404 error handler with logging"""
    logger.warning(f'404 Error: {exception}')
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error handler with logging"""
    logger.error('500 Server Error', exc_info=True)
    return render(request, 'errors/500.html', status=500)