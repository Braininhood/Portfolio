import json
import bleach
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import User, Post, Like, Follow, Comment, Reaction
from .forms import CustomAuthenticationForm, CustomUserCreationForm, PostForm, CommentForm, ProfileUpdateForm
from .utils import sanitize_text, sanitize_html, validate_image_file, detect_sql_injection, detect_xss, escape_json_string, get_nested_comments


def welcome_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    context = {'is_welcome_page': True}
    return render(request, "network/welcome.html", context)


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("welcome"))
    return render(request, "network/index.html")


def following_view(request):
    # This is just to render the index template
    # The React router will handle rendering the Following component
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "network/index.html")


def profile_view(request, username):
    # Check if the requested user exists
    try:
        User.objects.get(username=username)
        # User exists, render the index template for React to handle
        return render(request, "network/index.html")
    except User.DoesNotExist:
        # User doesn't exist, redirect to register page
        return HttpResponseRedirect(reverse("register"))


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        
        # First check if username exists
        if not User.objects.filter(username=username).exists():
            return JsonResponse({
                "error": "Username does not exist.",
                "redirect": True,
                "message": "Username does not exist. Please register instead."
            })
            
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"error": "Invalid password."}, status=400)
    return HttpResponseRedirect(reverse("welcome"))


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        # Check if username already exists
        username = request.POST.get("username", "")
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "error": "Username already exists.",
                "redirect": True,
                "message": "Username already exists. Please login instead."
            })
            
        # Check if email already exists
        email = request.POST.get("email", "")
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                "error": "Email already exists.",
                "message": "Email already exists. Please use a different email."
            })
            
        # Check if passwords match
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirmation", "")
        if password != confirmation:
            return JsonResponse({
                "error": "Passwords do not match.",
                "message": "Passwords do not match. Please try again."
            })
            
        # Create user if all checks pass
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            login(request, user)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({
                "error": "Registration failed.",
                "message": str(e)
            }, status=400)
            
    return HttpResponseRedirect(reverse("welcome"))


# API Routes
@csrf_exempt
@login_required
def create_post(request):
    """API endpoint to create a new post."""
    # Creating a new post must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Handle form data vs JSON data
    if request.content_type and 'application/json' in request.content_type:
        # Get content of post from JSON
        try:
            data = json.loads(request.body)
            content = data.get("content", "")
            
            # Validate and sanitize content
            if not content.strip():
                return JsonResponse({"error": "Post content cannot be empty."}, status=400)
            
            if len(content) > 280:
                return JsonResponse({"error": "Post content exceeds 280 characters."}, status=400)
            
            # Only check for the most obvious security issues
            if detect_sql_injection(content) and detect_xss(content):
                return JsonResponse({"error": "Invalid content detected."}, status=400)
            
            # Sanitize content
            content = sanitize_text(content)
            
            # Create post without image
            post = Post(
                user=request.user,
                content=content
            )
            post.save()
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
    else:
        # Form data with potential image
        form = PostForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Create post
            post = form.save(commit=False)
            post.user = request.user
            post.save()
        else:
            # Return form errors
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                "error": "Failed to create post.",
                "details": errors
            }, status=400)

    # If image exists, include its URL in the response
    image_url = None
    if post.image:
        try:
            image_url = post.image.url
        except ValueError:
            image_url = None

    return JsonResponse({
        "message": "Post created successfully.",
        "post_id": post.id,
        "image_url": image_url
    }, status=201)


