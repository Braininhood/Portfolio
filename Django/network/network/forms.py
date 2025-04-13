from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator, FileExtensionValidator, MaxLengthValidator
from .models import User, Post, Comment

# Custom validators
alphanumeric_validator = RegexValidator(
    r'^[a-zA-Z0-9_]+$',
    'Only alphanumeric characters and underscores are allowed.'
)

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        validators=[alphanumeric_validator]
    )
    email = forms.EmailField(
        required=True,
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered")
        return email

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class PostForm(forms.ModelForm):
    content = forms.CharField(
        max_length=280,
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': "What's on your mind?"}),
        validators=[MaxLengthValidator(280)]
    )
    image = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
        ],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/png, image/jpeg, image/jpg'})
    )

    class Meta:
        model = Post
        fields = ['content', 'image']

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (5MB max)
            if image.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError("File size too large. Maximum allowed size is 5MB.")
        return image

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        max_length=280,
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Write a comment...'}),
        validators=[MaxLengthValidator(280)]
    )
    parent_id = forms.IntegerField(required=False)

    class Meta:
        model = Comment
        fields = ['content']

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content.strip():
            raise forms.ValidationError("Comment cannot be empty")
        return content

class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        validators=[MaxLengthValidator(500)]
    )
    avatar = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
        ],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/png, image/jpeg, image/jpg'})
    )

    class Meta:
        model = User
        fields = ['bio', 'avatar']

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Check file size (5MB max)
            if avatar.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError("File size too large. Maximum allowed size is 5MB.")
        return avatar

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        # Sanitize bio to prevent XSS
        import bleach
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a']
        allowed_attributes = {'a': ['href', 'title']}
        bio = bleach.clean(bio, tags=allowed_tags, attributes=allowed_attributes)
        return bio 