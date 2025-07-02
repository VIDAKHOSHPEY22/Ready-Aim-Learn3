from django.contrib import admin
from .models import FAQComment

@admin.register(FAQComment)
class FAQCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_content', 'parent', 'created_at', 'is_reply')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'user__username')
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
    
    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Is Reply?'