def get_posts(request):
    # Get all posts
    posts = Post.objects.all().order_by('-timestamp')
    
    # Get page number and posts per page from query parameters
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page < 1:
            per_page = 10
    except ValueError:
        per_page = 10
    
    # Create paginator instance
    paginator = Paginator(posts, per_page)
    
    # Get specific page
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for JSON response
    posts_data = []
    for post in page_obj:
        likes_count = post.likes.count()
        liked_by_user = request.user.is_authenticated and post.likes.filter(user=request.user).exists()
        comments_count = post.comments.filter(parent=None).count()
        
        # Get reactions data
        reactions = {}
        for reaction in post.reactions.all():
            if reaction.emoji in reactions:
                reactions[reaction.emoji] += 1
            else:
                reactions[reaction.emoji] = 1
        
        # Get user's reactions
        user_reactions = []
        if request.user.is_authenticated:
            user_reactions = list(post.reactions.filter(
                user=request.user
            ).values_list('emoji', flat=True))
        
        # Get image URL if any
        image_url = None
        if post.image:
            try:
                image_url = post.image.url
            except ValueError:
                image_url = None
        
        posts_data.append({
            "id": post.id,
            "user": post.user.username,
            "content": post.content,
            "timestamp": post.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "likes_count": likes_count,
            "liked_by_user": liked_by_user,
            "is_owner": post.user == request.user if request.user.is_authenticated else False,
            "comments_count": comments_count,
            "reactions": reactions,
            "user_reactions": user_reactions,
            "image": image_url
        })
    
    return JsonResponse({
        "posts": posts_data,
        "page": {
            "current": page_obj.number,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "total_pages": paginator.num_pages
        }
    }, safe=False)


