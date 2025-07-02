from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class FAQComment(models.Model):
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
        verbose_name='Comment'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Posted at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last updated'
    )

    class Meta:
        ordering = ['-created_at']  # Show newest comments first
        verbose_name = 'FAQ Comment'
        verbose_name_plural = 'FAQ Comments'

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