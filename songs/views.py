import json
import re
import requests
import logging
from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count
from django.db.models import Prefetch
from django.views.decorators.csrf import csrf_exempt
from core.generation_utility import generate_song, model_generator, generate_video, get_video_status
from core.heygen import HeyGenVideoCreator, select_voice_for_scene, select_avatar_for_scene
from .models import  Song, Playlist, PlaylistSong, Favorite, GeneratedSongs, GeneratedSongsData, GeneratedVideo
from .serializers import (
    SongSerializer, SongDetailSerializer,
    PlaylistSerializer, AddSongToPlaylistSerializer, FavoriteSerializer, 
    GeneratedSongsSerializer, GeneratedSongsDataSerializer,
    GeneratedVideoSerializer, VideoSerializer, VideoDetailSerializer
)
from decouple import config

logger = logging.getLogger(__name__)
client = HeyGenVideoCreator(config("HeyGen_API_KEY"))

# class ArtistListView(generics.ListAPIView):
#     queryset = Artist.objects.filter(is_active=True).annotate(songs_count=Count('songs'))
#     serializer_class = ArtistSerializer
#     permission_classes = [permissions.AllowAny]

# class ArtistDetailView(generics.RetrieveAPIView):
#     queryset = Artist.objects.filter(is_active=True)
#     serializer_class = ArtistSerializer
#     permission_classes = [permissions.AllowAny]

# class AlbumListView(generics.ListAPIView):
#     serializer_class = AlbumSerializer
#     permission_classes = [permissions.AllowAny]
    
#     def get_queryset(self):
#         queryset = Album.objects.select_related('artist').annotate(songs_count=Count('songs'))
#         artist_id = self.request.query_params.get('artist')
#         if artist_id:
#             queryset = queryset.filter(artist_id=artist_id)
#         return queryset

# class AlbumDetailView(generics.RetrieveAPIView):
#     queryset = Album.objects.select_related('artist')
#     serializer_class = AlbumSerializer
#     permission_classes = [permissions.AllowAny]

class SongListView(generics.ListAPIView):
    serializer_class = SongSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # queryset = Song.objects.filter(is_active=True).select_related('artist', 'album', 'category')
        queryset = Song.objects.filter(is_active=True).select_related('category')
        
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
    # queryset = Song.objects.filter(is_active=True).select_related('artist', 'album', 'category')
    queryset = Song.objects.filter(is_active=True).select_related('category')
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
        Q(artist__icontains=query) |
        Q(lyrics__icontains=query) |
        Q(album__icontains=query)
    ).filter(is_active=True).select_related('category').distinct()[:50]
    # songs = Song.objects.filter(
    #     Q(title__icontains=query) |
    #     Q(artist__name__icontains=query) |
    #     Q(lyrics__icontains=query) |
    #     Q(album__title__icontains=query)
    # ).filter(is_active=True).select_related('artist', 'album', 'category').distinct()[:50]
    
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
        ).select_related('user').prefetch_related(
            Prefetch(
                'playlistsong_set',
                queryset=PlaylistSong.objects.select_related('song')
            )
        )
        
    def perform_create(self, serializer):
        # Automatically attach the logged-in user
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)

