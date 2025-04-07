from django.urls import path

from . import views

urlpatterns = [
    path("", views.welcome_view, name="welcome"),
    path("index", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("following", views.following_view, name="following"),
    path("profile/<str:username>", views.profile_view, name="profile"),
    path("edit-profile", views.edit_profile_view, name="edit_profile"),

    # API Routes
    path("api/posts", views.get_posts, name="get_posts"),
    path("api/posts/create", views.create_post, name="create_post"),
    path("api/posts/<int:post_id>/edit", views.edit_post, name="edit_post"),
    path("api/posts/<int:post_id>/like", views.toggle_like, name="toggle_like"),
    path("api/posts/<int:post_id>/delete", views.delete_post, name="delete_post"),
    path("api/posts/following", views.get_following_posts, name="get_following_posts"),
    path("api/users/<str:username>", views.get_user_profile, name="get_user_profile"),
    path("api/users/<str:username>/follow", views.toggle_follow, name="toggle_follow"),
    path("api/users/<str:username>/stats", views.get_user_stats, name="get_user_stats"),
    path("api/profile/update", views.update_profile, name="update_profile"),
    
    # Comment Routes
    path("api/posts/<int:post_id>/comments", views.get_comments, name="get_comments"),
    path("api/posts/<int:post_id>/comments/create", views.create_comment, name="create_comment"),
    path("api/comments/<int:comment_id>/edit", views.edit_comment, name="edit_comment"),
    path("api/comments/<int:comment_id>/delete", views.delete_comment, name="delete_comment"),
    
    # Reaction Routes
    path("api/posts/<int:post_id>/reaction", views.toggle_post_reaction, name="toggle_post_reaction"),
    path("api/comments/<int:comment_id>/reaction", views.toggle_comment_reaction, name="toggle_comment_reaction")
]
