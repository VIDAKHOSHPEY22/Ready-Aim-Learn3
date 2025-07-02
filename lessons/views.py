from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import FAQComment
from .forms import FAQCommentForm

def home(request):
    return render(request, 'home.html')

def packages(request):
    return render(request, 'packages.html')

def booking(request):
    return render(request, 'booking.html')

def about(request):
    return render(request, 'about.html')

def faq(request):
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
            comment.is_active = True  # این خط کامنت‌ها را فعال می‌کند
            
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
    return render(request, 'faq.html', context)

def contact(request):
    return render(request, 'contact.html')

def legal(request):
    return render(request, 'legal.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Automatically log the user in after signup
            from django.contrib.auth import login
            login(request, user)
            
            messages.success(request, "Account created successfully! You are now logged in.")
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def delete_comment(request, comment_id):
    try:
        comment = FAQComment.objects.get(id=comment_id, user=request.user)
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
    except FAQComment.DoesNotExist:
        messages.error(request, "Comment not found or you don't have permission to delete it.")
    
    return redirect('faq')