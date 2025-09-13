from django.urls import path
from . import views

urlpatterns = [
    # path('artists/', views.ArtistListView.as_view(), name='artists'),
    # path('artists/<uuid:pk>/', views.ArtistDetailView.as_view(), name='artist_detail'),
    # path('albums/', views.AlbumListView.as_view(), name='albums'),
    # path('albums/<uuid:pk>/', views.AlbumDetailView.as_view(), name='album_detail'),
    path('songs/', views.SongListView.as_view(), name='songs'),
    path('songs/<uuid:pk>/', views.SongDetailView.as_view(), name='song_detail'),
    path('search/', views.search_songs, name='search_songs'),
    path('playlists/', views.PlaylistListCreateView.as_view(), name='playlists'),
    path('playlists/<uuid:pk>/', views.PlaylistDetailView.as_view(), name='playlist_detail'),
    path('playlists/<uuid:playlist_id>/add-song/', views.add_song_to_playlist, name='add_song_to_playlist'),
    path('playlists/<uuid:playlist_id>/remove-song/<uuid:song_id>/', views.remove_song_from_playlist, name='remove_song_from_playlist'),
    # path('requests/', views.SongRequestListCreateView.as_view(), name='song_requests'),
    # path('requests/<uuid:pk>/', views.SongRequestDetailView.as_view(), name='song_request_detail'),
    path('favorites/', views.FavoriteListCreateView.as_view(), name='favorites'),
    path('favorites/<uuid:pk>/', views.FavoriteDetailView.as_view(), name='favorite_detail'),
    path('songs/<uuid:song_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('generate-music-callback/', views.handle_callback, name='generate_music_callback'),
]