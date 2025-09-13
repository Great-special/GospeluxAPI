# services/data_sync_service.py
from .api_bible import BibleAPI, config
from .models import BibleVersion, Book, Chapter, Verse
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

# Standard book ID mappings for common versions
STANDARD_BOOK_IDS = {
    'genesis': 'GEN', 'exodus': 'EXO', 'leviticus': 'LEV', 'numbers': 'NUM', 'deuteronomy': 'DEU',
    'joshua': 'JOS', 'judges': 'JDG', 'ruth': 'RUT', '1 samuel': '1SA', '2 samuel': '2SA',
    '1 kings': '1KI', '2 kings': '2KI', '1 chronicles': '1CH', '2 chronicles': '2CH',
    'ezra': 'EZR', 'nehemiah': 'NEH', 'esther': 'EST', 'job': 'JOB', 'psalms': 'PSA',
    'proverbs': 'PRO', 'ecclesiastes': 'ECC', 'song of solomon': 'SNG', 'isaiah': 'ISA',
    'jeremiah': 'JER', 'lamentations': 'LAM', 'ezekiel': 'EZK', 'daniel': 'DAN',
    'hosea': 'HOS', 'joel': 'JOL', 'amos': 'AMO', 'obadiah': 'OBA', 'jonah': 'JON',
    'micah': 'MIC', 'nahum': 'NAH', 'habakkuk': 'HAB', 'zephaniah': 'ZEP', 'haggai': 'HAG',
    'zechariah': 'ZEC', 'malachi': 'MAL', 'matthew': 'MAT', 'mark': 'MRK', 'luke': 'LUK',
    'john': 'JHN', 'acts': 'ACT', 'romans': 'ROM', '1 corinthians': '1CO', '2 corinthians': '2CO',
    'galatians': 'GAL', 'ephesians': 'EPH', 'philippians': 'PHP', 'colossians': 'COL',
    '1 thessalonians': '1TH', '2 thessalonians': '2TH', '1 timothy': '1TI', '2 timothy': '2TI',
    'titus': 'TIT', 'philemon': 'PHM', 'hebrews': 'HEB', 'james': 'JAS', '1 peter': '1PE',
    '2 peter': '2PE', '1 john': '1JN', '2 john': '2JN', '3 john': '3JN', 'jude': 'JUD',
    'revelation': 'REV'
}