class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Playlist.objects.filter(
            Q(user=user) | Q(is_public=True)
        ).select_related('user').prefetch_related(
            Prefetch(
                'playlistsong_set',
                queryset=PlaylistSong.objects.select_related('song')
            )
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_song_to_playlist(request, playlist_id):
    """Add a song to a playlist"""
    from django.db import models
    try:
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)
    except Playlist.DoesNotExist:
        return Response({'error': 'Playlist not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AddSongToPlaylistSerializer(data=request.data)
    if serializer.is_valid():
        song_id = serializer.validated_data['song']
        order = serializer.validated_data.get('order')
        try:
            song = Song.objects.get(id=song_id.id, is_active=True)
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

# class SongRequestListCreateView(generics.ListCreateAPIView):
#     serializer_class = SongRequestSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         return SongRequest.objects.filter(user=self.request.user)

# class SongRequestDetailView(generics.RetrieveUpdateAPIView):
#     serializer_class = SongRequestSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         return SongRequest.objects.filter(user=self.request.user)

class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('song')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)

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

class FavoriteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

class GeneratedSongsListView(generics.ListAPIView):
    serializer_class = GeneratedSongsDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        generated_song = GeneratedSongs.objects.filter(user=self.request.user).first()
        return GeneratedSongsData.objects.filter(generated_song=generated_song).order_by('-created_at')

class GeneratedSongsDetailView(generics.RetrieveAPIView):
    serializer_class = GeneratedSongsDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        generated_song = GeneratedSongs.objects.filter(user=self.request.user).first()
        return GeneratedSongsData.objects.filter(generated_song=generated_song).order_by('-created_at')


class GeneratedSongsCreateView(generics.CreateAPIView):
    serializer_class = GeneratedSongsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        title = request.data.get('title', None)
        lyrics = request.data.get('lyrics', '')
        bible_verse = request.data.get('bible_verse', '')
        genre = request.data.get('genre', 'gospel')
        mood = request.data.get('mood', 'uplifting')

        try:
            # Call external music generation utility
            prompt = f"Generate a short song title for: {bible_verse}"
            if title is None:
                res = model_generator(prompt)
                # Split by number followed by a dot and space
                parts = re.findall(r'"(.*?)"', res)
                if len(parts) >= 2:
                    title = parts[1]
                else:
                    title = parts[0]
            response = generate_song(title=title, bible_verse=bible_verse, genre=genre, mood=mood)
            if response.get('code') != 200:
                raise Exception(f"[SUNO] Music generation failed with code {response.get('code')}: {response.get('msg')}")
          
            task_id = response.get('data').get('taskId')
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Pass user and other fields into serializer.save()
            serializer.save(
                user=request.user,
                title=title,
                status='processing',
                task_id=task_id
            )

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            logger.error(f"Error generating song: {e}")
            return Response(
                {'error': f'Failed to initiate music generation {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def update_generated_song_status(task_id, status, data_id=None, duration=None, prompt=None, audio_file_url=None, audio_file=None):
    try:
        generated_song = GeneratedSongs.objects.get(task_id=task_id)
        generated_song.status = status

        if prompt:
            generated_song.lyrics = prompt

        generated_song.save()

        # store audio metadata only if available
        if audio_file_url:
            GeneratedSongsData.objects.create(
                generated_song=generated_song,
                data_id=data_id,
                duration=duration,
                audio_file_url=audio_file_url,
                audio_file=audio_file
            )

        logger.info(f"Updated song {task_id} → status={status}")

    except GeneratedSongs.DoesNotExist:
        logger.error(f"GeneratedSongs with task_id {task_id} does not exist")


@csrf_exempt
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def handle_callback(request):
    try:
        data = request.data

        code = data.get("code")
        msg = data.get("msg", "")
        try:
            callback_data = data.get("data")
        except Exception:
            callback_data = {}

        # Normalize task id
        task_id = callback_data.get("task_id")
        callback_type = callback_data.get("callbackType")
        try:
            tracks = callback_data.get("data")
        except Exception:
            tracks = [] 

        logger.info(f"[SUNO CALLBACK] task={task_id}, code={code}, type={callback_type}, msg={msg}")

        if not task_id:
            logger.error("Callback missing taskId")
            return Response({"error": "taskId missing"}, status=400)

        # ---- SUCCESS -------------------------------------------------------
        if code == 200:
            logger.info(f"Suno task {task_id} completed. Tracks: {len(tracks)}")

            for index, track in enumerate(tracks, start=1):
                data_id = track.get("id")
                title = track.get("title") or f"Track {index}"
                duration = track.get("duration")
                audio_url = track.get("audio_url")

                logger.info(f"Track {index}: title={title}, duration={duration}, audio={audio_url}")

                if audio_url:
                    try:
                        # Download the audio file
                        resp = requests.get(audio_url, timeout=30)
                        resp.raise_for_status()

                        # Sanitize filename
                        safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', "", title)
                        filename = f"suno_{task_id}_{safe_title}_{index}.mp3"

                        with open(filename, "wb") as f:
                            f.write(resp.content)

                        logger.info(f"Audio saved: {filename}")

                        # Update DB
                        update_generated_song_status(
                            task_id=task_id,
                            status="completed",
                            data_id=data_id,
                            duration=duration,
                            audio_file_url=audio_url,
                        )

                    except Exception as e:
                        logger.error(f"Audio download failed for task {task_id}: {str(e)}")

        # ---- FAILURE -------------------------------------------------------
        else:
            logger.warning(f"Suno generation failed: code={code}, msg={msg}")
            update_generated_song_status(task_id, status="failed")

        return Response({"message": "Callback processed successfully"})

    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}", exc_info=True)
        return Response({"error": "Internal server error"}, status=500)



class GeneratedVideoCreateView(generics.CreateAPIView):
    serializer_class = GeneratedVideoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        title = request.data.get('title', None)
        bible_verse = request.data.get('bible_verse', '')
        video_style = request.data.get('video_style', 'inspirational')
        length = request.data.get('video_length', '3')
        if length.isdigit():
            length = int(length) * 60
            length_seconds = min(length, 180)
        try:
            # Call external music generation utility
            prompt = f"Generate a short song title for: {bible_verse}"
            if title is None:
                res = model_generator(prompt)
                # Split by number followed by a dot and space
                parts = re.findall(r'"(.*?)"', res)
                if len(parts) >= 2:
                    title = parts[1]
                else:
                    title = parts[0]
            #------------------ here will be removed in favour of the heygen sdk-------------
            # response = generate_video(verse=bible_verse, video_style=video_style)
            # print(f"From view {response}")
            # if response.get('code') != 200:
            #     raise Exception(f"Video generation failed with code {response.get('code')}: {response.get('msg')}")
            
            # -------------- Here is the heygen  sdk use case ---------------------
            # prompt = f"""You are a professional video scriptwriter. 
            #     Create a {length_seconds}-second {video_style} video script based on the following topic: {verse}. 
            #     Ensure the script is engaging, concise, and suitable for a short video format."""
            # video_scripts = model_generator(prompt, max_tokens=500)
            
            script_prompt = """
                You are a professional scriptwriter for inspirational Bible-based videos.

                Write a multi-scene script for the topic: "{}"
                Video style: {}
                Duration: {} seconds.

                Use ONLY these speaker types:
                - "presenter"
                - "male"
                - "female"
                - "god"
                - "angel"

                Return ONLY valid JSON with this structure:

                {{
                "scenes": [
                    {{
                    "speaker_type": "presenter | male | female | god | angel",
                    "text": "What this speaker says in the scene."
                    }}
                ]
                }}

                Rules:
                - Use 4–8 scenes.
                - 1–2 sentences per scene.
                - Speaker type MUST be one of the allowed values.
                - DO NOT include explanations or commentary — only JSON.
            """.format(bible_verse, video_style, length_seconds)


            script_raw = model_generator(script_prompt, max_tokens=500)
            
            try:
                script = json.loads(script_raw.strip())
                scenes = script["scenes"]
            except Exception as e:
                raise Exception(f"Generated script is not valid JSON: {e}")
            
            voices = client.get_voices_list()
            avatars = client.get_avatars_list()
            for scene in scenes:
                speaker_type = scene.get("speaker_type", "presenter")

                scene["voice_id"] = select_voice_for_scene(speaker_type, voices)
                scene["avatar_id"] = select_avatar_for_scene(speaker_type, avatars)
                
                if "background_color" not in scene:
                    scene["background_color"] = "#FCDCBE"

            response = client.create_multi_scene_video(
                title=title,
                scenes=scenes)

            video_id = response.get('data').get('video_id')
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Pass user and other fields into serializer.save()
            serializer.save(
                user=request.user,
                title=title,
                status='processing',
                video_id=video_id
            )

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return Response(
                {'error': f'Failed to initiate video generation {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GeneratedVideosListView(generics.ListAPIView):
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GeneratedVideo.objects.filter(user=self.request.user).order_by('-created_at')


class GeneratedVideoDetailView(generics.RetrieveAPIView):
    serializer_class = VideoDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GeneratedVideo.objects.filter(user=self.request.user).order_by('-created_at')



@api_view(['GET'])
def get_video_status_view(request):
    try:
        video_id = request.GET.get('video_id')
        if not video_id:
            return Response({'error': 'video_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        video_status = client.get_video_status(video_id)
        return Response(video_status, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error fetching video status: {e}")
        return Response(
            {'error': 'Failed to fetch video status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )