from django.core.management.base import BaseCommand
from django.utils import timezone
from songs.models import GeneratedVideo
from songs.views import generate_video_task
import traceback
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

    def handle(self, *args, **kwargs):
        self.log("🔥 CRON STARTED")

        videos = GeneratedVideo.objects.filter(status="queued")[:3]

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
