import requests
import re
import json
from huggingface_hub import InferenceClient, login
from decouple import config


SUNO_API_KEY = config('SUNO_API_KEY')
SUNO_BASE_URL = "https://api.sunoapi.org/api/v1"


suno_headers = {
    "Authorization": f"Bearer {SUNO_API_KEY}",
    "Content-Type": "application/json"
}


login(config('HF_API_TOKEN'))



bible_verse = 'For I known the plans I have for you, says the Lord. They are plans of good and not for disaster, to give you a future and a hope. Jeremiah 29:11'


# class SingletonModelLoader:
#     _model_instance = None

#     def __new__(cls):
#         if cls._model_instance is None:
#             cls._model_instance = super().__new__(cls)
#         return cls._model_instance
    
#     def __init__(self, model_name: str ='mistralai/Mistral-7B-Instruct-v0.3', task_type: str ='text-generation'):
#         self.model_name = model_name
#         self.task_type = task_type
#         self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
#         self.model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
#         self.generator = pipeline(task_type,  model=self.model, tokenizer=self.tokenizer)
    
    
#     def __remove_punctuation(self, text):
#         """Remove punctuation from the given text."""
#         import string
#         return text.translate(str.maketrans('', '', string.punctuation))
    
    

#     def generate_song_title(self, bible_verse):
#         """Generate a song title based on a Bible verse using a text generation model."""
    
#         prompt = f"Generate a short song title for: {bible_verse}"
#         titles = self.generator(prompt, max_new_tokens=10, 
#                                 pad_token_id=self.tokenizer.eos_token_id, 
#                                 return_full_text=False)
#         return self.__remove_punctuation(titles[0]['generated_text']).strip()
#         # return "Faithful God"

#     def generate_sermon(self, bible_verse, length_points=5):
#         """Generate a song title based on a Bible verse using a text generation model."""

#         prompt = f"""Generate a full sermon outline from {bible_verse}.
#         Include: a captivating title, a clear objective, an introduction, 
#         {length_points} main points with 1 or 2 sub-points (explanation, illustration, application, and supporting Scriptures), an application section, and a conclusion. 
#         Make it inspirational and practical for teaching and preaching."""
#         titles = self.generator(prompt, max_new_tokens=200, pad_token_id=self.tokenizer.eos_token_id, 
#                                 return_full_text=False)
#         return titles[0]['generated_text'].strip()



#     def generate_song(self, bible_verse, title=None, genre='gospel', mood='uplifting', song_length_style='medium song with 2'):
#         if mood not in ('uplifting', 'reflective', 'joyful', 'somber'):
#             raise ValueError("Invalid mood. Choose from 'uplifting', 'reflective', 'joyful', 'somber'.")
        
#         if song_length_style not in ('short song with 2', 'medium song with 2', 'full song with 3'):
#             raise ValueError("Invalid song length/style. Choose from 'short song with 2', 'medium song with 2', 'full song with 3'.")
        
#         if genre not in ('worship', 'classical', 'gospel', 'contemporary christian', 'hymn', 'pop', 'rock', 'afrobeat'):
#             raise ValueError("Invalid genre. Choose from 'worship', 'gospel', 'contemporary Christian', 'hymn'.")
        
#         url = f"{SUNO_BASE_URL}/generate"
#         prompt_template = f"""You are a professional Christian songwriter. 
#             Create a {genre} song based on {bible_verse}. The song should have a {mood} tone. Structure it as {song_length_style} verses, a repeating chorus, and a bridge. 
#             Keep the lyrics faithful to the message of the verse while making it musically engaging and emotionally impactful. 
#             Ensure the chorus is memorable and can be easily sung by others."""
        
        
#         payload = {
#             "prompt": prompt_template,
#             "style": genre,
#             "title": self.generate_song_title(bible_verse) if title == None else title,
#             "customMode": True,
#             "instrumental": False,
#             "model": "V3_5",
#             # "negativeTags": "Heavy Metal, Upbeat Drums",
#             "callBackUrl": "https://api.example.com/callback"
#         }

#         response = requests.post(url, headers=suno_headers, json=payload)
#         if response.status_code == 200:
#             return response.json()
#         else:
#             print("Error:", response.status_code, response.text)
#             return None

# Example usage

# model_generator = SingletonModelLoader()
# song = model.generate_song(bible_verse)
# print(song)


def model_generator(prompt, max_tokens=50, temperature=0.8):
    """
    Send a text prompt to Mistral-7B-Instruct-v0.3 and return the generated response.
    """
    try:
        client = InferenceClient(
            provider="featherless-ai",
            api_key=config('HF_API_TOKEN'))


        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.7,
        )
        res = completion.choices[0].message.content.strip()
        return res
    except Exception as e:
        return f"Request error: {e}"


