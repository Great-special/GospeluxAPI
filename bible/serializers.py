from rest_framework import serializers
from .models import BibleVersion, Book, Chapter, Verse, ReadingPlan, ReadingPlanDay, Bookmark, Sermon

class BibleVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleVersion
        fields = ['id', 'name', 'abbreviation', 'language', 'description', 'is_active']

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'name', 'abbreviation', 'testament', 'book_number', 'total_chapters']

class ChapterSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    
    class Meta:
        model = Chapter
        fields = ['id', 'book', 'chapter_number', 'total_verses']

class VerseSerializer(serializers.ModelSerializer):
    chapter = ChapterSerializer(read_only=True)
    version = BibleVersionSerializer(read_only=True)
    reference = serializers.ReadOnlyField()
    
    class Meta:
        model = Verse
        fields = ['id', 'chapter', 'verse_number', 'text', 'version', 'reference']

class VerseDetailSerializer(serializers.ModelSerializer):
    book_name = serializers.CharField(source='chapter.book.name', read_only=True)
    chapter_number = serializers.IntegerField(source='chapter.chapter_number', read_only=True)
    version_name = serializers.CharField(source='version.abbreviation', read_only=True)
    reference = serializers.ReadOnlyField()
    
    class Meta:
        model = Verse
        fields = ['id', 'book_name', 'chapter_number', 'verse_number', 'text', 'version_name', 'reference']

class ReadingPlanSerializer(serializers.ModelSerializer):
    total_days = serializers.IntegerField(source='duration_days', read_only=True)
    
    class Meta:
        model = ReadingPlan
        fields = ['id', 'title', 'description', 'duration_days', 'total_days', 'category', 'is_active', 'created_at']

class ReadingPlanDaySerializer(serializers.ModelSerializer):
    verses = VerseDetailSerializer(many=True, read_only=True)
    verses_count = serializers.IntegerField(source='verses.count', read_only=True)
    
    class Meta:
        model = ReadingPlanDay
        fields = ['id', 'day_number', 'title', 'verses', 'verses_count']

class BookmarkSerializer(serializers.ModelSerializer):
    verse = VerseDetailSerializer(read_only=True)
    verse_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Bookmark
        fields = ['id', 'verse', 'verse_id', 'note', 'tags', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)



class SermonSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Sermon
        fields = [
            'id', 'title', 'bible_text', 'content',
            'author', 'author_name', 'generated_by_ai', 'created_at'
        ]
        read_only_fields = ['id', 'author_name', 'created_at']
