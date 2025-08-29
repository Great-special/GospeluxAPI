from django.db import models
from core.models import BaseModel, Category, Tag

class BibleVersion(BaseModel):
    """Different Bible versions (KJV, NIV, ESV, etc.)"""
    bible_id = models.CharField(max_length=50, unique=True)  # API Bible ID
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10)
    language = models.CharField(max_length=50, default='English')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Book(BaseModel):
    """Books of the Bible"""
    book_id = models.CharField(max_length=10, unique=True)  # API Book ID
    bible_id = models.CharField(max_length=50, blank=True, null=True)  # To link with BibleVersion
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10)
    testament = models.CharField(max_length=20, choices=[
        ('OT', 'Old Testament'),
        ('NT', 'New Testament')
    ])
    book_number = models.PositiveIntegerField()
    total_chapters = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['book_number']
        unique_together = ['name', 'testament']
    
    def __str__(self):
        return self.name

class Chapter(BaseModel):
    """Chapters within each book"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.CharField(max_length=10)  # Changed to CharField to accommodate non-numeric chapters
    total_verses = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['book__book_number', 'chapter_number']
        unique_together = ['book', 'chapter_number']
    
    def __str__(self):
        return f"{self.book.name} {self.chapter_number}"

class Verse(BaseModel):
    """Individual Bible verses"""
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='verses')
    verse_number = models.CharField(max_length=10)
    text = models.TextField()
    version = models.ForeignKey(BibleVersion, on_delete=models.CASCADE, related_name='verses')
    
    class Meta:
        ordering = ['chapter__book__book_number', 'chapter__chapter_number', 'verse_number']
        unique_together = ['chapter', 'verse_number', 'version']
    
    def __str__(self):
        return f"{self.chapter.book.name} {self.chapter.chapter_number}:{self.verse_number}"
    
    @property
    def reference(self):
        return f"{self.chapter.book.name} {self.chapter.chapter_number}:{self.verse_number}"

class ReadingPlan(BaseModel):
    """Bible reading plans"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_days = models.PositiveIntegerField(help_text="Total days to complete the plan")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return self.title

class ReadingPlanDay(BaseModel):
    """Daily readings for a reading plan"""
    reading_plan = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE, related_name='daily_readings')
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True)
    verses = models.ManyToManyField(Verse, related_name='reading_plans')
    
    class Meta:
        ordering = ['reading_plan', 'day_number']
        unique_together = ['reading_plan', 'day_number']
    
    def __str__(self):
        return f"{self.reading_plan.title} - Day {self.day_number}"

class Bookmark(BaseModel):
    """User bookmarks for Bible verses"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='bookmarks')
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'verse']
    
    def __str__(self):
        return f"{self.user.email} - {self.verse.reference}"