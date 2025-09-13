from django.db import models
import uuid

class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Category(BaseModel):
    """Generic category model for organizing content"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Tag(BaseModel):
    """Generic tag model for labeling content"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserFeedBack(BaseModel):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    organization = models.CharField(max_length=150, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()


class ApplicationAPK(BaseModel):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)
    type = models.CharField(max_length=50, choices=[
        ('ios', 'iOS'),
        ('android', 'Android')
    ])
    file = models.FileField(upload_to='apk_files/')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.version}"


class NewsLetterSubscriber(BaseModel):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email