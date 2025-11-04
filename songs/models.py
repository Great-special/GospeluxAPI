from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
from core.models import BaseModel, Category, Tag

User = get_user_model()

# class Artist(BaseModel):
#     """Song artists/performers"""
#     name = models.CharField(max_length=200)
#     biography = models.TextField(blank=True)
#     image = models.ImageField(upload_to='artists/', blank=True, null=True)
#     website = models.URLField(blank=True)
#     is_active = models.BooleanField(default=True)
    
#     class Meta:
#         ordering = ['name']
    
#     def __str__(self):
#         return self.name

# class Album(BaseModel):
#     """Song albums"""
#     title = models.CharField(max_length=200)
#     artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
#     description = models.TextField(blank=True)
#     cover_image = models.ImageField(upload_to='albums/', blank=True, null=True)
#     release_date = models.DateField(blank=True, null=True)
#     category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
#     class Meta:
#         ordering = ['-release_date', 'title']
    
#     def __str__(self):
#         return f"{self.title} - {self.artist.name}"

class Song(BaseModel):
    """Individual songs"""
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200, null=True)  # Changed to CharField for simplicity
    album = models.CharField(max_length=200, blank=True, null=True)
    lyrics = models.TextField(null=True)
    duration = models.DurationField(blank=True, null=True)
    audio_file = models.FileField(upload_to='songs/audio/', blank=True, null=True)
    sheet_music = models.FileField(upload_to='songs/sheets/', blank=True, null=True)
    key_signature = models.CharField(max_length=10, blank=True, help_text="e.g., C, G, Am, etc.")
    bpm = models.PositiveIntegerField(blank=True, null=True, help_text="Beats per minute")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} - {self.artist}"

class Playlist(BaseModel):
    """User-created playlists"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    songs = models.ManyToManyField(Song, through='PlaylistSong', related_name='playlists')
    is_public = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='playlists/', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.get_full_name() or self.user.username}"
    
    @property
    def songs_count(self):
        return self.songs.count()

class PlaylistSong(BaseModel):
    """Through model for playlist songs with ordering"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['playlist', 'song']

# class SongRequest(BaseModel):
#     """User requests for new songs"""
#     title = models.CharField(max_length=200)
#     artist_name = models.CharField(max_length=200)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='song_requests')
#     notes = models.TextField(blank=True)
#     status = models.CharField(max_length=20, choices=[
#         ('pending', 'Pending'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#         ('completed', 'Completed')
#     ], default='pending')
#     admin_notes = models.TextField(blank=True)
    
#     class Meta:
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"{self.title} by {self.artist_name} - {self.user.get_full_name() or self.user.username}"

class Favorite(BaseModel):
    """User favorite songs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='favorited_by')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'song']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.song.title}"
    

class GeneratedSongs(BaseModel):
    """Songs generated using AI"""
    bible_verse = models.TextField()
    title = models.CharField(max_length=200)
    lyrics = models.TextField()
    genre = models.CharField(max_length=100)
    mood = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=(
        ('processing', 'Processing'), 
        ('completed', 'Completed'), 
        ('failed', 'Failed')), default='processing')
    task_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_songs')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Generated: {self.title} - {self.user.get_full_name() or self.user.username}"
    


class GeneratedSongsData(BaseModel):
    """Data related to generated songs, e.g., audio file URLs"""
    generated_song = models.ForeignKey(GeneratedSongs, on_delete=models.CASCADE, related_name='data')
    audio_file_url = models.URLField()
    audio_file = models.FileField(upload_to='generated_songs/audio/', blank=True, null=True)
    data_id = models.CharField(max_length=100, blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Data for {self.generated_song.title} - {self.generated_song.user.get_full_name() or self.generated_song.user.username}"
