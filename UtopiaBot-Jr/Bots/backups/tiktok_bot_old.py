import os
import sys
import time
import asyncio
import logging
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, JoinEvent
from google.cloud import texttospeech
from playsound import playsound
import emoji
import random

# --- CONFIG ---
TIKTOK_USER = "gamingutopiadf"  # <-- change to your TikTok username
AUDIO_DIR = "tts_audio"
JOKES_FILE = "jokes/random/random.txt"  # Updated to use organized folder structure
YO_MAMA_FILE = "jokes/yo_mama/yo_mama.txt"  # Updated to use organized folder structure
os.makedirs(AUDIO_DIR, exist_ok=True)

# Set up Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("../key/ivory-oarlock-410506-865276f8b548.json")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TikTokTTSBot")

# --- TTS Deduplication ---
spoken_messages = set()
last_reset = time.time()
RESET_INTERVAL = 300  # 5 minutes

def reset_spoken():
    global spoken_messages, last_reset
    if time.time() - last_reset > RESET_INTERVAL:
        spoken_messages.clear()
        last_reset = time.time()
        logger.info("[TTS] Deduplication cache reset.")

# --- TTS Helper ---
def speak(text: str):
    client = texttospeech.TextToSpeechClient()
    ssml = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-D")
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    result = client.synthesize_speech(input=ssml, voice=voice, audio_config=audio_config)
    fn = os.path.join(AUDIO_DIR, f"{int(time.time())}.mp3")
    with open(fn, "wb") as f:
        f.write(result.audio_content)
    playsound(fn)
    os.remove(fn)

# --- Joke Loaders ---
def get_joke():
    if os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, "r", encoding="utf-8") as f:
            jokes = [line.strip() for line in f if line.strip()]
        return random.choice(jokes) if jokes else "No jokes found."
    return "No jokes file found."

def get_yo_mama():
    if os.path.exists(YO_MAMA_FILE):
        with open(YO_MAMA_FILE, "r", encoding="utf-8") as f:
            jokes = [line.strip() for line in f if line.strip()]
        return random.choice(jokes) if jokes else "No yo mama jokes found."
    return "No yo mama jokes file found."

# --- TikTok Events ---
client = TikTokLiveClient(unique_id=TIKTOK_USER)

@client.on(ConnectEvent)
async def on_connect(evt):
    logger.info("Connected to TikTok Live chat")

@client.on(JoinEvent)
async def on_join(evt):
    reset_spoken()
    user = evt.user.unique_id
    welcome_message = f"Thanks for joining {user}!"
    
    # Deduplication: skip if this user already got welcomed recently
    dedup_key = f"welcome:{user}"
    if dedup_key in spoken_messages:
        logger.info(f"[WELCOME] Skipping duplicate welcome for: {user}")
        return
    spoken_messages.add(dedup_key)
    
    logger.info(f"[WELCOME] {welcome_message}")
    speak(welcome_message)

@client.on(CommentEvent)
async def on_comment(evt):
    reset_spoken()
    text = evt.comment.strip()
    user = evt.user.unique_id
    # Deduplication: skip if already spoken
    dedup_key = f"{user}:{text}"
    if dedup_key in spoken_messages:
        logger.info(f"[TTS] Skipping duplicate: {dedup_key}")
        return
    spoken_messages.add(dedup_key)
    # Command handling
    if text.lower().startswith("!joke"):
        joke = get_joke()
        logger.info(f"[JOKE] {joke}")
        speak(joke)
    elif text.lower().startswith("!yo-mama"):
        joke = get_yo_mama()
        logger.info(f"[YO MAMA] {joke}")
        speak(joke)
    else:
        # Normal TTS
        spoken = emoji.demojize(text, delimiters=(" ", " "))
        logger.info(f"[TTS] {user}: {spoken}")
        speak(f"{user} says {spoken}")

# --- Main ---
if __name__ == "__main__":
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("Shutting down…")
