from rest_framework import serializers
from .models import Song, Playlist, PlaylistSong, Favorite, Video, GeneratedSongs, GeneratedSongsData, GeneratedVideo

# class ArtistSerializer(serializers.ModelSerializer):
#     songs_count = serializers.IntegerField(source='songs.count', read_only=True)

#     class Meta:
#         model = Artist
#         fields = ['id', 'name', 'biography', 'is_active', 'created_at', 'songs_count']
#         read_only_fields = ['created_at']
    
# class AlbumSerializer(serializers.ModelSerializer):
#     songs_count = serializers.IntegerField(source='songs.count', read_only=True)

#     class Meta:
#         model = Album
#         fields = ['id', 'title', 'artist', 'release_date', 'category', 'songs_count']
#         read_only_fields = ['created_at']

class SongSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True)

    class Meta:
        model = Song
        fields = ['id', 'title', 'artist', 'artist_name', 'album', 'album_title', 'key_signature', 'bpm', 'category', 'is_active']
        read_only_fields = ['created_at']

class SongDetailSerializer(SongSerializer):
    lyrics = serializers.CharField()
    duration = serializers.DurationField()
    audio_file = serializers.FileField(required=False)
    sheet_music = serializers.FileField(required=False)
    tags = serializers.StringRelatedField(many=True)

    class Meta(SongSerializer.Meta):
        fields = SongSerializer.Meta.fields + ['lyrics', 'duration', 'audio_file', 'sheet_music', 'tags']


class PlaylistSerializer(serializers.ModelSerializer):
    songs_count = serializers.IntegerField(source='songs.count', read_only=True)

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'user', 'is_public', 'songs_count']
        read_only_fields = ['created_at', 'user']


class AddSongToPlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistSong
        fields = ['song', 'order']
        read_only_fields = ['created_at', 'playlist']

# class SongRequestSerializer(serializers.ModelSerializer):
#     user_email = serializers.EmailField(source='user.email', read_only=True)

#     class Meta:
#         model = SongRequest
#         fields = ['id', 'title', 'artist_name', 'user', 'user_email', 'status', 'created_at']
#         read_only_fields = ['created_at']

class FavoriteSerializer(serializers.ModelSerializer):
    song_title = serializers.CharField(source='song.title', read_only=True)
    artist_name = serializers.CharField(source='song.artist', read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'song', 'song_title', 'artist_name', 'created_at']
        read_only_fields = ['created_at', 'user']


class GeneratedSongsSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = GeneratedSongs
        fields = ["id", 'task_id', 'status', "user", "bible_verse", "title", "genre", "created_at", "user_email"]
        read_only_fields = ['created_at', 'user', 'title', 'task_id', 'status']


class GeneratedSongsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedSongsData
        fields = "__all__"
        read_only_fields = ['created_at']
        

class GeneratedVideoSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = GeneratedVideo
        fields = ["id", "user", "bible_verse", "title", "video_id", "created_at", "user_email"]
        read_only_fields = ['created_at', 'user', 'title']


class GeneratedVideoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedVideo
        fields = "__all__"

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'title', 'category', 'is_active']
        read_only_fields = ['created_at']

class VideoDetailSerializer(VideoSerializer):
    video_file = serializers.FileField(required=False)
    tags = serializers.StringRelatedField(many=True)

    class Meta(VideoSerializer.Meta):
        fields = VideoSerializer.Meta.fields + ['video_file', 'tags']
