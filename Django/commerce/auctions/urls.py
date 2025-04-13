from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path('create', views.create_listing, name='create_listing'),
    path('listing/<int:listing_id>', views.listing_detail, name='listing_detail'),
    path('listing/', views.redirect_to_active_listings, name='redirect_to_active_listings'),
    path('watchlist', views.watchlist, name='watchlist'),
    path('categories', views.categories, name='categories'),
    path('category/<int:category_id>', views.category_detail, name='category_detail'),
    path('edit_listing/<int:listing_id>', views.edit_listing, name='edit_listing'),
]
