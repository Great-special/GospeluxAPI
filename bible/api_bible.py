import requests
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from decouple import config
import json

@dataclass
class BibleAPIConfig:
    base_url: str = "https://api.scripture.api.bible"
    api_version: str = "v1"
    
class BibleAPI:
    def __init__(self, api_key: str):
        self.config = BibleAPIConfig()
        self.api_key = api_key
        self.headers = {
            'api-key': api_key,
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _build_url(self, endpoint: str) -> str:
        """Build complete API URL from endpoint"""
        return f"{self.config.base_url}/{self.config.api_version}/{endpoint}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Generic request method"""
        url = self._build_url(endpoint)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    # Bibles Endpoints
    def get_bibles(self, language: Optional[str] = None, 
                  abbreviation: Optional[str] = None,
                  name: Optional[str] = None,
                  ids: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of Bibles
        
        Args:
            language: Filter by language code (e.g., 'eng')
            abbreviation: Filter by abbreviation (e.g., 'KJV')
            name: Filter by name
            ids: Comma separated list of Bible IDs to filter by
        """
        params = {}
        if language:
            params['language'] = language
        if abbreviation:
            params['abbreviation'] = abbreviation
        if name:
            params['name'] = name
        if ids:
            params['ids'] = ids
            
        return self._make_request('GET', 'bibles', params=params)
    
    def get_bible(self, bible_id: str) -> Dict[str, Any]:
        """
        Get specific Bible by ID
        
        Args:
            bible_id: The ID of the Bible to retrieve
        """
        return self._make_request('GET', f'bibles/{bible_id}')
    
    # Books Endpoints
    def get_books(self, bible_id: str, include_chapters: Optional[bool] = None,
                 include_chapters_and_sections: Optional[bool] = None) -> Dict[str, Any]:
        """
        Get books for a specific Bible
        
        Args:
            bible_id: The ID of the Bible
            include_chapters: Include chapters in the response
            include_chapters_and_sections: Include chapters and sections in the response
        """
        params = {}
        if include_chapters is not None:
            params['include-chapters'] = str(include_chapters).lower()
        if include_chapters_and_sections is not None:
            params['include-chapters-and-sections'] = str(include_chapters_and_sections).lower()
            
        return self._make_request('GET', f'bibles/{bible_id}/books', params=params)
    
    def get_book(self, bible_id: str, book_id: str, 
                include_chapters: Optional[bool] = None) -> Dict[str, Any]:
        """
        Get specific book by ID
        
        Args:
            bible_id: The ID of the Bible
            book_id: The ID of the book
            include_chapters: Include chapters in the response
        """
        params = {}
        if include_chapters is not None:
            params['include-chapters'] = str(include_chapters).lower()
            
        return self._make_request('GET', f'bibles/{bible_id}/books/{book_id}', params=params)
    
    # Chapters Endpoints
    def get_chapters(self, bible_id: str, book_id: str) -> Dict[str, Any]:
        """
        Get chapters for a specific book
        
        Args:
            bible_id: The ID of the Bible
            book_id: The ID of the book
        """
        return self._make_request('GET', f'bibles/{bible_id}/books/{book_id}/chapters')
    
    def get_chapter(self, bible_id: str, chapter_id: str, 
                   content_type: Optional[str] = None,
                   include_notes: Optional[bool] = None,
                   include_titles: Optional[bool] = None,
                   include_chapter_numbers: Optional[bool] = None,
                   include_verse_numbers: Optional[bool] = None,
                   include_verse_spans: Optional[bool] = None,
                   parallels: Optional[str] = None) -> Dict[str, Any]:
        """
        Get specific chapter by ID
        
        Args:
            bible_id: The ID of the Bible
            chapter_id: The ID of the chapter
            content_type: Content type (html, json, text)
            include_notes: Include footnotes
            include_titles: Include section titles
            include_chapter_numbers: Include chapter numbers
            include_verse_numbers: Include verse numbers
            include_verse_spans: Include verse spans
            parallels: Comma separated list of Bible IDs for parallel passages
        """
        params = {}
        if content_type:
            params['content-type'] = content_type
        if include_notes is not None:
            params['include-notes'] = str(include_notes).lower()
        if include_titles is not None:
            params['include-titles'] = str(include_titles).lower()
        if include_chapter_numbers is not None:
            params['include-chapter-numbers'] = str(include_chapter_numbers).lower()
        if include_verse_numbers is not None:
            params['include-verse-numbers'] = str(include_verse_numbers).lower()
        if include_verse_spans is not None:
            params['include-verse-spans'] = str(include_verse_spans).lower()
        if parallels:
            params['parallels'] = parallels
            
        return self._make_request('GET', f'bibles/{bible_id}/chapters/{chapter_id}', params=params)
    
    # Verses Endpoints
    def get_verses(self, bible_id: str, chapter_id: str) -> Dict[str, Any]:
        """
        Get verses for a specific chapter
        
        Args:
            bible_id: The ID of the Bible
            chapter_id: The ID of the chapter
        """
        return self._make_request('GET', f'bibles/{bible_id}/chapters/{chapter_id}/verses')
    
    def get_verse(self, bible_id: str, verse_id: str,
                 content_type: Optional[str] = None,
                 include_notes: Optional[bool] = None,
                 include_titles: Optional[bool] = None,
                 include_chapter_numbers: Optional[bool] = None,
                 include_verse_numbers: Optional[bool] = None,
                 include_verse_spans: Optional[bool] = None,
                 parallels: Optional[str] = None) -> Dict[str, Any]:
        """
        Get specific verse by ID
        
        Args:
            bible_id: The ID of the Bible
            verse_id: The ID of the verse
            content_type: Content type (html, json, text)
            include_notes: Include footnotes
            include_titles: Include section titles
            include_chapter_numbers: Include chapter numbers
            include_verse_numbers: Include verse numbers
            include_verse_spans: Include verse spans
            parallels: Comma separated list of Bible IDs for parallel passages
        """
        params = {}
        if content_type:
            params['content-type'] = content_type
        if include_notes is not None:
            params['include-notes'] = str(include_notes).lower()
        if include_titles is not None:
            params['include-titles'] = str(include_titles).lower()
        if include_chapter_numbers is not None:
            params['include-chapter-numbers'] = str(include_chapter_numbers).lower()
        if include_verse_numbers is not None:
            params['include-verse-numbers'] = str(include_verse_numbers).lower()
        if include_verse_spans is not None:
            params['include-verse-spans'] = str(include_verse_spans).lower()
        if parallels:
            params['parallels'] = parallels
            
        return self._make_request('GET', f'bibles/{bible_id}/verses/{verse_id}', params=params)
    
    # Search Endpoints
    def search_bible(self, bible_id: str, query: str, 
                    limit: Optional[int] = None,
                    offset: Optional[int] = None,
                    sort: Optional[str] = None,
                    fuzziness: Optional[str] = None) -> Dict[str, Any]:
        """
        Search within a Bible
        
        Args:
            bible_id: The ID of the Bible to search
            query: The search query
            limit: Number of results to return
            offset: Number of results to skip
            sort: Sort order (relevance, canonical)
            fuzziness: Fuzziness level (0, 1, 2, AUTO)
        """
        params = {'query': query}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        if sort:
            params['sort'] = sort
        if fuzziness:
            params['fuzziness'] = fuzziness
            
        return self._make_request('GET', f'bibles/{bible_id}/search', params=params)
    
    # Passage Endpoints
    def get_passage(self, bible_id: str, passage_id: str,
                   content_type: Optional[str] = None,
                   include_notes: Optional[bool] = None,
                   include_titles: Optional[bool] = None,
                   include_chapter_numbers: Optional[bool] = None,
                   include_verse_numbers: Optional[bool] = None,
                   include_verse_spans: Optional[bool] = None,
                   parallels: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a passage by ID
        
        Args:
            bible_id: The ID of the Bible
            passage_id: The passage ID (e.g., 'JHN.3.16-JHN.3.17')
            content_type: Content type (html, json, text)
            include_notes: Include footnotes
            include_titles: Include section titles
            include_chapter_numbers: Include chapter numbers
            include_verse_numbers: Include verse numbers
            include_verse_spans: Include verse spans
            parallels: Comma separated list of Bible IDs for parallel passages
        """
        params = {}
        if content_type:
            params['content-type'] = content_type
        if include_notes is not None:
            params['include-notes'] = str(include_notes).lower()
        if include_titles is not None:
            params['include-titles'] = str(include_titles).lower()
        if include_chapter_numbers is not None:
            params['include-chapter-numbers'] = str(include_chapter_numbers).lower()
        if include_verse_numbers is not None:
            params['include-verse-numbers'] = str(include_verse_numbers).lower()
        if include_verse_spans is not None:
            params['include-verse-spans'] = str(include_verse_spans).lower()
        if parallels:
            params['parallels'] = parallels
            
        return self._make_request('GET', f'bibles/{bible_id}/passages/{passage_id}', params=params)
    
    # Audio Endpoints
    def get_audio_bibles(self) -> Dict[str, Any]:
        """Get list of audio Bibles"""
        return self._make_request('GET', 'audio-bibles')
    
    def get_audio_bible(self, audio_bible_id: str) -> Dict[str, Any]:
        """
        Get specific audio Bible by ID
        
        Args:
            audio_bible_id: The ID of the audio Bible
        """
        return self._make_request('GET', f'audio-bibles/{audio_bible_id}')
    
    def get_audio_chapter(self, audio_bible_id: str, chapter_id: str) -> Dict[str, Any]:
        """
        Get audio for a specific chapter
        
        Args:
            audio_bible_id: The ID of the audio Bible
            chapter_id: The ID of the chapter
        """
        return self._make_request('GET', f'audio-bibles/{audio_bible_id}/chapters/{chapter_id}')
    
    # Additional utility methods
    def get_bible_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Utility method to get Bible by name"""
        bibles = self.get_bibles()
        for bible in bibles.get('data', []):
            if bible.get('name', '').lower() == name.lower():
                return bible
        return None
    
    def get_verse_text(self, bible_id: str, book: str, chapter: int, verse: int) -> Optional[str]:
        """Utility method to get specific verse text"""
        verse_id = f"{book.upper()}.{chapter}.{verse}"
        try:
            response = self.get_verse(bible_id, verse_id, content_type='text')
            return response.get('data', {}).get('content', '')
        except:
            return None

# Example usage
if __name__ == "__main__":
    # Initialize with your API key
    api_key = config('bible_api_key')
    bible_api = BibleAPI(api_key)
    
    try:
        # Example 1: Get list of Bibles
        # bibles = bible_api.get_bibles(language='eng')
        # print("Available English Bibles:")
        # for bible in bibles.get('data', []):
        #     print(f"- {bible['name']} ({bible['id']})")
        
        # Example 2: Get specific Bible (ESV) de4e12af7f28f599-01
        # esv_bible = bible_api.get_bible('de4e12af7f28f599-02')
        # print(f"\nESV Bible: {esv_bible['data']['name']}")
        
        # Example 3: Get books of the Bible
        # books = bible_api.get_books('de4e12af7f28f599-02')
        # print(books)
        # for book in books.get('data', []):
        #     print(book)
        #     print(f"- {book['name']} ({book['id']})")
        # print(f"\nBooks in ESV: {len(books['data'])} books")
        
        
        chapters = bible_api.get_chapters('de4e12af7f28f599-02', 'JHN')
        print(chapters)
        # Example 4: Get specific chapter
        # john_3 = bible_api.get_chapter('de4e12af7f28f599-02', 'JHN.3', content_type='text')
        # print(john_3)
        # print(f"\nJohn 3 content: {john_3['data']['content'][:100]}...")
        # john_3['data']['content'] contains the full text of John chapter 3
        # next_chapter = john_3['data']['next']
        # next_chapter['id']
        # next_chapter['number']
        # next_chapter['bookId']
        
        # previous_chapter = john_3['data']['previous']
        # previous_chapter['id']
        # previous_chapter['number']
        # previous_chapter['bookId']
        
        # Example 5: Get specific verse
        # john_3_16 = bible_api.get_verse('de4e12af7f28f599-02', 'JHN.3.18', content_type='text')
        # print(f"\nJohn 3:16: {john_3_16['data']['content']}")
        
        # Example 6: Search the Bible
        # search_results = bible_api.search_bible('de4e12af7f28f599-02', 'love', limit=5)
        # print(f"\nSearch results for 'love':")
        # for result in search_results['data']['verses']:
        #     print(f"- {result['reference']}: {result['text'][:50]}...")
            
    except Exception as e:
        print(f"Error: {e}")