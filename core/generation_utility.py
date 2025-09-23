import requests
import json
# from transformers import pipeline
from decouple import config



API_KEY = config('SUNO_API_KEY', default='your_api_key_here')
BASE_URL = "https://api.sunoapi.org/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

bible_verse = 'For I known the plans I have for you, says the Lord. They are plans of good and not for disaster, to give you a future and a hope. Jeremiah 29:11'
# generator = pipeline('text2text-generation', model='google/flan-t5-base')
# prompt = f"Generate a catchy and meaningful song title based on the following Bible verse: {bible_verse}"
# prompt = f"Bible verse: {bible_verse}\n\nGenerate ONLY a short song title (max 5 words)."


def generate_song_title(bible_verse):
    """Generate a song title based on a Bible verse using a text generation model."""
    # generator = pipeline('text-generation', model='meta-llama/Meta-Llama-3-8B')
    # generator = pipeline('text2text-generation', model='google/flan-t5-base')
    # prompt = f"Generate a catchy and meaningful song title based on the following Bible verse: {bible_verse}"
    # song_title_prompt_template = f"""
    #     Bible Verse: "The Lord is my shepherd; I shall not want." (Psalm 23:1)
    #     Song Title: "Shepherd of My Soul"

    #     Bible Verse: "I can do all things through Christ who strengthens me." (Philippians 4:13)
    #     Song Title: "Strength in Christ"

    #     Bible Verse: "Be still, and know that I am God." (Psalm 46:10)
    #     Song Title: "Be Still"

    #     Bible Verse: "For God so loved the world that He gave His only begotten Son." (John 3:16)
    #     Song Title: "Love So Great"

    #     Bible Verse: "The joy of the Lord is your strength." (Nehemiah 8:10)
    #     Song Title: "Joy Is My Strength"

    #     Bible Verse: "Your word is a lamp to my feet and a light to my path." (Psalm 119:105)
    #     Song Title: "Light on My Path"

    #     Bible Verse: "The Lord is my light and my salvation; whom shall I fear?" (Psalm 27:1)
    #     Song Title: "My Salvation"

    #     Bible Verse: "We walk by faith, not by sight." (2 Corinthians 5:7)
    #     Song Title: "Walk by Faith"

    #     Bible Verse: "Those who wait on the Lord shall renew their strength." (Isaiah 40:31)
    #     Song Title: "Wings Like Eagles"

    #     Bible Verse: "The Lord is good; His mercy endures forever." (Psalm 136:1)
    #     Song Title: "Endless Mercy"

    #     Bible Verse: "{bible_verse}"
    #     Song Title:
    # """
    # titles = generator(song_title_prompt_template, max_new_tokens=10, num_return_sequences=1, do_sample=True, top_p=1.3, temperature=1.3)
    # return titles[0]['generated_text'].strip()
    return "Faithful God"

def generate_sermon(bible_verse, length_points=5):
    """Generate a song title based on a Bible verse using a text generation model."""
    # generator = pipeline('text-generation', model='meta-llama/Meta-Llama-3-8B')
    generator = pipeline('text2text-generation', model='google/flan-t5-base')
    prompt = f"""Generate a full sermon outline from {bible_verse}.
    Include: a captivating title, a clear objective, an introduction, 
    {length_points} main points with 1 or 2 sub-points (explanation, illustration, application, and supporting Scriptures), an application section, and a conclusion. 
    Make it inspirational and practical for teaching and preaching."""
    titles = generator(prompt, max_new_tokens=200, num_return_sequences=1)
    return titles[0]['generated_text'].strip()





def generate_song(bible_verse, title=None, genre='gospel', mood='uplifting', song_length_style='medium song with 2'):
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
        "prompt": prompt_template,
        "style": genre,
        "title": generate_song_title(bible_verse) if not title else title,
        "customMode": True,
        "instrumental": False,
        "model": "V3_5",
        # "negativeTags": "Heavy Metal, Upbeat Drums",
        "callBackUrl": "https://api.example.com/callback"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code, response.text)
        return None

# Example usage



# song = generate_song(bible_verse)
# print(song)
