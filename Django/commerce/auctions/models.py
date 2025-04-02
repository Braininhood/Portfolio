from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils.text import slugify


class User(AbstractUser):
    # Additional user fields can be added here if needed
    pass

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    slug = models.SlugField(unique=True, blank=True, null=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_full_path(self):
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_level(self):
        """Returns the level of the category in the hierarchy."""
        level = 0
        parent = self.parent
        while parent is not None:
            level += 1
            parent = parent.parent
        return level

class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(
        upload_to='listing_images/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_listings')

    def __str__(self):
        return self.title

    def image_url(self):
        """Returns the URL of the image if it exists, otherwise returns None."""
        if self.image:
            return self.image.url
        return None
    image_url.short_description = 'Image URL'

    def save(self, *args, **kwargs):
        # Set current_price to starting_bid when first created
        if not self.pk:
            self.current_price = self.starting_bid
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Remove the listing from all watchlists
        Watchlist.objects.filter(listings=self).update(listings=None)
        # Delete all associated images
        self.images.all().delete()
        # Delete the listing
        super().delete(*args, **kwargs)

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')

    def __str__(self):
        return f"Image for {self.listing.title}"

class Bid(models.Model):
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bidder.username} - ${self.amount}"

class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username}"

class Watchlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='watchlist')
    listings = models.ManyToManyField(Listing, blank=True)

    def __str__(self):
        return f"{self.user.username}'s watchlist"
