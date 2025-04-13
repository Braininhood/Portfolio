from django import forms
from .models import User, Listing, Bid, Comment, Watchlist, Category, ListingImage
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator, validate_email, RegexValidator

class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Display hierarchical structure
        return f"{'—' * obj.get_level()} {obj.name}"

class ListingForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Select a category"
    )
    starting_bid = forms.DecimalField(
        validators=[MinValueValidator(0.01)],
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
    title = forms.CharField(
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_ ]+$',
                message='Title can only contain letters, numbers, spaces, and underscores.'
            )
        ]
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Add a description...',
            'class': 'form-control',
            'style': 'width: 300px; height: 100px;'  # Adjust width and height here
        }),
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_ .,!?]+$',
                message='Description can only contain letters, numbers, spaces, and basic punctuation.'
            )
        ]
    )

    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'category']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add a description...',
                'class': 'form-control',
                'style': 'width: 300px; height: 100px;'  # Adjust width and height here
            }),
        }
        labels = {
            'image': 'Upload Image (optional)',
            'category': 'Category (optional)',
        }

    def clean(self):
        cleaned_data = super().clean()
        images = self.files.getlist('images')

        # Check for duplicate images
        unique_images = set()
        for image in images:
            if image.name in unique_images:
                raise ValidationError(f"Duplicate image detected: {image.name}. Please upload unique images.")
            unique_images.add(image.name)

        return cleaned_data

class RegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=64,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='Username can only contain letters, numbers, and underscores.'
            )
        ]
    )
    email = forms.EmailField(validators=[validate_email])
    password = forms.CharField(widget=forms.PasswordInput)
    confirmation = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("confirmation")
        email = cleaned_data.get("email")

        # Check if passwords match
        if password and confirmation and password != confirmation:
            raise ValidationError("Passwords must match.")

        # Check if username or email already exists
        username = cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already taken. Please log in.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered. Please log in.")

        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True) 