def get_following_posts(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
    
    # Get users that the current user follows
    following_users = User.objects.filter(followers__follower=request.user)
    
    # Get posts from those users
    posts = Post.objects.filter(user__in=following_users).order_by('-timestamp')
    
    # Get page number and posts per page from query parameters
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page < 1:
            per_page = 10
    except ValueError:
        per_page = 10
    
    # Create paginator instance
    paginator = Paginator(posts, per_page)
    
    # Get specific page
    page_obj = paginator.get_page(page_number)
    
    # Prepare data for JSON response
    posts_data = []
    for post in page_obj:
        likes_count = post.likes.count()
        liked_by_user = post.likes.filter(user=request.user).exists()
        comments_count = post.comments.filter(parent=None).count()
        
        # Get reactions data
        reactions = {}
        for reaction in post.reactions.all():
            if reaction.emoji in reactions:
                reactions[reaction.emoji] += 1
            else:
                reactions[reaction.emoji] = 1
        
        # Get user's reactions
        user_reactions = list(post.reactions.filter(
            user=request.user
        ).values_list('emoji', flat=True))
        
        # Get image URL if any
        image_url = None
        if post.image:
            try:
                image_url = post.image.url
            except ValueError:
                image_url = None
        
        posts_data.append({
            "id": post.id,
            "user": post.user.username,
            "content": post.content,
            "timestamp": post.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "likes_count": likes_count,
            "liked_by_user": liked_by_user,
            "is_owner": post.user == request.user,
            "comments_count": comments_count,
            "reactions": reactions,
            "user_reactions": user_reactions,
            "image": image_url
        })
    
    return JsonResponse({
        "posts": posts_data,
        "page": {
            "current": page_obj.number,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "total_pages": paginator.num_pages
        }
    }, safe=False)


def get_user_profile(request, username):
    # Get the user
    profile_user = get_object_or_404(User, username=username)
    
    # Get user's posts
    posts = Post.objects.filter(user=profile_user).order_by('-timestamp')
    
    # Get page number and posts per page from query parameters
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page < 1:
            per_page = 10
    except ValueError:
        per_page = 10
    
    # Create paginator instance
    paginator = Paginator(posts, per_page)
    
    # Get specific page
    page_obj = paginator.get_page(page_number)
    
    # Prepare posts data
    posts_data = []
    for post in page_obj:
        likes_count = post.likes.count()
        liked_by_user = request.user.is_authenticated and post.likes.filter(user=request.user).exists()
        comments_count = post.comments.filter(parent=None).count()
        
        # Get reactions data
        reactions = {}
        for reaction in post.reactions.all():
            if reaction.emoji in reactions:
                reactions[reaction.emoji] += 1
            else:
                reactions[reaction.emoji] = 1
        
        # Get user's reactions
        user_reactions = []
        if request.user.is_authenticated:
            user_reactions = list(post.reactions.filter(
                user=request.user
            ).values_list('emoji', flat=True))
        
        # Get image URL if any
        image_url = None
        if post.image:
            try:
                image_url = post.image.url
            except ValueError:
                image_url = None
        
        posts_data.append({
            "id": post.id,
            "user": post.user.username,
            "content": post.content,
            "timestamp": post.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "likes_count": likes_count,
            "liked_by_user": liked_by_user,
            "is_owner": post.user == request.user if request.user.is_authenticated else False,
            "comments_count": comments_count,
            "reactions": reactions,
            "user_reactions": user_reactions,
            "image": image_url
        })
    
    # Count followers and following
    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()
    posts_count = Post.objects.filter(user=profile_user).count()
    
    # Check if current user follows the profile user
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(follower=request.user, followed=profile_user).exists()
    
    # Safely get avatar URL
    avatar_url = None
    if profile_user.avatar and profile_user.avatar.name:
        try:
            avatar_url = profile_user.avatar.url
        except ValueError:
            avatar_url = None
    
    return JsonResponse({
        "username": profile_user.username,
        "avatar": avatar_url,
        "bio": profile_user.bio,
        "followers_count": followers_count,
        "following_count": following_count,
        "posts_count": posts_count, 
        "is_following": is_following,
        "is_self": request.user.is_authenticated and request.user == profile_user,
        "posts": posts_data,
        "page": {
            "current": page_obj.number,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "total_pages": paginator.num_pages
        }
    }, safe=False)


@csrf_exempt
@login_required
def toggle_like(request, post_id):
    # Toggle like must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # Get the post
    post = get_object_or_404(Post, pk=post_id)
    
    # Check if user already liked the post
    like_exists = Like.objects.filter(user=request.user, post=post).exists()
    
    if like_exists:
        # If like exists, remove it
        Like.objects.filter(user=request.user, post=post).delete()
        liked = False
    else:
        # If like doesn't exist, create it
        like = Like(user=request.user, post=post)
        like.save()
        liked = True
    
    # Return updated likes count
    likes_count = post.likes.count()
    
    return JsonResponse({
        "likes_count": likes_count,
        "liked": liked
    }, safe=False)


@csrf_exempt
@login_required
def toggle_follow(request, username):
    # Toggle follow must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # Get the user to follow/unfollow
    followed_user = get_object_or_404(User, username=username)
    
    # Cannot follow yourself
    if request.user == followed_user:
        return JsonResponse({"error": "Cannot follow yourself."}, status=400)
    
    # Check if already following
    follow_exists = Follow.objects.filter(follower=request.user, followed=followed_user).exists()
    
    if follow_exists:
        # If follow exists, remove it
        Follow.objects.filter(follower=request.user, followed=followed_user).delete()
        following = False
    else:
        # If follow doesn't exist, create it
        follow = Follow(follower=request.user, followed=followed_user)
        follow.save()
        following = True
    
    # Return updated followers count
    followers_count = followed_user.followers.count()
    
    return JsonResponse({
        "followers_count": followers_count,
        "following": following
    }, safe=False)


@csrf_exempt
@login_required
def edit_post(request, post_id):
    """API endpoint to edit an existing post."""
    # Edit post must be via PUT
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)
    
    # Get the post
    post = get_object_or_404(Post, pk=post_id)
    
    # Check if user is the owner of the post
    if request.user != post.user:
        return JsonResponse({"error": "Cannot edit another user's post."}, status=403)
    
    try:
        # Get data from request
        data = json.loads(request.body)
        content = data.get("content", "")
        
        # Validate content
        if not content.strip():
            return JsonResponse({"error": "Post content cannot be empty."}, status=400)
        
        if len(content) > 280:
            return JsonResponse({"error": "Post content exceeds 280 characters."}, status=400)
        
        # Only check for the most obvious security issues
        if detect_sql_injection(content) and detect_xss(content):
            return JsonResponse({"error": "Invalid content detected."}, status=400)
        
        # Sanitize content
        content = sanitize_text(content)
        
        # Update post
        post.content = content
        post.save()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
    
    return JsonResponse({"message": "Post updated successfully."}, status=200)


