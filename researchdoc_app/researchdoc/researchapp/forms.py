"""
All the form classes used by the views.

A `ModelForm` is just a `Form` that auto-generates its fields from a
model's columns saves a lot of typing. Each form here either:
  - wraps one of our own models (ResearchProjectForm, ResourceForm…), or
  - extends an allauth form to add extra fields (CustomSignupForm), or
  - is a free-standing form for a page that doesn't map directly to a
    model (PreferencesForm for the dark-mode picker).
"""
from django import forms
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from .models import (
    UserDetail, ResearchProject, Resource,
    ResearchSummary, ComparisonTable,
)


try:
    from allauth.account.forms import SignupForm as _AllauthSignupForm
    _AllauthBase = _AllauthSignupForm
except Exception:  # pragma: no cover allauth always present in this project
    _AllauthBase = forms.Form


class CustomSignupForm(_AllauthBase):

    first_name = forms.CharField(
        max_length=30, required=True, label='First name',
        widget=forms.TextInput(attrs={'placeholder': 'Jane'}),
    )
    last_name = forms.CharField(
        max_length=30, required=True, label='Last name',
        widget=forms.TextInput(attrs={'placeholder': 'Doe'}),
    )

    def signup(self, request, user):
        """allauth calls this once the User has been created write our extras."""
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        from .models import UserDetail
        UserDetail.objects.filter(user=user).update(
            firstname=self.cleaned_data['first_name'],
            surname=self.cleaned_data['last_name'],
        )
        return user


class UserSettingsForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = UserDetail
        fields = ['firstname', 'surname', 'mobile', 'bio']
        widgets = {
            'firstname': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'firstname': 'First name',
            'surname': 'Last name',
            'mobile': 'Mobile',
            'bio': 'Bio',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.instance and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError('That email is already in use.')
        return email

    def save(self, commit=True):
        user_detail = super().save(commit=False)
        user = user_detail.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('firstname') or user.first_name
        user.last_name = self.cleaned_data.get('surname') or user.last_name
        user.save()
        if commit:
            user_detail.save()
        return user_detail


class PreferencesForm(forms.Form):
    """Display preferences theme."""
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'System default'),
    ]
    theme = forms.ChoiceField(
        choices=THEME_CHOICES,
        widget=forms.RadioSelect,
        label='Appearance',
    )


class UserDetailFullForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to keep the existing password when editing.",
    )

    class Meta:
        model = UserDetail
        fields = ['firstname', 'surname', 'mobile', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill username and email from the linked User on edit
        if self.instance and self.instance.pk and self.instance.user_id:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

        # Apply Bootstrap classes to all fields
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()

    def save(self, commit=True):
        user_detail = super().save(commit=False)
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data.get('password')

        if user_detail.pk and user_detail.user_id:
            # Update existing user
            user = user_detail.user
            user.username = username
            user.email = email
            if password:
                user.set_password(password)
            user.save()
        else:
            # Create new user
            user = User.objects.create_user(
                username=username, email=email,
                password=password or get_random_string(12),
            )
            user_detail.user = user

        if commit:
            user_detail.save()
        return user_detail


class ResearchProjectForm(forms.ModelForm):
    """Project create/edit form."""
    class Meta:
        model = ResearchProject
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Quantum Computing Trends 2024',
                'aria-label': 'Project name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Briefly outline the research goals, methodology, and expected outcomes...',
                'aria-label': 'Project description',
            }),
        }
        labels = {'title': 'Project Name', 'description': 'Description'}


class ResourceForm(forms.ModelForm):
    """Resource (paper or link) form with file validation."""
    class Meta:
        model = Resource
        fields = [
            'title', 'resource_type', 'file', 'url', 'description',
            'authors', 'year', 'venue', 'volume', 'issue', 'pages', 'doi',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Attention Is All You Need',
            }),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control', 'accept': '.pdf',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://...',
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'authors': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Surname, F.; Surname, F.',
            }),
            'year': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g., 2024',
            }),
            'venue': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Journal / conference / publisher',
            }),
            'volume': forms.TextInput(attrs={'class': 'form-control'}),
            'issue': forms.TextInput(attrs={'class': 'form-control'}),
            'pages': forms.TextInput(attrs={'class': 'form-control'}),
            'doi': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '10.xxxx/...',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        rtype = cleaned.get('resource_type')
        file = cleaned.get('file')
        url = cleaned.get('url')
        if rtype == Resource.PAPER and not file:
            raise forms.ValidationError('Please upload a PDF for paper resources.')
        if rtype == Resource.LINK and not url:
            raise forms.ValidationError('Please provide a URL for link resources.')
        if file:
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are accepted.')
            if file.size > 25 * 1024 * 1024:
                raise forms.ValidationError('File size must be 25 MB or less.')
        return cleaned


class ResearchSummaryForm(forms.ModelForm):
    class Meta:
        model = ResearchSummary
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Summary title',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 12, 'id': 'summary-editor',
            }),
        }


class ComparisonTableForm(forms.ModelForm):
    class Meta:
        model = ComparisonTable
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Vector Database Comparison',
            }),
        }
