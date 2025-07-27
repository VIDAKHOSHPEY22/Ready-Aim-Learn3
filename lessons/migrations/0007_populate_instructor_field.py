from django.db import migrations

def set_default_instructor(apps, schema_editor):
    Booking = apps.get_model('lessons', 'Booking')
    Instructor = apps.get_model('lessons', 'Instructor')
    
    # Get Luis David Valencia as the default instructor
    luis_instructor = Instructor.objects.filter(user__username='luisdavid').first()
    
    if luis_instructor:
        # Update all bookings with NULL instructor
        updated = Booking.objects.filter(instructor__isnull=True).update(instructor=luis_instructor)
        print(f"Updated {updated} bookings with instructor Luis David Valencia Hernandez")

class Migration(migrations.Migration):
    dependencies = [
        # This should point to my last migration file
        ('lessons', '0006_set_default_instructor'),  
    ]

    operations = [
        migrations.RunPython(set_default_instructor),
    ]