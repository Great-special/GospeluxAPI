from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from .models import BibleVersion, Book, Chapter, Verse, ReadingPlan, ReadingPlanDay, Bookmark
from .serializers import (
    BibleVersionSerializer, BookSerializer, ChapterSerializer, VerseSerializer,
    VerseDetailSerializer, ReadingPlanSerializer, ReadingPlanDaySerializer, BookmarkSerializer
)
from .api_bible import BibleAPI
from decouple import config

bible_api = BibleAPI(config('bible_api_key', default=''))

class BibleVersionListView(generics.ListAPIView):
    queryset = BibleVersion.objects.filter(is_active=True)
    serializer_class = BibleVersionSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        # Try to get from local database first
        local_versions = super().list(request, *args, **kwargs)
        # If no local versions, try to fetch from API
        if not local_versions.data:
            language = request.query_params.get('language', 'eng')
            if language:
                try:
                    api_versions = bible_api.get_bibles(language=language)
                    # Return API response if local database is empty
                    return Response(api_versions)
                except Exception as e:
                    return Response(f'Error fetching version from API: {e}', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(local_versions)
        
class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]
    
    def list(self, request, *args, **kwargs):
        # Try to get from local database first
        local_books = super().list(request, *args, **kwargs)
        # If no local versions, try to fetch from API
        if not local_books.data:
            bible_id = request.query_params.get('bible_id', 'de4e12af7f28f599-02')
            if bible_id:
                try:
                    api_books = bible_api.get_books(bible_id)
                    # Return API response if local database is empty
                    return Response(api_books)
                except Exception as e:
                    return Response(f'Error fetching books from API: {e}', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(local_books)

class ChapterListView(generics.ListAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        book_id = self.kwargs.get('book_id')
        return Chapter.objects.filter(book_id=book_id)

    
    def list(self, request, *args, **kwargs):
        # Try to get from local database first
        local_chapters = super().list(request, *args, **kwargs)
        
        # If no local chapters, try to fetch from API
        if not local_chapters.data:
            book_id = self.kwargs.get('book_id')
            bible_id = request.query_params.get('bible_id')
            
            if bible_id and book_id:
                try:
                    api_chapters = bible_api.get_chapters(bible_id, book_id)
                    # Return API response if local database is empty
                    return Response(api_chapters)
                except Exception as e:
                    return Response(f"Error fetching chapters from API: {e}", status=status.HTTP_400_BAD_REQUEST)
        
        return local_chapters
    
class VerseListView(generics.ListAPIView):
    serializer_class = VerseDetailSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        chapter_id = self.kwargs.get('chapter_id')
        version_id = self.request.query_params.get('version')
        
        queryset = Verse.objects.filter(chapter_id=chapter_id)
        if version_id:
            queryset = queryset.filter(version_id=version_id)
        else:
            # Default to first available version
            first_version = BibleVersion.objects.filter(is_active=True).first()
            if first_version:
                queryset = queryset.filter(version=first_version)
        
        return queryset.select_related('chapter__book', 'version')

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_verses(request):
    """Search for verses by text content"""
    query = request.GET.get('q', '').strip()
    version_id = request.GET.get('version')
    
    if not query:
        return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    verses = Verse.objects.filter(text__icontains=query)
    
    if version_id:
        verses = verses.filter(version_id=version_id)
    
    verses = verses.select_related('chapter__book', 'version')[:50]  # Limit results
    
    serializer = VerseDetailSerializer(verses, many=True)
    return Response({
        'query': query,
        'results': serializer.data,
        'count': len(serializer.data)
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_verse_by_reference(request):
    """Get verse by reference (e.g., John 3:16)"""
    reference = request.GET.get('ref', '').strip()
    version_id = request.GET.get('version')
    
    if not reference:
        return Response({'error': 'Reference is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Parse reference (simplified parsing)
        parts = reference.split(' ')
        if len(parts) < 2:
            raise ValueError("Invalid reference format")
        
        book_name = ' '.join(parts[:-1])
        chapter_verse = parts[-1]
        
        if ':' not in chapter_verse:
            raise ValueError("Invalid reference format")
        
        chapter_num, verse_num = chapter_verse.split(':')
        chapter_num = int(chapter_num)
        verse_num = int(verse_num)
        
        # Find the book
        book = Book.objects.filter(
            Q(name__iexact=book_name) | Q(abbreviation__iexact=book_name)
        ).first()
        
        if not book:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Find the verse
        verse_query = Verse.objects.filter(
            chapter__book=book,
            chapter__chapter_number=chapter_num,
            verse_number=verse_num
        )
        
        if version_id:
            verse_query = verse_query.filter(version_id=version_id)
        
        verse = verse_query.select_related('chapter__book', 'version').first()
        
        if not verse:
            return Response({'error': 'Verse not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = VerseDetailSerializer(verse)
        return Response(serializer.data)
        
    except (ValueError, IndexError):
        return Response({'error': 'Invalid reference format'}, status=status.HTTP_400_BAD_REQUEST)

class ReadingPlanListView(generics.ListAPIView):
    queryset = ReadingPlan.objects.filter(is_active=True)
    serializer_class = ReadingPlanSerializer
    permission_classes = [permissions.AllowAny]

class ReadingPlanDetailView(generics.RetrieveAPIView):
    queryset = ReadingPlan.objects.filter(is_active=True)
    serializer_class = ReadingPlanSerializer
    permission_classes = [permissions.AllowAny]

class ReadingPlanDayView(generics.RetrieveAPIView):
    serializer_class = ReadingPlanDaySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_object(self):
        plan_id = self.kwargs.get('plan_id')
        day_number = self.kwargs.get('day_number')
        return ReadingPlanDay.objects.get(reading_plan_id=plan_id, day_number=day_number)

class BookmarkListCreateView(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('verse__chapter__book', 'verse__version')

class BookmarkDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)