def generate_song(bible_verse, title=None, genre='gospel', mood='uplifting', song_length_style='medium song with 2'):
    
    API_KEY = config('SUNO_API_KEY')
    print(API_KEY)
    BASE_URL = "https://api.sunoapi.org/api/v1"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    if mood not in ('uplifting', 'reflective', 'joyful', 'somber'):
        raise ValueError("Invalid mood. Choose from 'uplifting', 'reflective', 'joyful', 'somber'.")
    
    if song_length_style not in ('short song with 2', 'medium song with 2', 'full song with 3'):
        raise ValueError("Invalid song length/style. Choose from 'short song with 2', 'medium song with 2', 'full song with 3'.")
    
    if genre not in ('worship', 'classical', 'gospel', 'contemporary christian', 'hymn', 'pop', 'rock', 'afrobeat'):
        raise ValueError("Invalid genre. Choose from 'worship', 'gospel', 'contemporary Christian', 'hymn'.")
    
    url = f"{BASE_URL}/generate"
    prompt_template = f"""You are a professional Christian songwriter. 
        Create a {genre} song based on {bible_verse}. The song should have a {mood} tone. Structure it as {song_length_style} verses, a repeating chorus, and a bridge. 
        Keep the lyrics faithful to the message of the verse while making it musically engaging and emotionally impactful. 
        Ensure the chorus is memorable and can be easily sung by others."""
    
    payload = {
        "prompt": model_generator(prompt_template, max_tokens=2500, temperature=0.7),
        "style": genre,
        "title": title,
        "customMode": True,
        "instrumental": False,
        "model": "V3_5",
        # "negativeTags": "Heavy Metal, Upbeat Drums",
        "callBackUrl": "https://gospelux.com/api/v1/songs/generated-music-callback/"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code, response.text)
        return response


def generate_sermon(bible_verse, length_points=5):
    """Generate a song title based on a Bible verse using a text generation model."""

    prompt = f"""Generate a full sermon outline from {bible_verse}.
    Include: a captivating title, a clear objective, an introduction, 
    {length_points} main points with 1 or 2 sub-points (explanation, illustration, application, and supporting Scriptures), an application section, and a conclusion. 
    Make it inspirational and practical for teaching and preaching."""
    titles = model_generator(prompt, max_tokens=3000)
    try:
        return titles[0]['generated_text'].strip()
    except Exception:
        return titles.strip()


def generate_video(verse, video_style='bibilical', length_seconds=60):
    prompt = f"""You are a professional video scriptwriter. 
        Create a {length_seconds}-second {video_style} video script based on the following topic: {verse}. 
        Ensure the script is engaging, concise, and suitable for a short video format."""
    video_scripts = model_generator(prompt, max_tokens=500)
    client = InferenceClient(
        provider="fal-ai",
        api_key=config("HF_API_TOKEN"),
    )

    video = client.text_to_video(
        prompt=video_scripts,
        model="meituan-longcat/LongCat-Video",
    )
    
    return video

def generate_heygen_video(verse: str, video_style: str ='bibilical', length_seconds: int = 60, voice: int = 1, avatar: int = 1):
    """
    Sends a request to the HeyGen API to generate a video with a specified
    avatar, voice, and script.

    Args:
        verse (str): The Bible verse or topic to base the video script on.
        video_style (str): The style of the video (default is 'bibilical').
        length_seconds (int): The desired length of the video in seconds (default is 60).
        voice (int): The voice ID to use for the video narration (default is 1).
        avatar (int): The avatar ID to use for the video character (default is 1).
        

    Returns:
        The JSON response from the HeyGen API, containing the video ID and status.
    """
    voices = {
        1:"2d5b0e6cf36f460aa7fc47e3eee4ba54",
    }
    
    avatars = {
        1:"Daisy-inskirt-20220818",
    }
    
    url = "https://api.heygen.com/v2/video/generate"
    api_key = config('HeyGen_API_KEY')
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    prompt = f"""You are a professional video scriptwriter. 
        Create a {length_seconds}-second {video_style} video script based on the following topic: {verse}. 
        Ensure the script is engaging, concise, and suitable for a short video format."""
    video_scripts = model_generator(prompt, max_tokens=500)

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatars.get(avatar, "Daisy-inskirt-20220818"),
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": video_scripts,  # Uses the dynamic script text
                    "voice_id":  voices.get(voice, "2d5b0e6cf36f460aa7fc47e3eee4ba54"),
                },
                "background": {
                    "type": "color",
                    "value": "#008000"
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def get_video_status(video_id: str):
    API_KEY = config('HEYGEN_API_KEY')

    # The base URL for the HeyGen API
    base_url = "https://api.heygen.com/v1/video_status.get"

    # The parameters to be passed in the URL (query string)
    params = {
        'video_id': video_id
    }

    # The custom headers, including the X-Api-Key
    headers = {
        'X-Api-Key': API_KEY
    }

    try:
        # Make the GET request
        response = requests.get(base_url, headers=headers, params=params)

        # Check for a successful response (status code 200)
        response.raise_for_status() 

        # Print the JSON response content
        print("Status Code:", response.status_code)
        print("Response JSON:")
        print(response.json())
        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred: {err}")
        return f"An unexpected error occurred: {err}"