@csrf_exempt
@login_required
def create_comment(request, post_id):
    """API endpoint to create a new comment or reply."""
    # Creating a new comment must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # Get the post
    post = get_object_or_404(Post, pk=post_id)
    
    try:
        # Get data from request
        data = json.loads(request.body)
        
        # Use our form for validation
        form = CommentForm(data)
        
        if form.is_valid():
            content = form.cleaned_data['content']
            parent_id = form.cleaned_data.get('parent_id')
            
            # Create comment
            comment = Comment(
                user=request.user,
                post=post,
                content=content
            )
            
            # Set parent comment if specified
            if parent_id:
                # Verify the parent comment exists and belongs to this post
                parent_comment = get_object_or_404(Comment, pk=parent_id)
                if parent_comment.post.id != post.id:
                    return JsonResponse({"error": "Parent comment does not belong to this post."}, status=400)
                comment.parent = parent_comment
            
            comment.save()
            
            return JsonResponse({
                "id": comment.id,
                "user": comment.user.username,
                "content": comment.content,
                "timestamp": comment.timestamp.strftime("%b %d %Y, %I:%M %p"),
                "parent_id": parent_id
            }, status=201)
        else:
            # Return form errors
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                "error": "Failed to create comment.",
                "details": errors
            }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body."}, status=400)


def get_comments(request, post_id):
    # Get the post
    post = get_object_or_404(Post, pk=post_id)
    
    # Get top-level comments for the post
    top_comments = Comment.objects.filter(post=post, parent=None)
    
    # Prepare data for JSON response by recursively processing comments
    comments_data = []
    for comment in top_comments:
        comment_data = get_nested_comments(comment, request)
        comments_data.append(comment_data)
    
    return JsonResponse({
        "comments": comments_data
    }, safe=False)


@csrf_exempt
@login_required
def edit_comment(request, comment_id):
    """API endpoint to edit an existing comment."""
    # Edit comment must be via PUT
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)
    
    # Get the comment
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # Check if user is the owner of the comment
    if request.user != comment.user:
        return JsonResponse({"error": "Cannot edit another user's comment."}, status=403)
    
    try:
        # Get data from request
        data = json.loads(request.body)
        
        # Use our form for validation
        form = CommentForm(data)
        
        if form.is_valid():
            content = form.cleaned_data['content']
            
            # Update comment
            comment.content = content
            comment.is_edited = True
            comment.save()
            
            return JsonResponse({
                "message": "Comment updated successfully.",
                "content": content,
                "is_edited": True
            }, status=200)
        else:
            # Return form errors
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                "error": "Failed to update comment.",
                "details": errors
            }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body."}, status=400)


def toggle_post_reaction(request, post_id):
    """
    API endpoint to toggle a reaction on a post.
    """
    # Make sure request method is POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    # Get the post
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    # Get request data
    data = json.loads(request.body)
    emoji = data.get("emoji", "")

    # Make sure emoji is provided
    if not emoji:
        return JsonResponse({"error": "Emoji is required."}, status=400)
        
    # Check if user has already reacted with this emoji
    existing_reaction = Reaction.objects.filter(
        user=request.user,
        post=post,
        emoji=emoji
    ).first()
    
    if existing_reaction:
        # If the reaction exists, remove it
        existing_reaction.delete()
    else:
        # Otherwise, create a new reaction
        Reaction.objects.create(
            user=request.user,
            post=post,
            emoji=emoji
        )
    
    # Get updated reactions
    reactions = {}
    for reaction in Reaction.objects.filter(post=post):
        if reaction.emoji in reactions:
            reactions[reaction.emoji] += 1
        else:
            reactions[reaction.emoji] = 1
    
    # Get user's reactions
    user_reactions = list(Reaction.objects.filter(
        user=request.user,
        post=post
    ).values_list('emoji', flat=True))
    
    return JsonResponse({
        "reactions": reactions,
        "user_reactions": user_reactions
    })


