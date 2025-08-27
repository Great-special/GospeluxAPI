from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Artist, Album, Song, Playlist, PlaylistSong, SongRequest, Favorite
from .serializers import (
    ArtistSerializer, AlbumSerializer, SongSerializer, SongDetailSerializer,
    PlaylistSerializer, AddSongToPlaylistSerializer, SongRequestSerializer, FavoriteSerializer
)

class ArtistListView(generics.ListAPIView):
    queryset = Artist.objects.filter(is_active=True).annotate(songs_count=Count('songs'))
    serializer_class = ArtistSerializer
    permission_classes = [permissions.AllowAny]

class ArtistDetailView(generics.RetrieveAPIView):
    queryset = Artist.objects.filter(is_active=True)
    serializer_class = ArtistSerializer
    permission_classes = [permissions.AllowAny]

class AlbumListView(generics.ListAPIView):
    serializer_class = AlbumSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Album.objects.select_related('artist').annotate(songs_count=Count('songs'))
        artist_id = self.request.query_params.get('artist')
        if artist_id:
            queryset = queryset.filter(artist_id=artist_id)
        return queryset

class AlbumDetailView(generics.RetrieveAPIView):
    queryset = Album.objects.select_related('artist')
    serializer_class = AlbumSerializer
    permission_classes = [permissions.AllowAny]

class SongListView(generics.ListAPIView):
    serializer_class = SongSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Song.objects.filter(is_active=True).select_related('artist', 'album', 'category')
        
        # Filter by artist
        artist_id = self.request.query_params.get('artist')
        if artist_id:
            queryset = queryset.filter(artist_id=artist_id)
        
        # Filter by album
        album_id = self.request.query_params.get('album')
        if album_id:
            queryset = queryset.filter(album_id=album_id)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by key
        key = self.request.query_params.get('key')
        if key:
            queryset = queryset.filter(key_signature__iexact=key)
        
        return queryset

class SongDetailView(generics.RetrieveAPIView):
    queryset = Song.objects.filter(is_active=True).select_related('artist', 'album', 'category')
    serializer_class = SongDetailSerializer
    permission_classes = [permissions.AllowAny]

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_songs(request):
    """Search for songs by title, artist, or lyrics"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    songs = Song.objects.filter(
        Q(title__icontains=query) |
        Q(artist__name__icontains=query) |
        Q(lyrics__icontains=query) |
        Q(album__title__icontains=query)
    ).filter(is_active=True).select_related('artist', 'album', 'category').distinct()[:50]
    
    serializer = SongSerializer(songs, many=True, context={'request': request})
    return Response({
        'query': query,
        'results': serializer.data,
        'count': len(serializer.data)
    })

class PlaylistListCreateView(generics.ListCreateAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Show user's own playlists and public playlists
        return Playlist.objects.filter(
            Q(user=user) | Q(is_public=True)
        ).select_related('user').prefetch_related('playlistsong_set__song__artist')

class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Playlist.objects.filter(
            Q(user=user) | Q(is_public=True)
        ).select_related('user').prefetch_related('playlistsong_set__song__artist')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_song_to_playlist(request, playlist_id):
    """Add a song to a playlist"""
    try:
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)
    except Playlist.DoesNotExist:
        return Response({'error': 'Playlist not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AddSongToPlaylistSerializer(data=request.data)
    if serializer.is_valid():
        song_id = serializer.validated_data['song_id']
        order = serializer.validated_data.get('order')
        
        try:
            song = Song.objects.get(id=song_id, is_active=True)
        except Song.DoesNotExist:
            return Response({'error': 'Song not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if song is already in playlist
        if PlaylistSong.objects.filter(playlist=playlist, song=song).exists():
            return Response({'error': 'Song already in playlist'}, status=status.HTTP_400_BAD_REQUEST)
        
        # If no order specified, add to end
        if order is None:
            max_order = PlaylistSong.objects.filter(playlist=playlist).aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            order = max_order + 1
        
        PlaylistSong.objects.create(playlist=playlist, song=song, order=order)
        
        return Response({'message': 'Song added to playlist successfully'}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_song_from_playlist(request, playlist_id, song_id):
    """Remove a song from a playlist"""
    try:
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)
        playlist_song = PlaylistSong.objects.get(playlist=playlist, song_id=song_id)
        playlist_song.delete()
        return Response({'message': 'Song removed from playlist'}, status=status.HTTP_200_OK)
    except (Playlist.DoesNotExist, PlaylistSong.DoesNotExist):
        return Response({'error': 'Playlist or song not found'}, status=status.HTTP_404_NOT_FOUND)

class SongRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = SongRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SongRequest.objects.filter(user=self.request.user)

class SongRequestDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SongRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SongRequest.objects.filter(user=self.request.user)

class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('song__artist', 'song__album')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_favorite(request, song_id):
    """Toggle favorite status for a song"""
    try:
        song = Song.objects.get(id=song_id, is_active=True)
    except Song.DoesNotExist:
        return Response({'error': 'Song not found'}, status=status.HTTP_404_NOT_FOUND)
    
    favorite, created = Favorite.objects.get_or_create(user=request.user, song=song)
    
    if not created:
        favorite.delete()
        return Response({'message': 'Song removed from favorites', 'is_favorited': False})
    else:
        return Response({'message': 'Song added to favorites', 'is_favorited': True})

class FavoriteDetailView(generics.DestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)