# Version-specific book ID mappings
VERSION_SPECIFIC_MAPPINGS = {
    # Indonesian Bibles (like 5e51f89e89947acb-01)
    '5e51f89e89947acb-01': {
        'efesus': 'EPH', 'filipai': 'PHP', 'kolosi': 'COL', '1 tesalonika': '1TH',
        '2 tesalonika': '2TH', '1 timoti': '1TI', '2 timoti': '2TI', 'taitus': 'TIT',
        'filemon': 'PHM', 'hibru': 'HEB', 'jems': 'JAS', '1 pita': '1PE', '2 pita': '2PE',
        '1 jon': '1JN', '2 jon': '2JN', '3 jon': '3JN', 'jut': 'JUD'
    },
    
    # Greek Bibles (like 901dcd9744e1bf69-01)
    '901dcd9744e1bf69-01': {
        'κατα ματθαιον': 'MAT', 'κατα μαρκον': 'MRK', 'κατα λουκαν': 'LUK',
        'κατα ιωαννην': 'JHN', 'πραξεις': 'ACT', 'προς ρωμαιους': 'ROM',
        'προς κορινθιους α': '1CO', 'προς κορινθιους β': '2CO', 'προς γαλατας': 'GAL',
        'προς εφεσιους': 'EPH', 'προς φιλιππησιους': 'PHP', 'προς κολοσσαεις': 'COL',
        'προς θεσσαλονικεις α': '1TH', 'προς θεσσαλονικεις β': '2TH',
        'προς τιμοθεον α': '1TI', 'προς τιμοθεον β': '2TI', 'προς τιτον': 'TIT',
        'προς φιλημονα': 'PHM', 'προς εβραιους': 'HEB', 'ιακωβου': 'JAS',
        'πετρου α': '1PE', 'πετρου β': '2PE', 'ιωαννου α': '1JN', 'ιωαννου β': '2JN',
        'ιωαννου γ': '3JN', 'ιουδα': 'JUD', 'αποκαλυψις': 'REV'
    },
    
    # Hindi Bibles (like e051b4f945d52400-02)
    'e051b4f945d52400-02': {
        'मत्ती': 'MAT', 'मरकुस': 'MRK', 'लूका': 'LUK', 'यूहन्ना': 'JHN',
        'रोमियों': 'ROM', '1 कुरिन्थियों': '1CO', '2 कुरिन्थियों': '2CO',
        'गलातियों': 'GAL', 'इफिसियों': 'EPH', 'फिलिप्पियों': 'PHP',
        'कुलुस्सियों': 'COL', '1 थिस्सलुनीकियों': '1TH', '2 थिस्सलुनीकियों': '2TH',
        '1 तीमुथियुस': '1TI', '2 तीमुथियुस': '2TI', 'तीतुस': 'TIT', 'फिलेमोन': 'PHM',
        'इब्रानियों': 'HEB', 'याकूब': 'JAS', '1 पतरस': '1PE', '2 पतरस': '2PE',
        '1 यूहन्ना': '1JN', '2 यूहन्ना': '2JN', '3 यूहन्ना': '3JN', 'यहूदा': 'JUD',
        'प्रकाशितवाक्य': 'REV'
    },
    
    # Chinese Bible (04fb2bec0d582d1f-01)
    '04fb2bec0d582d1f-01': {
        # Old Testament
        '创世记': 'GEN', '出埃及记': 'EXO', '利未记': 'LEV', '民数记': 'NUM', '申命记': 'DEU',
        '约书亚记': 'JOS', '士师记': 'JDG', '路得记': 'RUT', '撒母耳记上': '1SA', '撒母耳记下': '2SA',
        '列王纪上': '1KI', '列王纪下': '2KI', '历代志上': '1CH', '历代志下': '2CH',
        '以斯拉记': 'EZR', '尼希米记': 'NEH', '以斯帖记': 'EST', '约伯记': 'JOB', '诗篇': 'PSA',
        '箴言': 'PRO', '传道书': 'ECC', '雅歌': 'SNG', '以赛亚书': 'ISA',
        '耶利米书': 'JER', '耶利米哀歌': 'LAM', '以西结书': 'EZK', '但以理书': 'DAN',
        '何西阿书': 'HOS', '约珥书': 'JOL', '阿摩司书': 'AMO', '俄巴底亚书': 'OBA', '约拿书': 'JON',
        '弥迦书': 'MIC', '那鸿书': 'NAH', '哈巴谷书': 'HAB', '西番雅书': 'ZEP', '哈该书': 'HAG',
        '撒迦利亚书': 'ZEC', '玛拉基书': 'MAL',
        
        # New Testament
        '马太福音': 'MAT', '马可福音': 'MRK', '路加福音': 'LUK', '约翰福音': 'JHN',
        '使徒行传': 'ACT', '罗马书': 'ROM', '哥林多前书': '1CO', '哥林多后书': '2CO',
        '加拉太书': 'GAL', '以弗所书': 'EPH', '腓立比书': 'PHP', '歌罗西书': 'COL',
        '帖撒罗尼迦前书': '1TH', '帖撒罗尼迦后书': '2TH', '提摩太前书': '1TI', '提摩太后书': '2TI',
        '提多书': 'TIT', '腓利门书': 'PHM', '希伯来书': 'HEB', '雅各书': 'JAS',
        '彼得前书': '1PE', '彼得后书': '2PE', '约翰一书': '1JN', '约翰二书': '2JN',
        '约翰三书': '3JN', '犹大书': 'JUD', '启示录': 'REV',
        
        # Apocrypha/Deuterocanonical books (common in some Chinese Bibles)
        '多俾亚传': 'TOB', '友弟德传': 'JDT', '艾斯德尔传': 'EST', '智慧篇': 'WIS',
        '德训篇': 'SIR', '巴路克': 'BAR', '玛加伯上': '1MA', '玛加伯下': '2MA',
        '达尼尔': 'DAN', '以斯得拉一书': '1ES', '以斯得拉二书': '2ES', '玛纳舍祷言': 'MAN',
        '诗篇一五一': 'PS2'
    },
}

