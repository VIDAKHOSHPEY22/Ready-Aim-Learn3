from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import time


class TrainingPackage(models.Model):
    """Model for different training packages offered"""
    name = models.CharField(max_length=100, verbose_name=_('Package Name'))
    description = models.TextField(verbose_name=_('Description'))
    price = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        verbose_name=_('Price'),
        validators=[MinValueValidator(0)]
    )
    duration = models.PositiveIntegerField(
        verbose_name=_('Duration (minutes)'),
        help_text=_('Standard duration in minutes'),
        validators=[MinValueValidator(30), MaxValueValidator(240)]
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this package is currently available')
    )
    image = models.ImageField(
        upload_to='packages/',
        verbose_name=_('Package Image'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']
        verbose_name = _('Training Package')
        verbose_name_plural = _('Training Packages')
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.name} (${self.price})"

    def get_absolute_url(self):
        return reverse('package_detail', kwargs={'pk': self.pk})


class Weapon(models.Model):
    """Model for firearms available for training"""
    FIREARM_TYPES = [
        ('pistol', _('Pistol')),
        ('revolver', _('Revolver')),
        ('rifle', _('Rifle')),
        ('shotgun', _('Shotgun')),
    ]

    name = models.CharField(max_length=100, verbose_name=_('Weapon Name'))
    caliber = models.CharField(max_length=50, verbose_name=_('Caliber'))
    type = models.CharField(
        max_length=20,
        choices=FIREARM_TYPES,
        default='pistol',
        verbose_name=_('Firearm Type')
    )
    image = models.ImageField(
        upload_to='weapons/',
        verbose_name=_('Weapon Image')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this weapon is currently available')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['type', 'name']
        verbose_name = _('Weapon')
        verbose_name_plural = _('Weapons')
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.caliber})"


