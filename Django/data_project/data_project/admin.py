from django.contrib import admin
from .models import SlideImage, UserDataFile, Visualization

@admin.register(SlideImage)
class SlideImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('order',)

@admin.register(UserDataFile)
class UserDataFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'file_type', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('title', 'user__username')
    date_hierarchy = 'uploaded_at'

@admin.register(Visualization)
class VisualizationAdmin(admin.ModelAdmin):
    list_display = ('title', 'data_file', 'viz_type', 'created_at')
    list_filter = ('viz_type', 'created_at')
    search_fields = ('title', 'data_file__title')
    date_hierarchy = 'created_at'