sample_version = (
    "65eec8e0b60e656b-01", "de4e12af7f28f599-01", 
    "de4e12af7f28f599-02",  
    "6b7f504f1b6050c1-01", "48acedcf8595c754-01", 
    "482ddd53705278cc-01")
# "40072c4a5aba4022-01",

def get_book_id_for_version(bible_id, book_name):
    """
    Get the correct book ID for a specific Bible version.
    
    Args:
        bible_id: The API Bible ID
        book_name: The book name to look up
    
    Returns:
        The correct book ID for the API, or None if not found
    """
    book_name_lower = book_name.lower().strip()
    
    # First check version-specific mappings
    if bible_id in VERSION_SPECIFIC_MAPPINGS:
        for key, value in VERSION_SPECIFIC_MAPPINGS[bible_id].items():
            if key in book_name_lower or book_name_lower in key:
                return value
    
    # Then check standard mappings
    for key, value in STANDARD_BOOK_IDS.items():
        if key in book_name_lower or book_name_lower in key:
            return value
    
    # Try to extract from book ID if it follows standard pattern
    if hasattr(book_name, 'book_id') and book_name.book_id:
        return book_name.book_id
    
    return None

def is_intro_chapter(chapter_data):
    """Check if a chapter is an introduction chapter"""
    chapter_id = chapter_data.get('id', '').lower()
    chapter_number = str(chapter_data.get('number', ''))
    
    return ('intro' in chapter_id or 
            'intro' in chapter_number or
            chapter_number == '0' or
            chapter_number == '')


