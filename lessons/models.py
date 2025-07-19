from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


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
        default='Mon-Fri',
        verbose_name=_('Available Days')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Instructor')
        verbose_name_plural = _('Instructors')

    def __str__(self):
        return f"Instructor {self.user.get_full_name()}"

    def get_absolute_url(self):
        return reverse('instructor_detail', kwargs={'pk': self.pk})


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
        ('stripe', _('Credit Card')),
        ('cash', _('Cash')),
        ('check', _('Check')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True
    )
    package = models.ForeignKey(
        TrainingPackage,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    weapon = models.ForeignKey(
        Weapon,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    instructor = models.ForeignKey(
        Instructor,
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
    full_name = models.CharField(max_length=100, verbose_name=_('Full Name'))
    email = models.EmailField(verbose_name=_('Email Address'))
    phone = models.CharField(max_length=20, verbose_name=_('Phone Number'))
    notes = models.TextField(
        verbose_name=_('Special Requests'),
        blank=True
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
    transaction_id = models.CharField(
        max_length=100,
        verbose_name=_('Transaction ID'),
        blank=True
    )
    amount_paid = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_('Amount Paid'),
        default=0
    )
    is_confirmed = models.BooleanField(
        default=False,
        verbose_name=_('Confirmed')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        unique_together = ['date', 'time', 'instructor']

    def __str__(self):
        return f"Booking #{self.id} - {self.full_name} on {self.date}"

    def get_absolute_url(self):
        return reverse('booking_detail', kwargs={'pk': self.pk})

    def calculate_total(self):
        """Calculate total price based on package and duration"""
        base_price = self.package.price
        duration_multiplier = self.duration / self.package.duration
        return round(base_price * duration_multiplier, 2)

    def save(self, *args, **kwargs):
        """Override save to calculate amount if not set"""
        if not self.amount_paid:
            self.amount_paid = self.calculate_total()
        super().save(*args, **kwargs)


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
        ordering = ['-created_at']  # Show newest comments first
        verbose_name = _('FAQ Comment')
        verbose_name_plural = _('FAQ Comments')

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

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('location_detail', kwargs={'pk': self.pk})


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

    def __str__(self):
        return f"Testimonial from {self.name} ({self.rating} stars)"

    def get_absolute_url(self):
        return reverse('testimonial_detail', kwargs={'pk': self.pk})