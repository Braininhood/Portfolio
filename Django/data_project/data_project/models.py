from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.dispatch import receiver
from django.db.models.signals import pre_save

class EncryptedUserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='encrypted_profile')
    encrypted_email = models.BinaryField(null=True, blank=True)
    encrypted_full_name = models.BinaryField(null=True, blank=True)
    encrypted_phone = models.BinaryField(null=True, blank=True)
    
    def __str__(self):
        return f"Encrypted profile for {self.user.username}"

# Signal to encrypt user data before saving
@receiver(pre_save, sender=User)
def encrypt_user_data(sender, instance, **kwargs):
    # Check if this is a new user or if password has been changed
    if instance.pk is None or sender.objects.filter(pk=instance.pk).exclude(password=instance.password).exists():
        # Hash the password if it's not already hashed
        if not instance.password.startswith('pbkdf2_sha256$'):
            instance.password = make_password(instance.password)

class SlideImage(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='slides/')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order']

class UserDataFile(models.Model):
    FILE_TYPES = (
        ('csv', 'CSV File'),
        ('excel', 'Excel File'),
        ('db', 'Database File'),
        ('mysql', 'MySQL Database'),
        ('postgres', 'PostgreSQL Database'),
        ('mssql', 'SQL Server Database'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_files')
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='user_data/', null=True, blank=True)  # Make file optional for remote DBs
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Remote database connection parameters
    db_host = models.CharField(max_length=255, blank=True, null=True)
    db_port = models.IntegerField(blank=True, null=True)
    db_name = models.CharField(max_length=100, blank=True, null=True)
    db_username = models.CharField(max_length=100, blank=True, null=True)
    db_password = models.CharField(max_length=100, blank=True, null=True)  # Should be encrypted
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Visualization(models.Model):
    VIZ_TYPES = (
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('scatter', 'Scatter Plot'),
        ('pie', 'Pie Chart'),
        ('histogram', 'Histogram'),
    )
    
    data_file = models.ForeignKey(UserDataFile, on_delete=models.CASCADE, related_name='visualizations')
    title = models.CharField(max_length=100)
    viz_type = models.CharField(max_length=20, choices=VIZ_TYPES)
    x_column = models.CharField(max_length=100)
    y_column = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='visualizations/', blank=True, null=True)
    source_table = models.CharField(max_length=100, blank=True, null=True, help_text="Source table name for database files")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_viz_type_display()}"