class DataSyncService:
    def __init__(self):
        self.bible_api = BibleAPI(config('bible_api_key'))
    
    def sync_bible_versions(self):
        """Sync Bible versions from API to local database"""
        qureyset = BibleVersion.objects.all()
        if qureyset.exists():
            return True, "Bible versions already synced"
        
        try:
            response = self.bible_api.get_bibles()
            bibles_data = response.get('data', [])
            
            for bible_data in bibles_data:
                bible_id = bible_data['id']
                if bible_id in sample_version:
                    defaults = {
                        'name': bible_data['name'],
                        'abbreviation': bible_data['abbreviation'],
                        'language': bible_data['language']['id'],
                        'description': bible_data.get('description', ''),
                        'is_active': True
                    }
                    
                    bible_version, created = BibleVersion.objects.update_or_create(
                        bible_id=bible_id,
                        defaults=defaults
                    )
                    
                    action = "Created" if created else "Updated"
                    logger.info(f"{action} Bible version: {bible_version.name}")
                
            return True, f"Synced {len(bibles_data)} Bible versions"
            
        except Exception as e:
            logger.error(f"Error syncing Bible versions: {e}")
            return False, str(e)
    
    def sync_books_for_version(self, bible_version):
        """Sync books for a specific Bible version"""
        queryset = Book.objects.filter(bible_id=bible_version.bible_id)
        if len(queryset) >= 66:
            return True, f"Books for {bible_version.name} already synced"
        
        try:
            response = self.bible_api.get_books(bible_version.bible_id)
            books_data = response.get('data', [])
            
            count = 0
            for book_data in books_data:
                book_id = book_data['id']
                defaults = {
                    'bible_id': bible_version.bible_id,
                    'name': book_data['name'],
                    'abbreviation': book_data['abbreviation'],
                    'testament': 'OT' if count < 40 else 'NT',
                    'book_number': count + 1,
                    'total_chapters': 0  # Will be updated when syncing chapters
                }
                
                book, created = Book.objects.update_or_create(
                    book_id=book_id,
                    defaults=defaults
                )
                
                action = "Created" if created else "Updated"
                logger.info(f"{action} book: {book.name}")
                count += 1
                
            return True, f"Synced {len(books_data)} books for {bible_version.name}"
            
        except Exception as e:
            logger.error(f"Error syncing books for {bible_version.name}: {e}")
            return False, str(e)
    
    def sync_chapters_for_book(self, book):
        """Sync chapters for a specific book"""
        try:
            bible_version = book.bible_id
            if bible_version in sample_version:
                book_id  = book.book_id
                if book_id is None:
                    return False, f"Could not determine book ID for {book.name} in version {bible_version}"
                response = self.bible_api.get_chapters(bible_version, book_id)
                chapters_data = response.get('data', [])
                print("---Chapters---")
                for chapter_data in chapters_data:
                    chapter_number = chapter_data["id"]
                    
                    defaults = {
                        'chapter_number': chapter_number,
                        'total_verses': 0  # Will be updated when syncing verses
                    }
                    
                    chapter, created = Chapter.objects.update_or_create(
                        book=book,
                        chapter_number=chapter_number,
                        defaults=defaults
                    )
                    
                    action = "Created" if created else "Updated"
                    logger.info(f"{action} chapter: {book.name} {chapter_number}")
                
                # Update total chapters count for the book
                book.total_chapters = len(chapters_data)
                book.save()
                
                return True, f"Synced {len(chapters_data)} chapters for {book.name}"
            else:
                return True, f"Skipping chapter sync for {book.name} due to sample version"
        except Exception as e:
            logger.error(f"Error syncing chapters for {book.name}: {e}")
            return False, str(e)
    
    def sync_verses_for_chapter(self, chapter):
        """Sync verses for a specific chapter"""
        try:
            bible_version = chapter.book.bible_id
            if bible_version in sample_version:
                chapter_ref = chapter.chapter_number
                response = self.bible_api.get_verses(bible_version, chapter_ref)
                verses_data = response.get('data', [])
                print("---Verses---")
                for verse_data in verses_data:
                    verse_id = verse_data['id']
                    verse_number = verse_id.split('.')[-1]
                    
                    # Get verse content
                    verse_content_response = self.bible_api.get_verse(
                        bible_version, 
                        verse_id,
                        content_type='text',
                        include_verse_numbers=False
                    )
                    
                    verse_content = verse_content_response.get('data', {}).get('content', '')
                    defaults = {
                        'verse_number': verse_number,
                        'text': verse_content,
                    }
                    
                    verse, created = Verse.objects.update_or_create(
                        chapter=chapter,
                        verse_number=verse_number,
                        version=BibleVersion.objects.get(bible_id=bible_version),
                        defaults=defaults
                    )
                    
                    action = "Created" if created else "Updated"
                    logger.info(f"{action} verse: {chapter.book.name} {chapter.chapter_number}:{verse_number}")
                
                # Update total verses count for the chapter
                chapter.total_verses = len(verses_data)
                chapter.save()
                
                return True, f"Synced {len(verses_data)} verses for {chapter.book.name} {chapter.chapter_number}"
            else:
                return True, f"Skipping verse sync for {chapter.book.name} {chapter.chapter_number} due to sample version"
        except Exception as e:
            logger.error(f"Error syncing verses for {chapter.book.name} {chapter.chapter_number}: {e}")
            return False, str(e)
    
    @transaction.atomic
    def full_sync(self, bible_version_id=None):
        """Perform a full sync of all data"""
        results = []
        
        # Sync Bible versions
        success, message = self.sync_bible_versions()
        results.append(message)
        if not success:
            return False, results
        
        # Get Bible versions to sync
        if bible_version_id:
            bible_versions = BibleVersion.objects.filter(id=bible_version_id, is_active=True)
        else:
            bible_versions = BibleVersion.objects.filter(is_active=True)
        
        print("Bible Versions to sync:", len(bible_versions))
        for bible_version in bible_versions:
            # Sync books for this version
            success, message = self.sync_books_for_version(bible_version)
            results.append(message)
            if not success:
                continue
            
        # Get all books for this version
        books = Book.objects.all()
        
        for book in books:
            print(type(book), book)
            # Sync chapters for this book
            success, message = self.sync_chapters_for_book(book)
            results.append(message)
            if not success:
                continue
            
        # Get all chapters for this book
        chapters = Chapter.objects.all()
        print("Chapters to sync:", len(chapters))
        for chapter in chapters:
            # Sync verses for this chapter
            success, message = self.sync_verses_for_chapter(chapter)
            results.append(message)
        
        return True, results
