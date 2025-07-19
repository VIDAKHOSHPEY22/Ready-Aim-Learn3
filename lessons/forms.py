from django import forms
from .models import FAQComment, Booking, TrainingPackage, Weapon, Testimonial
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
import re

class FAQCommentForm(forms.ModelForm):
    class Meta:
        model = FAQComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('Write your comment here...'),
                'class': 'form-control'
            })
        }
    
    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content) < 5:
            raise forms.ValidationError(_("Comment must be at least 5 characters"))
        return content


class BookingForm(forms.ModelForm):
    package = forms.ModelChoiceField(
        queryset=TrainingPackage.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'package-select'
        })
    )
    
    weapon = forms.ModelChoiceField(
        queryset=Weapon.objects.filter(is_active=True),
        widget=forms.RadioSelect(),
        empty_label=None
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'booking-date'
        })
    )
    
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
            'id': 'booking-time'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=Booking.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'payment-option'
        })
    )

    class Meta:
        model = Booking
        fields = [
            'package', 'weapon', 'date', 'time', 'duration',
            'full_name', 'email', 'phone', 'notes', 'payment_method'
        ]
        widgets = {
            'duration': forms.Select(attrs={
                'class': 'form-control',
                'id': 'duration-select'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('John Smith')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('your@email.com')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('555-123-4567')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Any special requests or requirements...')
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for authenticated users
        if self.user and self.user.is_authenticated:
            self.fields['full_name'].initial = self.user.get_full_name()
            self.fields['email'].initial = self.user.email
            
        # Customize choices for duration based on selected package
        if 'package' in self.data:
            try:
                package_id = int(self.data.get('package'))
                package = TrainingPackage.objects.get(id=package_id)
                self.fields['duration'].choices = self.get_duration_choices(package)
            except (ValueError, TrainingPackage.DoesNotExist):
                pass
        elif self.instance.pk:
            package = self.instance.package
            self.fields['duration'].choices = self.get_duration_choices(package)

    def get_duration_choices(self, package):
        """Generate duration choices based on package"""
        base_duration = package.duration
        return [
            (base_duration, f"{base_duration} minutes (Standard)"),
            (base_duration * 2, f"{base_duration * 2} minutes (Extended)"),
        ]

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Basic phone number validation
        phone = re.sub(r'[^0-9+]', '', phone)
        if len(phone) < 10:
            raise forms.ValidationError(_("Please enter a valid phone number"))
        return phone

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError(_("Booking date cannot be in the past"))
        return date

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        # Check for existing bookings at this time
        if date and time:
            existing_booking = Booking.objects.filter(
                date=date,
                time=time,
                is_confirmed=True
            ).exists()
            
            if existing_booking:
                raise forms.ValidationError(
                    _("This time slot is already booked. Please choose another time.")
                )
        
        return cleaned_data


class QuickBookingForm(forms.Form):
    package = forms.ModelChoiceField(
        queryset=TrainingPackage.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError(_("Please select a future date"))
        return date


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'content', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your name')
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Share your experience...')
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'step': 1
            })
        }

    def clean_rating(self):
        rating = self.cleaned_data['rating']
        if rating < 1 or rating > 5:
            raise forms.ValidationError(_("Rating must be between 1 and 5"))
        return rating


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your name')
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your@email.com')
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Subject')
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': _('Your message...')
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            validate_email(email)
        except forms.ValidationError:
            raise forms.ValidationError(_("Please enter a valid email address"))
        return email


class PackageFilterForm(forms.Form):
    DURATION_CHOICES = [
        ('', _('Any Duration')),
        ('30', _('30 mins')),
        ('60', _('1 hour')),
        ('90', _('1.5 hours')),
        ('120', _('2 hours')),
    ]

    PRICE_RANGE_CHOICES = [
        ('', _('Any Price')),
        ('0-100', _('Under $100')),
        ('100-200', _('$100-$200')),
        ('200-300', _('$200-$300')),
        ('300', _('Over $300')),
    ]

    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    price_range = forms.ChoiceField(
        choices=PRICE_RANGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('name', _('Name (A-Z)')),
            ('-name', _('Name (Z-A)')),
            ('price', _('Price (Low to High)')),
            ('-price', _('Price (High to Low)')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class AvailabilityCheckForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    package = forms.ModelChoiceField(
        queryset=TrainingPackage.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError(_("Please select a future date"))
        return date