class Instructor(models.Model):
    """Model for training instructors"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='instructor_profile'
    )
    bio = models.TextField(verbose_name=_('Biography'))
    certifications = models.TextField(
        verbose_name=_('Certifications'),
        help_text=_('List certifications separated by commas')
    )
    years_experience = models.PositiveIntegerField(
        verbose_name=_('Years of Experience'),
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    profile_picture = models.ImageField(
        upload_to='instructors/',
        verbose_name=_('Profile Picture'),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this instructor is currently available')
    )
    available_days = models.CharField(
        max_length=100,
        verbose_name=_('Available Days'),
        help_text=_('Comma-separated list of available weekdays (0-6)'),
        default='0,1,2,3,4'  # Monday to Friday by default
    )
    start_time = models.TimeField(
        default=time(9, 0),  # 9:00 AM
        verbose_name=_('Start Time')
    )
    end_time = models.TimeField(
        default=time(17, 0),  # 5:00 PM
        verbose_name=_('End Time')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Instructor')
        verbose_name_plural = _('Instructors')
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Instructor {self.user.get_full_name() or self.user.username}"

    def get_absolute_url(self):
        return reverse('instructor_detail', kwargs={'pk': self.pk})

    def get_available_days_list(self):
        """Return available days as a list of integers"""
        return [int(day.strip()) for day in self.available_days.split(',') if day.strip()]


class RangeLocation(models.Model):
    """Model for shooting range locations"""
    name = models.CharField(max_length=100, verbose_name=_('Location Name'))
    address = models.TextField(verbose_name=_('Address'))
    phone = models.CharField(max_length=20, verbose_name=_('Phone Number'))
    email = models.EmailField(verbose_name=_('Email Address'))
    hours = models.TextField(verbose_name=_('Business Hours'))
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this location is currently available')
    )
    image = models.ImageField(
        upload_to='locations/',
        verbose_name=_('Location Image'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Range Location')
        verbose_name_plural = _('Range Locations')
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('location_detail', kwargs={'pk': self.pk})


class Availability(models.Model):
    """Special availability exceptions (holidays, vacations, etc.)"""
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    date = models.DateField(verbose_name=_('Date'))
    is_available = models.BooleanField(
        default=False,
        verbose_name=_('Is Available')
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Reason')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['instructor', 'date']
        verbose_name = _('Availability')
        verbose_name_plural = _('Availabilities')
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['is_available']),
        ]
        ordering = ['date']

    def __str__(self):
        return f"{self.instructor} - {'Available' if self.is_available else 'Unavailable'} on {self.date}"


class Booking(models.Model):
    """Model for training session bookings"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('paypal', _('PayPal')),
        ('cash', _('Cash')),
        ('credit_card', _('Credit Card')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    package = models.ForeignKey(
        TrainingPackage,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    weapon = models.ForeignKey(
        Weapon,
        on_delete=models.PROTECT,
        related_name='bookings',
        null=True,
        blank=True
    )
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    location = models.ForeignKey(
        RangeLocation,
        on_delete=models.PROTECT,
        related_name='bookings',
        null=True,
        blank=True
    )
    date = models.DateField(verbose_name=_('Booking Date'))
    time = models.TimeField(verbose_name=_('Booking Time'))
    duration = models.PositiveIntegerField(
        verbose_name=_('Duration (minutes)'),
        validators=[MinValueValidator(30), MaxValueValidator(240)]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='paypal',
        verbose_name=_('Payment Method')
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Payment Status')
    )
    payment_completed = models.BooleanField(
        default=False,
        verbose_name=_('Payment Completed')
    )
    transaction_id = models.CharField(
        max_length=100,
        verbose_name=_('Transaction ID'),
        blank=True
    )
    paypal_txn_id = models.CharField(
        max_length=100,
        verbose_name=_('PayPal Transaction ID'),
        blank=True
    )
    amount_paid = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_('Amount Paid'),
        default=0
    )
    notes = models.TextField(
        verbose_name=_('Special Requests'),
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        unique_together = ['date', 'time', 'instructor']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['paypal_txn_id']),
        ]

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} on {self.date}"

    def get_absolute_url(self):
        return reverse('booking_detail', kwargs={'pk': self.pk})

    def clean(self):
        """Validate booking constraints"""
        # Ensure bookings are made at least 24 hours in advance
        booking_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.time))
        if booking_datetime < (timezone.now() + timezone.timedelta(hours=24)):
            raise ValidationError(
                _("Bookings must be made at least 24 hours in advance.")
            )
        
        # Validate instructor availability
        if not self.is_instructor_available():
            raise ValidationError(
                _("The selected instructor is not available at this time.")
            )

    def save(self, *args, **kwargs):
        """Override save to calculate amount if not set and validate"""
        if not self.amount_paid:
            self.amount_paid = self.calculate_total()
        self.full_clean()
        super().save(*args, **kwargs)

    def calculate_total(self):
        """Calculate total price based on package and duration"""
        return self.package.price

    def is_instructor_available(self):
        """Check if instructor is available for this booking"""
        # Check regular availability
        weekday = self.date.weekday()
        if weekday not in self.instructor.get_available_days_list():
            return False
        
        # Check time slot
        if (self.time < self.instructor.start_time or 
            self.time > self.instructor.end_time):
            return False
        
        # Check special availability exceptions
        try:
            availability = Availability.objects.get(
                instructor=self.instructor,
                date=self.date
            )
            return availability.is_available
        except Availability.DoesNotExist:
            return True

    @property
    def datetime(self):
        """Combine date and time into a datetime object"""
        return timezone.make_aware(timezone.datetime.combine(self.date, self.time))

    def is_upcoming(self):
        """Check if the booking is in the future"""
        return self.datetime > timezone.now()

    def mark_as_paid(self, txn_id=None, payment_method='paypal'):
        """Mark booking as paid"""
        self.payment_status = 'completed'
        self.payment_completed = True
        self.status = 'confirmed'
        self.payment_method = payment_method
        if txn_id:
            if payment_method == 'paypal':
                self.paypal_txn_id = txn_id
            else:
                self.transaction_id = txn_id
        self.save()


