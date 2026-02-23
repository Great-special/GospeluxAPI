from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from sklearn import logger
from songs.models import GeneratedSongs
from core.generation_utility import model_generator, generate_song
import re


LOG_FILE = "/home/gospqyhq/songs_cron.log"


class Command(BaseCommand):
    help = 'Process pending song generation requests'

    
    def log(self, message):
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)
    
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of songs to process in one run'
        )
        parser.add_argument(
            '--max-age-minutes',
            type=int,
            default=60,
            help='Maximum age of pending songs to process (prevents stuck records)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        max_age = options['max_age_minutes']
        
        # Find pending songs that aren't too old and haven't been attempted too many times
        cutoff_time = timezone.now() - timedelta(minutes=max_age)
        
        pending_songs = GeneratedSongs.objects.filter(
            status='pending',
            created_at__gte=cutoff_time,
            retry_count__lt=3  # Max 3 attempts
        ).order_by('created_at')[:batch_size]
        
        if not pending_songs:
            self.stdout.write(self.style.SUCCESS('No pending songs to process'))
            return
        
        self.stdout.write(f'Processing {pending_songs.count()} pending songs...')
        
        for song in pending_songs:
            try:
                self.process_song(song)
            except Exception as e:
                self.log(f"Failed to process song {song.id}: {e}")
                song.retry_count += 1
                song.error_message = str(e)
                if song.retry_count >= 3:
                    song.status = 'failed'
                song.save(update_fields=['retry_count', 'error_message', 'status'])
    
    def process_song(self, song):
        """Process a single song generation"""
        self.stdout.write(f'Processing song {song.id}: {song.bible_verse[:50]}...')
        
        # Update to processing
        song.status = 'processing'
        song.save(update_fields=['status'])
        
        try:
            # Step 1: Generate title if needed
            if not song.title or song.title == "Generating...":
                self.stdout.write(f'  → Generating title...')
                prompt = f"Generate a short song title for: {song.bible_verse}"
                
                try:
                    res = model_generator(prompt, max_tokens=50, temperature=0.8)
                    parts = re.findall(r'"(.*?)"', res)
                    if len(parts) >= 2:
                        title = parts[1]
                    elif len(parts) >= 1:
                        title = parts[0]
                    else:
                        title = "Untitled Song"
                    
                    song.title = title
                    song.save(update_fields=['title'])
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Title: {title}'))
                    
                except Exception as e:
                    self.log(f"LLM title generation failed for song {song.id}: {e}")
                    song.title = "Untitled Song"
                    song.save(update_fields=['title'])
            
            # Step 2: Generate music
            self.stdout.write(f'  → Generating music with Suno API...')
            response = generate_song(
                title=song.title,
                bible_verse=song.bible_verse,
                genre=song.genre,
                mood=song.mood
            )
            
            if response.get('code') != 200:
                raise Exception(
                    f"Suno API failed with code {response.get('code')}: {response.get('msg')}"
                )
            
            task_id = response.get('data', {}).get('taskId')
            if not task_id:
                raise Exception("No taskId received from Suno API")
            
            # Update song with Suno task ID
            song.task_id = task_id
            song.status = 'processing'  # Waiting for Suno callback
            song.processed_at = timezone.now()
            song.save(update_fields=['task_id', 'status', 'processed_at'])
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Music generation initiated (task: {task_id})'))
            
        except Exception as e:
            self.log(f"Error processing song {song.id}: {e}")
            song.retry_count += 1
            song.error_message = str(e)
            
            if song.retry_count >= 3:
                song.status = 'failed'
                self.stdout.write(self.style.ERROR(f'  ✗ Failed after 3 attempts: {e}'))
            else:
                song.status = 'pending'  # Retry later
                self.stdout.write(self.style.WARNING(f'  ⚠ Will retry (attempt {song.retry_count}/3): {e}'))
            
            song.save(update_fields=['retry_count', 'error_message', 'status'])
            raise