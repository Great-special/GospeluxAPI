import requests
import json
import time
from typing import Optional, Dict, List, Any

class HeyGenVideoCreator:
    """
    A Python client for creating videos with HeyGen's V2 API.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the HeyGen client.
        
        Args:
            api_key: Your HeyGen API key
        """
        self.api_key = api_key
        self.base_url = "https://api.heygen.com"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def create_video(
        self,
        video_inputs: List[Dict[str, Any]],
        title: Optional[str] = None,
        caption: bool = False,
        dimension: Optional[Dict[str, int]] = None,
        callback_id: Optional[str] = None,
        callback_url: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a video with HeyGen.
        
        Args:
            video_inputs: List of scene configurations
            title: Video title
            caption: Enable captions (text-based input only)
            dimension: Custom dimensions {"width": 1280, "height": 720}
            callback_id: Custom ID for tracking
            callback_url: Webhook URL for completion notification
            folder_id: Folder ID to store the video
            
        Returns:
            Response containing video_id
        """
        endpoint = f"{self.base_url}/v2/video/generate"
        
        payload = {
            "video_inputs": video_inputs
        }
        
        if title:
            payload["title"] = title
        if caption:
            payload["caption"] = caption
        if dimension:
            payload["dimension"] = dimension
        if callback_id:
            payload["callback_id"] = callback_id
        if callback_url:
            payload["callback_url"] = callback_url
        if folder_id:
            payload["folder_id"] = folder_id
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        return response.json()
    
    def get_voices_list(self) -> Dict[str, Any]:
        """
        Retrieve the list of available voices.
        
        Returns:
            Response containing list of voices
        """
        endpoint = f"{self.base_url}/v2/voices"
        
        return requests.get(endpoint, headers=self.headers).json()["data"]["voices"]
    
    def get_avatars_list(self, avatar_type: str = "avatars") -> Dict[str, Any]:
        """
        Retrieve the list of available avatars.
        
        Returns:
            Response containing list of avatars
        """
        endpoint = f"{self.base_url}/v2/avatars"
        if avatar_type not in ("avatars", "talking_photos"):
            raise ValueError("avatar_type must be 'avatars' or 'talking_photos'")
        
        return requests.get(endpoint, headers=self.headers).json()["data"][avatar_type]
    
    def create_simple_video(
        self,
        avatar_id: str,
        voice_id: str,
        text: str,
        background_color: str = "#FFFFFF"
    ) -> Dict[str, Any]:
        """
        Create a simple video with default settings.
        
        Args:
            avatar_id: Avatar ID from HeyGen
            voice_id: Voice ID from HeyGen
            text: Text for the avatar to speak
            background_color: Background color in hex format
            
        Returns:
            Response containing video_id
        """
        video_inputs = [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id
            },
            "voice": {
                "type": "text",
                "voice_id": voice_id,
                "input_text": text
            },
            "background": {
                "type": "color",
                "value": background_color
            }
        }]
        
        return self.create_video(video_inputs)
    
    def create_multi_scene_video(
        self,
        scenes: List[Dict[str, str]],
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a video with multiple scenes.
        
        Args:
            scenes: List of scene dicts with keys: avatar_id, voice_id, text, background_color
            title: Video title
            
        Returns:
            Response containing video_id
        """
        video_inputs = []
        
        for scene in scenes:
            video_input = {
                "character": {
                    "type": "avatar",
                    "avatar_id": scene["avatar_id"]
                },
                "voice": {
                    "type": "text",
                    "voice_id": scene["voice_id"],
                    "input_text": scene["text"]
                }
            }
            
            # Add background if specified
            if "background_color" in scene:
                video_input["background"] = {
                    "type": "color",
                    "value": scene["background_color"]
                }
            elif "background_image" in scene:
                video_input["background"] = {
                    "type": "image",
                    "url": scene["background_image"]
                }
            elif "background_video" in scene:
                video_input["background"] = {
                    "type": "video",
                    "url": scene["background_video"],
                    "play_style": scene.get("play_style", "loop")
                }
            
            video_inputs.append(video_input)
        
        return self.create_video(video_inputs, title=title)
    
    def create_talking_photo_video(
        self,
        talking_photo_id: str,
        voice_id: str,
        text: str,
        talking_style: str = "stable",
        expression: str = "default",
        super_resolution: bool = False
    ) -> Dict[str, Any]:
        """
        Create a video with a talking photo.
        
        Args:
            talking_photo_id: Talking photo ID from HeyGen
            voice_id: Voice ID from HeyGen
            text: Text for the photo to speak
            talking_style: "stable" or "expressive"
            expression: "default" or "happy"
            super_resolution: Enhance image quality
            
        Returns:
            Response containing video_id
        """
        video_inputs = [{
            "character": {
                "type": "talking_photo",
                "talking_photo_id": talking_photo_id,
                "talking_style": talking_style,
                "expression": expression,
                "super_resolution": super_resolution
            },
            "voice": {
                "type": "text",
                "voice_id": voice_id,
                "input_text": text
            }
        }]
        
        return self.create_video(video_inputs)
    
    def create_video_with_custom_voice(
        self,
        avatar_id: str,
        voice_id: str,
        text: str,
        speed: float = 1.0,
        pitch: int = 0,
        emotion: Optional[str] = None,
        locale: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a video with customized voice settings.
        
        Args:
            avatar_id: Avatar ID from HeyGen
            voice_id: Voice ID from HeyGen
            text: Text for the avatar to speak
            speed: Voice speed (0.5 to 1.5)
            pitch: Voice pitch (-50 to 50)
            emotion: "Excited", "Friendly", "Serious", "Soothing", "Broadcaster"
            locale: Voice locale (e.g., "en-US", "en-IN")
            
        Returns:
            Response containing video_id
        """
        voice_config = {
            "type": "text",
            "voice_id": voice_id,
            "input_text": text,
            "speed": speed,
            "pitch": pitch
        }
        
        if emotion:
            voice_config["emotion"] = emotion
        if locale:
            voice_config["locale"] = locale
        
        video_inputs = [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id
            },
            "voice": voice_config
        }]
        
        return self.create_video(video_inputs)
    
    def create_video_with_text_overlay(
        self,
        avatar_id: str,
        voice_id: str,
        speech_text: str,
        overlay_text: str,
        text_position: Dict[str, float] = {"x": 0.5, "y": 0.9},
        text_color: str = "#FFFFFF",
        font_size: float = 48
    ) -> Dict[str, Any]:
        """
        Create a video with text overlay.
        
        Args:
            avatar_id: Avatar ID from HeyGen
            voice_id: Voice ID from HeyGen
            speech_text: Text for the avatar to speak
            overlay_text: Text to display on screen
            text_position: Position dict with x and y coordinates
            text_color: Text color in hex format
            font_size: Font size in points
            
        Returns:
            Response containing video_id
        """
        video_inputs = [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id
            },
            "voice": {
                "type": "text",
                "voice_id": voice_id,
                "input_text": speech_text
            },
            "text": {
                "type": "text",
                "text": overlay_text,
                "font_size": font_size,
                "color": text_color,
                "position": text_position,
                "text_align": "center",
                "line_height": 1.2
            }
        }]
        
        return self.create_video(video_inputs)
    
    def create_social_media_video(
        self,
        avatar_id: str,
        voice_id: str,
        text: str,
        platform: str = "instagram_story"
    ) -> Dict[str, Any]:
        """
        Create a video optimized for social media platforms.
        
        Args:
            avatar_id: Avatar ID from HeyGen
            voice_id: Voice ID from HeyGen
            text: Text for the avatar to speak
            platform: "instagram_story", "tiktok", "youtube", "square"
            
        Returns:
            Response containing video_id
        """
        dimensions = {
            "instagram_story": {"width": 1080, "height": 1920},
            "tiktok": {"width": 1080, "height": 1920},
            "youtube": {"width": 1920, "height": 1080},
            "square": {"width": 1080, "height": 1080}
        }
        
        video_inputs = [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id
            },
            "voice": {
                "type": "text",
                "voice_id": voice_id,
                "input_text": text
            }
        }]
        
        return self.create_video(
            video_inputs,
            dimension=dimensions.get(platform, dimensions["youtube"])
        )

    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation.
        
        Args:
            video_id: The video ID returned from create_video
            
        Returns:
            Response containing video status and URL if completed
        """
        endpoint = f"{self.base_url}/v1/video_status.get"
        params = {"video_id": video_id}
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        return response.json()
    
    def wait_for_video(
        self,
        video_id: str,
        check_interval: int = 10,
        max_wait_time: int = 600
    ) -> Dict[str, Any]:
        """
        Wait for a video to complete processing and return the result.
        
        Args:
            video_id: The video ID to wait for
            check_interval: Seconds between status checks (default: 10)
            max_wait_time: Maximum seconds to wait (default: 600 = 10 minutes)
            
        Returns:
            Final video status response
        """
        elapsed_time = 0
        
        # print(f"Waiting for video {video_id} to complete...")
        
        while elapsed_time < max_wait_time:
            status_response = self.get_video_status(video_id)
            
            if status_response.get("error"):
                # print(f"Error: {status_response['error']}")
                return status_response
            
            data = status_response.get("data", {})
            status = data.get("status")
            
            print(f"Status: {status} (elapsed: {elapsed_time}s)")
            
            # Video statuses: pending, processing, completed, failed
            if status == "completed":
                video_url = data.get("video_url")
                print(f"✓ Video completed! URL: {video_url}")
                return status_response
            elif status == "failed":
                error_msg = data.get("error", {}).get("message", "Unknown error")
                print(f"✗ Video generation failed: {error_msg}")
                return status_response
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        print(f"✗ Timeout: Video did not complete within {max_wait_time} seconds")
        return self.get_video_status(video_id)
    
    def download_video(self, video_url: str, output_path: str = "video.mp4") -> bool:
        """
        Download a completed video to local file.
        
        Args:
            video_url: The video URL from get_video_status
            output_path: Local file path to save video (default: "video.mp4")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Downloading video to {output_path}...")
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Video downloaded successfully to {output_path}")
            return True
        except Exception as e:
            print(f"✗ Download failed: {str(e)}")
            return False
    
    def create_and_wait(
        self,
        video_inputs: List[Dict[str, Any]],
        output_path: str = "video.mp4",
        **kwargs
    ) -> Optional[str]:
        """
        Create a video and wait for it to complete, then optionally download.
        
        Args:
            video_inputs: List of scene configurations
            output_path: Path to save video (if None, won't download)
            **kwargs: Additional arguments for create_video
            
        Returns:
            Video URL if successful, None otherwise
        """
        # Create video
        response = self.create_video(video_inputs, **kwargs)
        
        if response.get("error"):
            print(f"✗ Video creation failed: {response['error']}")
            return None
        
        video_id = response.get("data", {}).get("video_id")
        if not video_id:
            print("✗ No video_id in response")
            return None
        
        print(f"✓ Video created with ID: {video_id}")
        
        # Wait for completion
        status_response = self.wait_for_video(video_id)
        
        if status_response.get("data", {}).get("status") != "completed":
            return None
        
        video_url = status_response.get("data", {}).get("video_url")
        
        # Download if output_path specified
        if output_path and video_url:
            self.download_video(video_url, output_path)
        
        return video_url


def select_voice_for_scene(speaker_type, voices):
    speaker_type = speaker_type.lower()

    if speaker_type == "god":
        # deep authoritative male voice
        for v in voices:
            if v.get("gender") == "male" and "deep" in v.get("name", "").lower():
                return v["voice_id"]

    if speaker_type == "angel":
        # soft neutral/female voice
        for v in voices:
            if v.get("gender") in ["female", "neutral"]:
                return v["voice_id"]

    if speaker_type == "male":
        for v in voices:
            if v.get("gender") == "male":
                return v["voice_id"]

    if speaker_type == "female":
        for v in voices:
            if v.get("gender") == "female":
                return v["voice_id"]

    if speaker_type == "presenter":
        # neutral default presenter voice
        for v in voices:
            if v.get("gender") == "neutral":
                return v["voice_id"]

    # fallback
    return voices[0]["voice_id"]



def select_avatar_for_scene(speaker_type, avatars):
    speaker_type = speaker_type.lower()

    if speaker_type == "god":
        # strong male avatar
        for a in avatars:
            if a.get("gender") == "male" and "serious" in a.get("name", "").lower():
                return a["avatar_id"]

    if speaker_type == "angel":
        # soft peaceful avatar
        for a in avatars:
            if a.get("gender") in ["female", "neutral"]:
                return a["avatar_id"]

    if speaker_type == "male":
        for a in avatars:
            if a.get("gender") == "male":
                return a["avatar_id"]

    if speaker_type == "female":
        for a in avatars:
            if a.get("gender") == "female":
                return a["avatar_id"]

    if speaker_type == "presenter":
        # neutral/host avatar
        return avatars[0]["avatar_id"]

    return avatars[0]["avatar_id"]



# Example usage
# if __name__ == "__main__":
#     # Initialize the client
#     API_KEY = "your-api-key-here"
#     client = HeyGenVideoCreator(API_KEY)
    
    # # Example 1: Simple video
    # print("Creating simple video...")
    # response = client.create_simple_video(
    #     avatar_id="your-avatar-id",
    #     voice_id="your-voice-id",
    #     text="Hello! This is a test video created with Python.",
    #     background_color="#4A90E2"
    # )
    # print(f"Response: {json.dumps(response, indent=2)}")
    
    # Example 2: Multi-scene video
    # print("\nCreating multi-scene video...")
    # scenes = [
    #     {
    #         "avatar_id": "your-avatar-id",
    #         "voice_id": "your-voice-id",
    #         "text": "Welcome to scene one!",
    #         "background_color": "#FF6B6B"
    #     },
    #     {
    #         "avatar_id": "your-avatar-id",
    #         "voice_id": "your-voice-id",
    #         "text": "Now we're in scene two!",
    #         "background_color": "#4ECDC4"
    #     }
    # ]
    # response = client.create_multi_scene_video(
    #     scenes=scenes,
    #     title="My Multi-Scene Video"
    # )
    # print(f"Response: {json.dumps(response, indent=2)}")
    
    # # Example 3: Video with custom voice
    # print("\nCreating video with custom voice...")
    # response = client.create_video_with_custom_voice(
    #     avatar_id="your-avatar-id",
    #     voice_id="your-voice-id",
    #     text="This is an excited announcement!",
    #     speed=1.2,
    #     pitch=10,
    #     emotion="Excited"
    # )
    # print(f"Response: {json.dumps(response, indent=2)}")
    
    # # Example 4: Social media video
    # print("\nCreating Instagram Story video...")
    # response = client.create_social_media_video(
    #     avatar_id="your-avatar-id",
    #     voice_id="your-voice-id",
    #     text="Check out this vertical video!",
    #     platform="instagram_story"
    # )
    # print(f"Response: {json.dumps(response, indent=2)}")
    
    # Example 1: Create video and check status manually
    # print("=" * 50)
    # print("Example 1: Create and check status manually")
    # print("=" * 50)
    # response = client.create_simple_video(
    #     avatar_id="your-avatar-id",
    #     voice_id="your-voice-id",
    #     text="Hello! This is a test video.",
    #     background_color="#4A90E2"
    # )
    
    # if response.get("data"):
    #     video_id = response["data"]["video_id"]
    #     print(f"✓ Video created! ID: {video_id}")
        
    #     # Check status
    #     status = client.get_video_status(video_id)
    #     print(f"Status: {json.dumps(status, indent=2)}")
    
    # # Example 2: Create and wait for completion
    # print("\n" + "=" * 50)
    # print("Example 2: Create and wait for completion")
    # print("=" * 50)
    
    # video_inputs = [{
    #     "character": {
    #         "type": "avatar",
    #         "avatar_id": "your-avatar-id"
    #     },
    #     "voice": {
    #         "type": "text",
    #         "voice_id": "your-voice-id",
    #         "input_text": "This video will auto-wait for completion!"
    #     },
    #     "background": {
    #         "type": "color",
    #         "value": "#FF6B6B"
    #     }
    # }]
    
    # video_url = client.create_and_wait(
    #     video_inputs=video_inputs,
    #     title="Auto-Wait Video",
    #     output_path="my_video.mp4"  # Will download automatically
    # )
    
    # if video_url:
    #     print(f"✓ Video URL: {video_url}")
    
    # # Example 3: Create without downloading
    # print("\n" + "=" * 50)
    # print("Example 3: Get URL without downloading")
    # print("=" * 50)
    
    # video_url = client.create_and_wait(
    #     video_inputs=video_inputs,
    #     title="URL Only Video",
    #     output_path=None  # Don't download, just get URL
    # )
    
    # if video_url:
    #     print(f"✓ Video URL: {video_url}")
    #     print("You can access this URL in your browser or download it later")
    
    # Example 4: Multi-scene with wait
    # print("\n" + "=" * 50)
    # print("Example 4: Multi-scene video with download")
    # print("=" * 50)
    
    # scenes = [
    #     {
    #         "avatar_id": "your-avatar-id",
    #         "voice_id": "your-voice-id",
    #         "text": "Welcome to scene one!",
    #         "background_color": "#FF6B6B"
    #     },
    #     {
    #         "avatar_id": "your-avatar-id",
    #         "voice_id": "your-voice-id",
    #         "text": "Now we're in scene two!",
    #         "background_color": "#4ECDC4"
    #     }
    # ]
    
    # response = client.create_multi_scene_video(scenes=scenes, title="Multi-Scene")
    
    # if response.get("data"):
    #     video_id = response["data"]["video_id"]
    #     result = client.wait_for_video(video_id)
        
    #     if result.get("data", {}).get("status") == "completed":
    #         video_url = result["data"]["video_url"]
    #         client.download_video(video_url, "multi_scene_video.mp4")