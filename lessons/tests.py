from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    TrainingPackage, Weapon, Instructor, 
    Booking, FAQComment, Testimonial, RangeLocation
)
from .forms import (
    BookingForm, QuickBookingForm, FAQCommentForm,
    TestimonialForm, ContactForm, PackageFilterForm
)
import datetime

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.package = TrainingPackage.objects.create(
            name='Basic Marksmanship',
            description='Intro to firearm safety',
            price=150.00,
            duration=60,
            is_active=True
        )
        self.weapon = Weapon.objects.create(
            name='Glock 19',
            caliber='9mm',
            type='pistol',
            is_active=True
        )
        self.instructor = Instructor.objects.create(
            user=self.user,
            bio='Certified instructor',
            certifications='NRA, DOJ',
            years_experience=5,
            is_active=True
        )

    def test_training_package_creation(self):
        self.assertEqual(self.package.name, 'Basic Marksmanship')
        self.assertEqual(self.package.price, 150.00)
        self.assertTrue(self.package.is_active)

    def test_weapon_creation(self):
        self.assertEqual(self.weapon.name, 'Glock 19')
        self.assertEqual(self.weapon.type, 'pistol')
        self.assertTrue(self.weapon.is_active)

    def test_booking_creation(self):
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            weapon=self.weapon,
            instructor=self.instructor,
            date=timezone.now().date() + datetime.timedelta(days=7),
            time=datetime.time(10, 0),
            duration=60,
            full_name='Test User',
            email='test@example.com',
            phone='5551234567',
            payment_method='paypal',
            payment_status='pending'
        )
        self.assertEqual(booking.package.name, 'Basic Marksmanship')
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.calculate_total(), 150.00)

    def test_faq_comment_creation(self):
        comment = FAQComment.objects.create(
            user=self.user,
            content='Great FAQ section!',
            is_active=True
        )
        self.assertEqual(comment.content, 'Great FAQ section!')
        self.assertTrue(comment.is_active)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.package = TrainingPackage.objects.create(
            name='Basic Package',
            description='Test package',
            price=100.00,
            duration=60,
            is_active=True
        )
        self.weapon = Weapon.objects.create(
            name='Test Weapon',
            caliber='9mm',
            is_active=True
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lessons/home.html')

    def test_packages_view(self):
        response = self.client.get(reverse('packages'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Basic Package')

    def test_booking_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('booking'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Book Your Training')

    def test_booking_view_unauthenticated(self):
        response = self.client.get(reverse('booking'))
        self.assertEqual(response.status_code, 200)  # Should still be accessible

    def test_booking_submission(self):
        self.client.login(username='testuser', password='testpass123')
        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        response = self.client.post(reverse('booking'), {
            'package': self.package.id,
            'weapon': self.weapon.id,
            'date': tomorrow,
            'time': '10:00',
            'duration': 60,
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '5551234567',
            'payment_method': 'paypal'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertEqual(Booking.objects.count(), 1)

    def test_faq_view(self):
        response = self.client.get(reverse('faq'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Frequently Asked Questions')


class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.package = TrainingPackage.objects.create(
            name='Test Package',
            description='Test desc',
            price=100.00,
            duration=60,
            is_active=True
        )
        self.weapon = Weapon.objects.create(
            name='Test Weapon',
            caliber='9mm',
            is_active=True
        )

    def test_booking_form_valid(self):
        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        form_data = {
            'package': self.package.id,
            'weapon': self.weapon.id,
            'date': tomorrow,
            'time': '10:00',
            'duration': 60,
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '5551234567',
            'payment_method': 'paypal'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_invalid_date(self):
        yesterday = timezone.now().date() - datetime.timedelta(days=1)
        form_data = {
            'package': self.package.id,
            'weapon': self.weapon.id,
            'date': yesterday,
            'time': '10:00',
            'duration': 60,
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '5551234567',
            'payment_method': 'paypal'
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_faq_comment_form_valid(self):
        form_data = {'content': 'This is a test comment'}
        form = FAQCommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_faq_comment_form_invalid(self):
        form_data = {'content': 'x'}  # Too short
        form = FAQCommentForm(data=form_data)
        self.assertFalse(form.is_valid())


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_successful_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect

    def test_failed_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stays on page
        self.assertContains(response, 'Please enter a correct username and password')

    def test_signup_view(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_successful_signup(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)


class BookingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.package = TrainingPackage.objects.create(
            name='Test Package',
            description='Test desc',
            price=100.00,
            duration=60,
            is_active=True
        )
        self.weapon = Weapon.objects.create(
            name='Test Weapon',
            caliber='9mm',
            is_active=True
        )
        self.instructor = Instructor.objects.create(
            user=self.user,
            bio='Test bio',
            certifications='Test cert',
            years_experience=5,
            is_active=True
        )

    def test_booking_total_calculation(self):
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            weapon=self.weapon,
            instructor=self.instructor,
            date=timezone.now().date() + datetime.timedelta(days=7),
            time=datetime.time(10, 0),
            duration=60,
            full_name='Test User',
            email='test@example.com',
            phone='5551234567',
            payment_method='paypal',
            payment_status='pending'
        )
        self.assertEqual(booking.calculate_total(), 100.00)

    def test_booking_extended_duration(self):
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            weapon=self.weapon,
            instructor=self.instructor,
            date=timezone.now().date() + datetime.timedelta(days=7),
            time=datetime.time(10, 0),
            duration=120,
            full_name='Test User',
            email='test@example.com',
            phone='5551234567',
            payment_method='paypal',
            payment_status='pending'
        )
        self.assertEqual(booking.calculate_total(), 200.00)

    def test_booking_str_representation(self):
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            weapon=self.weapon,
            instructor=self.instructor,
            date=timezone.now().date() + datetime.timedelta(days=7),
            time=datetime.time(10, 0),
            duration=60,
            full_name='Test User',
            email='test@example.com',
            phone='5551234567',
            payment_method='paypal',
            payment_status='pending'
        )
        self.assertIn('Booking #', str(booking))
        self.assertIn('Test User', str(booking))