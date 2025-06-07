from django.contrib import admin
from .models import CarMake, CarModel, Dealer, Review


# Register your models here.

# CarModelInline class
class CarModelInline(admin.StackedInline):
    model = CarModel
    extra = 2


# CarModelAdmin class
class CarModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'car_make', 'type', 'year', 'dealer_id']
    list_filter = ['car_make', 'type', 'year']
    search_fields = ['name', 'car_make__name']


# CarMakeAdmin class with CarModelInline
class CarMakeAdmin(admin.ModelAdmin):
    inlines = [CarModelInline]
    list_display = ['name', 'description', 'country', 'founded_year']
    list_filter = ['country']
    search_fields = ['name', 'description']


# DealerAdmin class
class DealerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'city', 'state', 'zip']
    list_filter = ['state', 'city']
    search_fields = ['full_name', 'city', 'state', 'address']


# ReviewAdmin class
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'dealer', 'car_make', 'car_model', 'sentiment',
                    'purchase']
    list_filter = ['sentiment', 'purchase', 'dealer', 'car_make']
    search_fields = ['name', 'review', 'dealer__full_name']
    readonly_fields = ['sentiment']  # Make sentiment read-only


# Register models here
admin.site.register(CarMake, CarMakeAdmin)
admin.site.register(CarModel, CarModelAdmin)
admin.site.register(Dealer, DealerAdmin)
admin.site.register(Review, ReviewAdmin)
