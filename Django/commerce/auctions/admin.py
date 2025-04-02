from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Listing, Bid, Comment, Category, Watchlist

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'current_price', 'active', 'created_at')
    list_filter = ('active', 'category', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('current_price', 'created_at', 'image_url')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'creator')
        }),
        ('Pricing', {
            'fields': ('starting_bid', 'current_price')
        }),
        ('Details', {
            'fields': ('image', 'category', 'active', 'winner')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

class BidAdmin(admin.ModelAdmin):
    list_display = ('listing', 'bidder', 'amount', 'created_at')
    list_filter = ('listing', 'bidder', 'created_at')
    search_fields = ('listing__title', 'bidder__username')
    readonly_fields = ('created_at',)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('listing', 'author', 'created_at')
    list_filter = ('listing', 'author', 'created_at')
    search_fields = ('listing__title', 'author__username', 'content')
    readonly_fields = ('created_at',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'listings_count')
    filter_horizontal = ('listings',)
    
    def listings_count(self, obj):
        return obj.listings.count()
    listings_count.short_description = 'Listings Count'

# Register the User model with the admin interface
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['deactivate_users']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Deactivate selected users"

# Register other models
admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Watchlist, WatchlistAdmin)