def toggle_comment_reaction(request, comment_id):
    # Toggle reaction must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    # Get comment
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found."}, status=404)
    
    # Get emoji from request
    data = json.loads(request.body)
    emoji = data.get("emoji", "")
    
    if not emoji:
        return JsonResponse({"error": "Emoji is required."}, status=400)
    
    # Check if user has already reacted with this emoji
    try:
        reaction = Reaction.objects.get(
            user=request.user,
            comment=comment,
            emoji=emoji
        )
        # If reaction exists, delete it (toggle off)
        reaction.delete()
        action = "removed"
    except Reaction.DoesNotExist:
        # If reaction doesn't exist, create it (toggle on)
        reaction = Reaction(
            user=request.user,
            comment=comment,
            emoji=emoji
        )
        reaction.save()
        action = "added"
    
    # Get updated reaction counts
    reactions = {}
    for r in comment.reactions.all():
        if r.emoji in reactions:
            reactions[r.emoji] += 1
        else:
            reactions[r.emoji] = 1
    
    # Get user's reactions
    user_reactions = list(comment.reactions.filter(
        user=request.user
    ).values_list('emoji', flat=True))
    
    return JsonResponse({
        "action": action,
        "reactions": reactions,
        "user_reactions": user_reactions
    })


def get_user_stats(request, username):
    """Get basic statistics for a user."""
    # Get the user
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)
    
    # Count posts
    posts_count = Post.objects.filter(user=user).count()
    
    # Count followers
    followers_count = Follow.objects.filter(followed=user).count()
    
    # Count following
    following_count = Follow.objects.filter(follower=user).count()
    
    # Check if current user is following this user
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
    
    return JsonResponse({
        "username": user.username,
        "posts_count": posts_count,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following
    })


# Add a new API endpoint for deleting posts
@csrf_exempt
@login_required
def delete_post(request, post_id):
    # Deleting a post must be via DELETE
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE request required."}, status=400)
    
    try:
        # Get the post
        post = Post.objects.get(pk=post_id)
        
        # Check if user is the post owner
        if post.user != request.user:
            return JsonResponse({"error": "You can only delete your own posts."}, status=403)
        
        # Delete the post
        post.delete()
        
        return JsonResponse({"message": "Post deleted successfully."}, status=200)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)


# Add a new API endpoint for deleting comments
@csrf_exempt
@login_required
def delete_comment(request, comment_id):
    # Deleting a comment must be via DELETE
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE request required."}, status=400)
    
    try:
        # Get the comment
        comment = Comment.objects.get(pk=comment_id)
        
        # Check if user is the comment owner
        if comment.user != request.user:
            return JsonResponse({"error": "You can only delete your own comments."}, status=403)
        
        # Delete the comment
        comment.delete()
        
        return JsonResponse({"message": "Comment deleted successfully."}, status=200)
    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found."}, status=404)


@login_required
def edit_profile_view(request):
    """Render the profile edit page"""
    return render(request, "network/edit_profile.html")


@csrf_exempt
@login_required
def update_profile(request):
    """API endpoint to update user profile information."""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
    
    if form.is_valid():
        # Save the sanitized form data
        profile = form.save(commit=False)
        
        # Form's clean methods already handle:
        # - Bio sanitization (using bleach)
        # - Avatar file type and size validation
        profile.save()
        
        # Return success response
        return JsonResponse({
            "message": "Profile updated successfully.",
            "avatar_url": profile.avatar.url if profile.avatar else None
        })
    else:
        # Return form errors
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = [str(error) for error in error_list]
        
        return JsonResponse({
            "error": "Failed to update profile.",
            "details": errors
        }, status=400)
