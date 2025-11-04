from django.urls import path
from . import views


urlpatterns = [
    path('version/', views.BibleVersionListView.as_view(), name='bible-version-list'),
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/<int:book_id>/chapters/', views.ChapterListView.as_view(), name='chapter-list'),
    path('chapters/<int:chapter_id>/verses/', views.VerseListView.as_view(), name='verse-list'),
    path('search/', views.search_verses, name='search-verses'),
    path('plans/', views.ReadingPlanListView.as_view(), name='reading-plan-list'),
    path('plans/<int:pk>/', views.ReadingPlanDetailView.as_view(), name='reading-plan-detail'),
    path('sermons/', views.SermonListCreateView.as_view(), name='sermon-list-create'),
    
]