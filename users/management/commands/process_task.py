from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from songs.models import GeneratedVideo
from songs.views import generate_video_task, client
import traceback
import requests
import re
import os

LOG_FILE = "/home/gospqyhq/video_cron.log"


class Command(BaseCommand):
    help = "Process queued videos"

    def log(self, message):
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)

        self.stdout.write(log_message)

    def check_status(self):
        self.log("Checking the video status and downloading...")
        videos = GeneratedVideo.objects.filter(status="processing")[:5]
        
        if not videos:
            self.log("ℹ️ No processed videos found")
            return

        for video in  videos:
            if video.video_id:
                video_status = client.get_video_status(video.video_id)
                
                data = video_status.get("data", {})
                status = data.get("status")
                
                # Video statuses: pending, processing, completed, failed
                if status == "completed":
                    safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', "", video.title)
                    filename = f"heygen_{video.video_id}_{safe_title}.mp4"
                    video_url = data.get("video_url")
                    response = requests.get(video_url, stream=True)
                    video.video_file = ContentFile(response.iter_content(chunk_size=8192), filename)
                    video.status = status
                    video.save()
                
                if status == "failed":
                    video.status = status 
                    video.save()
            
                    
                
    def handle(self, *args, **kwargs):
        self.log("🔥 CRON STARTED")

        videos = GeneratedVideo.objects.filter(status="queued")[:5]

        if not videos:
            self.log("ℹ️ No queued videos found")
            return

        for video in videos:
            self.log(f"🎬 Processing video ID={video.id}")

            video.status = "processing"
            video.save()

            try:
                length_seconds = 180

                generate_video_task(
                    video.id,
                    video.title,
                    video.bible_verse,
                    "inspirational",
                    length_seconds
                )

                self.log(f"✅ SUCCESS video ID={video.id}")

            except Exception as e:
                video.status = "failed"
                video.save()

                error_trace = traceback.format_exc()
                self.log(f"❌ FAILED video ID={video.id}")
                self.log(f"❌ ERROR: {str(e)}")
                self.log(error_trace)
                
        self.check_status()
        self.log("✅ CRON FINISHED")


# from django.core.management.base import BaseCommand
# from songs.models import GeneratedVideo
# from songs.views import generate_video_task

# class Command(BaseCommand):
#     help = "Process queued videos"

#     def handle(self, *args, **kwargs):
#         videos = GeneratedVideo.objects.filter(status="queued")

#         for video in videos:
#             video.status = "processing"
#             video.save()

#             try:
#                 length_seconds = 180
#                 generate_video_task(
#                     video.id,
#                     video.title,
#                     video.bible_verse,
#                     "inspirational",
#                     length_seconds
#                 )
#             except Exception as e:
#                 video.status = "failed"
#                 video.save()