class FAQComment(models.Model):
    """Model for FAQ comments and replies"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='faq_comments'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    content = models.TextField(
        max_length=1000,
        verbose_name=_('Comment')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Posted at')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last updated')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Designates whether this comment should be shown publicly')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('FAQ Comment')
        verbose_name_plural = _('FAQ Comments')
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        prefix = f"Reply to #{self.parent.id}" if self.parent else "Comment"
        return f"{prefix} by {self.user.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def is_reply(self):
        """Check if this comment is a reply"""
        return self.parent is not None
    
    def get_absolute_url(self):
        """Get URL to the comment's position on FAQ page"""
        return reverse('faq') + f'#comment-{self.id}'
    
    def time_since_creation(self):
        """Human-readable time since creation"""
        return timezone.now() - self.created_at


class Testimonial(models.Model):
    """Model for customer testimonials"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='testimonials'
    )
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    content = models.TextField(verbose_name=_('Testimonial'))
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('Rating')
    )
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='testimonials',
        verbose_name=_('Instructor')
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_('Approved'),
        help_text=_('Whether this testimonial is approved to be shown')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Testimonial')
        verbose_name_plural = _('Testimonials')
        indexes = [
            models.Index(fields=['is_approved']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"Testimonial from {self.name} ({self.rating} stars)"

    def get_absolute_url(self):
        return reverse('testimonial_detail', kwargs={'pk': self.pk})


class PayPalTransaction(models.Model):
    """Model to track PayPal transactions"""
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='paypal_transactions'
    )
    txn_id = models.CharField(
        max_length=100,
        verbose_name=_('Transaction ID')
    )
    payment_status = models.CharField(
        max_length=20,
        verbose_name=_('Payment Status')
    )
    payment_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_('Payment Amount')
    )
    payer_email = models.EmailField(
        verbose_name=_('Payer Email')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('PayPal Transaction')
        verbose_name_plural = _('PayPal Transactions')
        indexes = [
            models.Index(fields=['txn_id']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"PayPal Transaction {self.txn_id} for Booking #{self.booking_id}"


def create_initial_data():
    """Function to create initial data"""
    # Create sample training package
    package, created = TrainingPackage.objects.get_or_create(
        name="Basic Pistol Training",
        defaults={
            'description': "Introduction to pistol handling and safety",
            'price': 150.00,
            'duration': 60,
            'is_active': True
        }
    )
    
    # Create sample weapon
    weapon, created = Weapon.objects.get_or_create(
        name="Glock 19",
        defaults={
            'caliber': "9mm",
            'type': "pistol",
            'is_active': True,
            'description': "Popular 9mm semi-automatic pistol"
        }
    )
    
    # Create sample range location
    location, created = RangeLocation.objects.get_or_create(
        name="Downtown Shooting Range",
        defaults={
            'address': "123 Main St, Anytown, USA",
            'phone': "(555) 123-4567",
            'email': "info@downtownrange.com",
            'hours': "Mon-Fri: 9AM-9PM, Sat-Sun: 10AM-6PM",
            'is_active': True
        }
    )
    
    # Create sample instructor
    instructor_user, created = User.objects.get_or_create(
        username='luisdavid',
        defaults={
            'first_name': 'Luis David',
            'last_name': 'Valencia Hernandez',
            'email': 'luisdavid313@gmail.com'
        }
    )
    if created:
        instructor_user.set_password('temp_password123')
        instructor_user.save()

    instructor, created = Instructor.objects.get_or_create(
        user=instructor_user,
        defaults={
            'bio': 'NRA Certified Instructor with 10+ years of experience',
            'certifications': 'NRA Certified Pistol Instructor, NRA Range Safety Officer',
            'years_experience': 12,
            'is_active': True,
            'available_days': '0,1,2,3,4',  # Monday to Friday
            'start_time': time(9, 0),
            'end_time': time(17, 0)
        }
    )