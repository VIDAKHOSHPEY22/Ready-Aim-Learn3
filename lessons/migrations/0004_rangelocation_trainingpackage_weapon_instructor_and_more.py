# Generated by Django 5.2 on 2025-07-19 13:33

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0003_faqcomment_is_active'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RangeLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Location Name')),
                ('address', models.TextField(verbose_name='Address')),
                ('phone', models.CharField(max_length=20, verbose_name='Phone Number')),
                ('email', models.EmailField(max_length=254, verbose_name='Email Address')),
                ('hours', models.TextField(verbose_name='Business Hours')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this location is currently available', verbose_name='Active')),
                ('image', models.ImageField(blank=True, null=True, upload_to='locations/', verbose_name='Location Image')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Range Location',
                'verbose_name_plural': 'Range Locations',
            },
        ),
        migrations.CreateModel(
            name='TrainingPackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Package Name')),
                ('description', models.TextField(verbose_name='Description')),
                ('price', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Price')),
                ('duration', models.PositiveIntegerField(help_text='Standard duration in minutes', validators=[django.core.validators.MinValueValidator(30), django.core.validators.MaxValueValidator(240)], verbose_name='Duration (minutes)')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this package is currently available', verbose_name='Active')),
                ('image', models.ImageField(blank=True, null=True, upload_to='packages/', verbose_name='Package Image')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Training Package',
                'verbose_name_plural': 'Training Packages',
                'ordering': ['price'],
            },
        ),
        migrations.CreateModel(
            name='Weapon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Weapon Name')),
                ('caliber', models.CharField(max_length=50, verbose_name='Caliber')),
                ('type', models.CharField(choices=[('pistol', 'Pistol'), ('revolver', 'Revolver'), ('rifle', 'Rifle'), ('shotgun', 'Shotgun')], default='pistol', max_length=20, verbose_name='Firearm Type')),
                ('image', models.ImageField(upload_to='weapons/', verbose_name='Weapon Image')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this weapon is currently available', verbose_name='Active')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Weapon',
                'verbose_name_plural': 'Weapons',
                'ordering': ['type', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(verbose_name='Biography')),
                ('certifications', models.TextField(help_text='List certifications separated by commas', verbose_name='Certifications')),
                ('years_experience', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(50)], verbose_name='Years of Experience')),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='instructors/', verbose_name='Profile Picture')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this instructor is currently available', verbose_name='Active')),
                ('available_days', models.CharField(default='Mon-Fri', max_length=100, verbose_name='Available Days')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='instructor_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Instructor',
                'verbose_name_plural': 'Instructors',
            },
        ),
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('content', models.TextField(verbose_name='Testimonial')),
                ('rating', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Rating')),
                ('is_approved', models.BooleanField(default=False, help_text='Whether this testimonial is approved to be shown', verbose_name='Approved')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='testimonials', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Testimonial',
                'verbose_name_plural': 'Testimonials',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Booking Date')),
                ('time', models.TimeField(verbose_name='Booking Time')),
                ('duration', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(30), django.core.validators.MaxValueValidator(240)], verbose_name='Duration (minutes)')),
                ('full_name', models.CharField(max_length=100, verbose_name='Full Name')),
                ('email', models.EmailField(max_length=254, verbose_name='Email Address')),
                ('phone', models.CharField(max_length=20, verbose_name='Phone Number')),
                ('notes', models.TextField(blank=True, verbose_name='Special Requests')),
                ('payment_method', models.CharField(choices=[('paypal', 'PayPal'), ('stripe', 'Credit Card'), ('cash', 'Cash'), ('check', 'Check')], default='paypal', max_length=20, verbose_name='Payment Method')),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='pending', max_length=20, verbose_name='Payment Status')),
                ('transaction_id', models.CharField(blank=True, max_length=100, verbose_name='Transaction ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='Amount Paid')),
                ('is_confirmed', models.BooleanField(default=False, verbose_name='Confirmed')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to=settings.AUTH_USER_MODEL)),
                ('instructor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='lessons.instructor')),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='lessons.trainingpackage')),
                ('weapon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='lessons.weapon')),
            ],
            options={
                'verbose_name': 'Booking',
                'verbose_name_plural': 'Bookings',
                'ordering': ['-date', '-time'],
                'unique_together': {('date', 'time', 'instructor')},
            },
        ),
    ]
