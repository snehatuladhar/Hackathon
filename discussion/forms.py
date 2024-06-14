from django import forms
from .models import StudentDiscussion, InstructorDiscussion


class StudentDiscussionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentDiscussionForm, self).__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['content'].label = ''

    class Meta:
        model = StudentDiscussion
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'id': 'content', 'name': 'content', 'placeholder': 'Write message...', 'type': 'text'}),
        }


class InstructorDiscussionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InstructorDiscussionForm, self).__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['content'].label = ''

    class Meta:
        model = InstructorDiscussion
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'id': 'content', 'name': 'content', 'placeholder': 'Write message...', 'type': 'text'}),
        }
