from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from decimal import Decimal
import logging

from .models import User, Listing, Bid, Comment, Watchlist, Category, ListingImage
from .forms import ListingForm, RegistrationForm, LoginForm

logger = logging.getLogger(__name__)

def index(request):
    try:
        active_listings = Listing.objects.filter(active=True).order_by('-created_at')
        return render(request, "auctions/index.html", {
            'listings': active_listings
        })
    except Exception as e:
        logger.error(f"Error in index view: {e}")
        raise


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse("index"))
            else:
                # Check if the username exists in the database
                if not User.objects.filter(username=username).exists():
                    messages.info(request, 'Username not found. Please register.')
                    return redirect('register')
                else:
                    form.add_error(None, "Invalid username and/or password.")
    else:
        form = LoginForm()
    return render(request, "auctions/login.html", {
        "form": form
    })


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return HttpResponseRedirect(reverse("index"))
    return render(request, "auctions/logout.html")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create the user
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            # Log the user in and redirect to index
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
    else:
        form = RegistrationForm()
    return render(request, "auctions/register.html", {
        "form": form
    })


@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                listing = form.save(commit=False)
                listing.creator = request.user
                listing.save()
                # Save all uploaded images
                for image in request.FILES.getlist('images'):
                    ListingImage.objects.create(listing=listing, image=image)
                messages.success(request, 'Listing created successfully!')
                return redirect("listing_detail", listing_id=listing.id)
            except Exception as e:
                messages.error(request, f'An error occurred while creating the listing: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ListingForm()
    return render(request, "auctions/create_listing.html", {"form": form})


def listing_detail(request, listing_id):
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        messages.error(request, 'The listing you are looking for does not exist.')
        return redirect('index')

    # Handle closing auction
    if 'close_auction' in request.POST:
        if request.user == listing.creator:
            # Delete all associated images
            listing.images.all().delete()
            # Delete the listing
            listing.delete()
            messages.success(request, 'Listing and all associated data have been deleted.')
            return redirect('index')
        else:
            messages.error(request, 'You can only close your own listings.')
            return redirect("listing_detail", listing_id=listing.id)

    images = listing.images.all()  # Get all images for the listing
    user = request.user
    in_watchlist = False
    is_creator = False
    is_winner = False

    if user.is_authenticated:
        # Check if listing is in user's watchlist
        in_watchlist = Watchlist.objects.filter(user=user, listings=listing).exists()
        # Check if user is the creator
        is_creator = user == listing.creator
        # Check if user is the winner
        is_winner = user == listing.winner

    # Handle actions with login redirect
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        # Handle bidding
        if 'bid_amount' in request.POST:
            if not user.is_authenticated:
                return redirect('login')
            
            try:
                bid_amount = Decimal(request.POST['bid_amount'])
                if bid_amount < listing.current_price + Decimal('1.00'):
                    messages.error(request, 'Bid must be at least $1 higher than the current price.')
                elif bid_amount > listing.current_price * Decimal('10.00'):
                    messages.error(request, 'Bid cannot be more than 10 times the current price.')
                else:
                    # Create and save the bid
                    bid = Bid.objects.create(
                        amount=bid_amount,
                        bidder=request.user,
                        listing=listing
                    )
                    listing.current_price = bid_amount
                    listing.save()
                    messages.success(request, 'Bid placed successfully!')
                return redirect("listing_detail", listing_id=listing.id)
            except ValueError:
                messages.error(request, 'Invalid bid amount. Please enter a valid number.')

        # Handle watchlist
        if 'watchlist' in request.POST:
            if not user.is_authenticated:
                return redirect('login')
            
            watchlist, created = Watchlist.objects.get_or_create(user=user)
            if in_watchlist:
                watchlist.listings.remove(listing)
                messages.success(request, 'Removed from your watchlist.')
            else:
                watchlist.listings.add(listing)
                messages.success(request, 'Added to your watchlist!')

        # Handle comments
        if 'comment' in request.POST:
            if not user.is_authenticated:
                return redirect('login')
            
            comment_text = request.POST['comment']
            if comment_text.strip():
                Comment.objects.create(
                    content=comment_text,
                    author=user,
                    listing=listing
                )
                messages.success(request, 'Your comment was posted!')

    # Get all bids and comments
    bids = listing.bids.order_by('-created_at')
    comments = listing.comments.order_by('-created_at')
    paginator = Paginator(comments, 10)  # Show 10 comments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'auctions/listing_detail.html', {
        'listing': listing,
        'images': images,  # Pass images to the template
        'in_watchlist': in_watchlist,
        'is_creator': is_creator,
        'is_winner': is_winner,
        'bids': bids,
        'comments': comments,
        'page_obj': page_obj,
    })


@login_required
def watchlist(request):
    # Get or create watchlist for the user
    watchlist, created = Watchlist.objects.get_or_create(user=request.user)
    # Get all listings in the watchlist
    listings = watchlist.listings.filter(active=True).order_by('-created_at')
    
    return render(request, 'auctions/watchlist.html', {
        'listings': listings
    })


def categories(request):
    # Get all categories that have active listings
    active_categories = Category.objects.filter(listing__active=True).distinct()
    return render(request, "auctions/categories.html", {
        'categories': active_categories
    })


def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    # Get active listings for the category
    active_listings = Listing.objects.filter(category=category, active=True).order_by('-created_at')
    return render(request, "auctions/category_detail.html", {
        'category': category,
        'listings': active_listings
    })


@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Check if the logged-in user is the creator of the listing
    if request.user != listing.creator:
        messages.error(request, 'You can only edit your own listings.')
        return redirect("listing_detail", listing_id=listing.id)

    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            # Handle image deletions
            delete_images = request.POST.getlist('delete_images')
            for image_id in delete_images:
                image = ListingImage.objects.get(id=image_id)
                image.delete()
            
            # Handle new image uploads
            images = request.FILES.getlist('images')
            for image in images:
                ListingImage.objects.create(listing=listing, image=image)
            
            # Save the listing
            form.save()
            messages.success(request, 'Listing updated successfully!')
            return redirect("listing_detail", listing_id=listing.id)
    else:
        form = ListingForm(instance=listing)
    return render(request, "auctions/edit_listing.html", {
        "form": form,
        "listing": listing
    })


def redirect_to_active_listings(request):
    return redirect('index')  # Redirect to the active listings page
