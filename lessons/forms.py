from django import forms
from .models import FAQComment

class FAQCommentForm(forms.ModelForm):
    class Meta:
        model = FAQComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write your comment here...',
                'class': 'form-control'
            })
        }
    
    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content) < 5:
            raise forms.ValidationError("Comment must be at least 5 characters")
        return content