from django.contrib import admin

# Register your models here.
from .models import  Song, Playlist, PlaylistSong, Favorite, GeneratedSongs, GeneratedSongsData, Video, GeneratedVideo

# @admin.register(Artist)
# class ArtistAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_active', 'songs_count', 'created_at')
#     list_filter = ('is_active', 'created_at')
#     search_fields = ('name', 'biography')
#     ordering = ('name',)
    
#     def songs_count(self, obj):
#         return obj.songs.count()
#     songs_count.short_description = 'Songs Count'

# @admin.register(Album)
# class AlbumAdmin(admin.ModelAdmin):
#     list_display = ('title', 'artist', 'release_date', 'category', 'songs_count')
#     list_filter = ('release_date', 'category', 'artist')
#     search_fields = ('title', 'artist__name')
#     ordering = ('-release_date', 'title')
    
#     def songs_count(self, obj):
#         return obj.songs.count()
#     songs_count.short_description = 'Songs Count'

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'album', 'key_signature', 'bpm', 'category', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'key_signature', 'artist', 'created_at')
    search_fields = ('title', 'artist__name', 'lyrics')
    filter_horizontal = ('tags',)
    ordering = ('title',)

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'songs_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'user__email', 'description')
    ordering = ('-created_at',)
    
    def songs_count(self, obj):
        return obj.songs.count()
    
    
@admin.register(PlaylistSong)
class PlaylistSongAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'song', 'order', 'created_at')
    list_filter = ('playlist', 'created_at')
    search_fields = ('playlist__name', 'song__title')
    ordering = ('playlist', 'order')

# @admin.register(SongRequest)
# class SongRequestAdmin(admin.ModelAdmin):
#     list_display = ('title', 'artist_name', 'user', 'status', 'created_at')
#     list_filter = ('status', 'created_at')
#     search_fields = ('title', 'artist_name', 'user__email')
#     ordering = ('-created_at',)
    
#     fieldsets = (
#         (None, {'fields': ('title', 'artist_name', 'user', 'notes')}),
#         ('Admin', {'fields': ('status', 'admin_notes')}),
#     )

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'created_at')
    list_filter = ('created_at', 'song__artist')
    search_fields = ('user__email', 'song__title', 'song__artist__name')
    ordering = ('-created_at',)


@admin.register(GeneratedSongs)
class GeneratedSongsAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'user__email')
    ordering = ('-created_at',)
    
@admin.register(GeneratedSongsData)
class GeneratedSongsDataAdmin(admin.ModelAdmin):
    list_display = ('generated_song', 'duration', 'created_at')
    list_filter = ('data_id', 'duration', 'created_at')
    search_fields = ('generated_song__title', 'generated_song__user__email')
    ordering = ('-created_at',)    

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_file', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'song__title')
    ordering = ('-created_at',)

@admin.register(GeneratedVideo)
class GeneratedVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'user__email')
    ordering = ('-created_at',)