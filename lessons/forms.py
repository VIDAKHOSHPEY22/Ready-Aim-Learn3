from django import forms
from django.utils import timezone
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import time as dt_time
from .models import (
    FAQComment, Booking, TrainingPackage, Weapon,
    Testimonial, Instructor, RangeLocation, Availability
)
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
            raise ValidationError(_("Comment must be at least 5 characters"))
        return content

class BookingForm(forms.ModelForm):
    package = forms.ModelChoiceField(
        queryset=TrainingPackage.objects.filter(is_active=True),
        widget=forms.RadioSelect(),
        required=True,
        empty_label=None
    )
    
    weapon = forms.ModelChoiceField(
        queryset=Weapon.objects.filter(is_active=True),
        widget=forms.RadioSelect(),
        required=False,
        empty_label=None
    )
    
    instructor = forms.ModelChoiceField(
        queryset=Instructor.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_instructor'
        }),
        required=True
    )
    
    location = forms.ModelChoiceField(
        queryset=RangeLocation.objects.filter(is_active=True),
        widget=forms.RadioSelect(),
        required=False,
        empty_label=None
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_date',
            'min': (timezone.now() + timezone.timedelta(days=1)).date().isoformat()
        }),
        required=True
    )
    
    time = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_time'
        }),
        required=True
    )
    
    duration = forms.IntegerField(
        min_value=30,
        max_value=240,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Duration in minutes (30-240)')
        }),
        required=False
    )
    
    payment_method = forms.ChoiceField(
        choices=Booking.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(),
        required=True,
        initial='paypal'
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Any special requests or notes...')
        }),
        required=False
    )

    class Meta:
        model = Booking
        fields = [
            'package', 'weapon', 'instructor', 'location',
            'date', 'time', 'duration', 'payment_method', 'notes'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['time'].choices = self.get_initial_time_choices()
        
        if 'package' in self.initial:
            package = self.initial['package']
            self.fields['duration'].initial = package.duration
        elif self.fields['package'].queryset.exists():
            self.fields['duration'].initial = self.fields['package'].queryset.first().duration

    def get_initial_time_choices(self):
        return [
            ('', _('Select a time')),
            ('09:00:00', '9:00 AM'),
            ('10:30:00', '10:30 AM'),
            ('12:00:00', '12:00 PM'),
            ('13:30:00', '1:30 PM'),
            ('15:00:00', '3:00 PM'),
            ('16:30:00', '4:30 PM'),
            ('18:00:00', '6:00 PM')
        ]

    def clean(self):
        cleaned_data = super().clean()
        package = cleaned_data.get('package')
        
        if package and not cleaned_data.get('duration'):
            cleaned_data['duration'] = package.duration
            
        return cleaned_data

    def clean_date(self):
        date = self.cleaned_data['date']
        min_date = (timezone.now() + timezone.timedelta(days=1)).date()
        if date < min_date:
            raise ValidationError(
                _("Bookings must be made at least 24 hours in advance. The earliest available date is %(min_date)s"),
                params={'min_date': min_date.strftime('%Y-%m-%d')}
            )
        return date

    def clean_time(self):
        time = self.cleaned_data.get('time')
        if time:
            try:
                # Ensure time is in correct format
                dt_time.fromisoformat(time)
            except ValueError:
                raise ValidationError(_("Invalid time format"))
        return time

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
            'type': 'date',
            'min': (timezone.now() + timezone.timedelta(days=1)).date().isoformat()
        })
    )
    
    def clean_date(self):
        date = self.cleaned_data['date']
        if date < (timezone.now() + timezone.timedelta(days=1)).date():
            raise ValidationError(
                _("Bookings must be made at least 24 hours in advance")
            )
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
                'max': 5
            })
        }

    def clean_rating(self):
        rating = self.cleaned_data['rating']
        if rating < 1 or rating > 5:
            raise ValidationError(_("Rating must be between 1 and 5"))
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
        except ValidationError:
            raise ValidationError(_("Please enter a valid email address"))
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
            'type': 'date',
            'min': (timezone.now() + timezone.timedelta(days=1)).date().isoformat()
        })
    )
    
    instructor_id = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput()
    )

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < (timezone.now() + timezone.timedelta(days=1)).date():
            raise ValidationError(
                _("Bookings must be made at least 24 hours in advance")
            )
        return date