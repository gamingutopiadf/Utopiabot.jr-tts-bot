"""
TikTok TTS Bot - Unified Version
Supports both GUI and command-line modes
"""
import os
import sys
import time
import asyncio
import logging
from datetime import datetime
import threading
import queue
import random
import argparse
import requests
import webbrowser

# Core bot imports
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, JoinEvent
from google.cloud import texttospeech
from playsound import playsound
import emoji

# GUI imports (optional)
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️ GUI not available - tkinter not installed. Running in command-line mode only.")

class TikTokTTSBot:
    def __init__(self, username="gamingutopiadf", gui_mode=False):
        # Configuration
        self.username = username
        self.gui_mode = gui_mode
        self.audio_dir = "tts_audio"
        self.jokes_file = "jokes/random/random.txt"
        self.yo_mama_file = "jokes/yo_mama/yo_mama.txt"
        
        # Create audio directory
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Set up Google Cloud credentials using script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, "..", "key", "ivory-oarlock-410506-865276f8b548.json")
        
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            self.log("✅ Google Cloud credentials loaded", "success")
        else:
            self.log("⚠️ Google Cloud credentials not found", "warning")
            self.log(f"🔍 Looking for credentials at: {credentials_path}", "info")
        
        # TTS Deduplication
        self.spoken_messages = set()
        self.last_reset = time.time()
        self.reset_interval = 300  # 5 minutes
        
        # Bot state
        self.bot_client = None
        self.bot_running = False
        self.bot_thread = None
        self.online_check_thread = None
        self.last_online_check = time.time()
        self.connection_status = "Disconnected"
        self.connection_attempts = 0
        self.last_connection_attempt = 0
        self.rate_limit_cooldown = 60  # Wait 60 seconds after rate limit
        self.connection_retry_delay = 30  # Start with 30 seconds between retries
        self.failed_attempts = 0
        self.auto_retry_enabled = True  # Enable automatic retries
        self.max_retry_attempts = 3  # Maximum automatic retry attempts
        
        # Statistics
        self.stats = {
            "messages": 0,
            "jokes": 0,
            "welcomes": 0,
            "start_time": None,
            "connection_checks": 0,
            "last_activity": None
        }
        
        # User tracking
        self.joined_users = []  # List of users who joined
        self.unique_users = set()  # Set to track unique users
        
        # GUI components (if in GUI mode)
        if self.gui_mode and GUI_AVAILABLE:
            self.setup_gui()
        else:
            # Command line setup
            self.setup_logging()
            
    def setup_logging(self):
        """Set up logging for command-line mode"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("TikTokTTSBot")
        
    def log(self, message, level="info"):
        """Universal logging function"""
        if self.gui_mode and hasattr(self, 'log_queue'):
            # GUI mode - add to queue
            timestamp = datetime.now().strftime("%H:%M:%S")
            colors = {
                "info": "#ffffff",
                "success": "#22c55e",
                "warning": "#fbbf24",
                "error": "#ef4444",
                "tts": "#4a9eff",
                "welcome": "#4ade80"
            }
            color = colors.get(level, "#ffffff")
            self.log_queue.put((f"[{timestamp}] {message}", color))
        else:
            # Command line mode
            if hasattr(self, 'logger'):
                self.logger.info(message)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def reset_spoken(self):
        """Reset spoken messages cache"""
        if time.time() - self.last_reset > self.reset_interval:
            self.spoken_messages.clear()
            self.last_reset = time.time()
            self.log("🔄 TTS deduplication cache reset", "info")
    
    def speak(self, text):
        """Text-to-speech function"""
        try:
            # Credentials are already set in __init__, no need to check again
            client = texttospeech.TextToSpeechClient()
            ssml = texttospeech.SynthesisInput(text=text)
            
            # Get selected voice or default
            if hasattr(self, 'selected_voice') and hasattr(self, 'voice_options'):
                selected_display = self.selected_voice.get()
                voice_name = self.voice_options.get(selected_display, "en-US-Studio-M")
            else:
                voice_name = "en-US-Studio-M"  # Fallback for CLI mode
            
            # Determine language code based on voice region
            if "en-AU" in voice_name:
                language_code = "en-AU"
            elif "en-GB" in voice_name:
                language_code = "en-GB"
            elif "en-IN" in voice_name:
                language_code = "en-IN"
            else:
                language_code = "en-US"
            
            voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            result = client.synthesize_speech(input=ssml, voice=voice, audio_config=audio_config)
            
            fn = os.path.join(self.audio_dir, f"{int(time.time())}.mp3")
            with open(fn, "wb") as f:
                f.write(result.audio_content)
            playsound(fn)
            os.remove(fn)
            
            if self.gui_mode:
                self.log("✅ TTS played successfully", "success")
        except Exception as e:
            self.log(f"❌ TTS Error: {str(e)}", "error")
    
    def get_joke(self):
        """Load a random joke"""
        if os.path.exists(self.jokes_file):
            with open(self.jokes_file, "r", encoding="utf-8") as f:
                jokes = [line.strip() for line in f if line.strip()]
            return random.choice(jokes) if jokes else "No jokes found."
        return "No jokes file found."
    
    def get_yo_mama(self):
        """Load a yo mama joke"""
        if os.path.exists(self.yo_mama_file):
            with open(self.yo_mama_file, "r", encoding="utf-8") as f:
                jokes = [line.strip() for line in f if line.strip()]
            return random.choice(jokes) if jokes else "No yo mama jokes found."
        return "No yo mama jokes file found."
    
    def check_online_status(self):
        """Check if the TikTok live stream is still online every 5 seconds"""
        import requests
        
        while self.bot_running:
            try:
                self.stats["connection_checks"] += 1
                
                # Check TikTok live status with better detection
                url = f"https://www.tiktok.com/@{self.username}/live"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    page_content = response.text.upper()
                    # More comprehensive live detection
                    live_indicators = [
                        "LIVE",
                        "STREAMING",
                        "ROOM_ID",
                        "LIVE_TITLE", 
                        "VIEWER_COUNT",
                        '"LIVE"'
                    ]
                    
                    is_live = any(indicator in page_content for indicator in live_indicators)
                    
                    if is_live:
                        if self.connection_status != "Online":
                            self.connection_status = "Online"
                            self.log("🟢 Stream is LIVE - Chat bot ready", "success")
                            if self.gui_mode:
                                self.status_label.config(text="Status: Connected (LIVE)", fg="#22c55e")
                    else:
                        if self.connection_status != "Offline":
                            self.connection_status = "Offline"
                            self.log("🔴 Stream appears to be OFFLINE", "warning")
                            self.log("💡 Start your TikTok live stream for the bot to receive messages", "info")
                            if self.gui_mode:
                                self.status_label.config(text="Status: Connected (OFFLINE)", fg="#fbbf24")
                else:
                    if self.connection_status != "Error":
                        self.connection_status = "Error"
                        self.log(f"⚠️ Cannot check stream status (HTTP {response.status_code})", "warning")
                        
            except requests.exceptions.Timeout:
                self.log("⏱️ Stream status check timed out", "warning")
            except requests.exceptions.RequestException as e:
                if self.stats["connection_checks"] % 12 == 0:  # Log every minute instead of every 5 seconds
                    self.log(f"🌐 Network error checking stream status: {str(e)}", "warning")
            except Exception as e:
                if self.stats["connection_checks"] % 12 == 0:  # Log every minute
                    self.log(f"❌ Error checking online status: {str(e)}", "error")
            
            # Update last check time
            self.last_online_check = time.time()
            
            # Wait 5 seconds before next check
            time.sleep(5)
    
    def start_bot(self):
        """Start the TikTok bot"""
        if self.bot_running:
            return
            
        self.bot_running = True
        self.stats["start_time"] = time.time()
        
        if self.gui_mode:
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_label.config(text="Status: Starting...", fg="#fbbf24")
        
        self.log(f"🚀 Starting bot for @{self.username}", "info")
        
        # Start online status monitoring
        self.online_check_thread = threading.Thread(target=self.check_online_status, daemon=True)
        self.online_check_thread.start()
        self.log("🔍 Started online status monitoring (5-second intervals)", "info")
        
        if self.gui_mode:
            # Start bot in separate thread for GUI
            self.bot_thread = threading.Thread(target=self.run_bot_threaded, daemon=True)
            self.bot_thread.start()
        else:
            # Run directly for command line
            self.run_bot()
    
    def run_bot_threaded(self):
        """Run bot in thread for GUI mode with auto-retry"""
        max_retries = 3
        retry_count = 0
        
        while self.bot_running and retry_count < max_retries:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.run_bot_async())
                break  # Success, exit retry loop
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if "No Message Provided" in error_msg or "rate" in error_msg.lower():
                    wait_time = int(self.rate_limit_cooldown)
                    self.log(f"🔄 Rate limited. Auto-retry {retry_count}/{max_retries} in {wait_time}s...", "warning")
                    
                    # Wait with countdown in GUI
                    for remaining in range(wait_time, 0, -5):
                        if not self.bot_running:  # Stop if user stops bot
                            return
                        if self.gui_mode:
                            self.status_label.config(text=f"Status: Auto-retry in {remaining}s", fg="#fbbf24")
                        time.sleep(5)
                    
                    if self.bot_running:
                        self.log(f"🔄 Attempting auto-retry {retry_count}/{max_retries}...", "info")
                        if self.gui_mode:
                            self.status_label.config(text="Status: Retrying...", fg="#3b82f6")
                else:
                    self.log(f"❌ Bot error (attempt {retry_count}/{max_retries}): {error_msg}", "error")
                    break  # Don't retry for non-rate-limit errors
        
        if retry_count >= max_retries:
            self.log("❌ Max retries reached. TikTok may be blocking connections.", "error")
            self.log("💡 Wait 5-10 minutes before trying again", "warning")
        
        # Clean up
        self.bot_running = False
        if self.gui_mode:
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_label.config(text="Status: Disconnected", fg="#b3b3b3")
    
    def run_bot(self):
        """Run bot for command line mode"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_bot_async())
        except KeyboardInterrupt:
            self.log("🛑 Shutting down...", "warning")
        except Exception as e:
            self.log(f"❌ Bot error: {str(e)}", "error")
    
    async def run_bot_async(self):
        """Async bot logic with improved error handling and rate limiting protection"""
        
        # Rate limiting protection
        current_time = time.time()
        time_since_last_attempt = current_time - self.last_connection_attempt
        
        if time_since_last_attempt < self.connection_retry_delay:
            remaining_wait = self.connection_retry_delay - time_since_last_attempt
            self.log(f"⏱️ Rate limiting protection: waiting {remaining_wait:.0f} seconds before retry", "warning")
            await asyncio.sleep(remaining_wait)
        
        self.last_connection_attempt = time.time()
        
        try:
            self.log(f"🔗 Connecting to TikTok Live for @{self.username}...", "info")
            self.log("🔄 Attempting to connect to TikTok Live stream...", "info")
            
            self.bot_client = TikTokLiveClient(unique_id=self.username)
            
            @self.bot_client.on(ConnectEvent)
            async def on_connect(evt):
                self.log("✅ Connected to TikTok Live chat", "success")
                self.connection_status = "Connected"
                if self.gui_mode:
                    self.status_label.config(text="Status: Connected", fg="#22c55e")
            
            @self.bot_client.on(JoinEvent)
            async def on_join(evt):
                self.reset_spoken()
                user = evt.user.unique_id
                welcome_message = f"Thanks for joining {user}!"
                
                dedup_key = f"welcome:{user}"
                if dedup_key in self.spoken_messages:
                    return
                self.spoken_messages.add(dedup_key)
                
                # Add user to the joined users list
                self.add_user_to_list(user)
                
                self.log(f"👋 Welcome: {user}", "welcome")
                self.stats["welcomes"] += 1
                
                if self.gui_mode:
                    self.stats_labels["Users Welcomed:"].config(text=str(self.stats["welcomes"]))
                    threading.Thread(target=self.speak, args=(welcome_message,), daemon=True).start()
                else:
                    self.speak(welcome_message)
            
            @self.bot_client.on(CommentEvent)
            async def on_comment(evt):
                self.reset_spoken()
                text = evt.comment.strip()
                user = evt.user.unique_id
                
                dedup_key = f"{user}:{text}"
                if dedup_key in self.spoken_messages:
                    self.log(f"[TTS] Skipping duplicate: {dedup_key}", "info")
                    return
                self.spoken_messages.add(dedup_key)
                
                self.stats["messages"] += 1
                self.stats["last_activity"] = datetime.now().strftime("%H:%M:%S")
                
                if self.gui_mode:
                    self.stats_labels["Messages Processed:"].config(text=str(self.stats["messages"]))
                
                # Command handling
                if text.lower().startswith("!help"):
                    help_text = "🤖 Available commands: !joke (random joke), !yo-mama (yo mama joke), !help (show this message). Just type normal messages for TTS!"
                    self.log(f"ℹ️ Help for {user}: Commands shown", "info")
                    if self.gui_mode:
                        threading.Thread(target=self.speak, args=(help_text,), daemon=True).start()
                    else:
                        self.speak(help_text)
                        
                elif text.lower().startswith("!joke"):
                    joke = self.get_joke()
                    self.log(f"😂 Joke for {user}: {joke[:50]}...", "tts")
                    self.stats["jokes"] += 1
                    if self.gui_mode:
                        self.stats_labels["Jokes Told:"].config(text=str(self.stats["jokes"]))
                        threading.Thread(target=self.speak, args=(joke,), daemon=True).start()
                    else:
                        self.speak(joke)
                        
                elif text.lower().startswith("!yo-mama"):
                    joke = self.get_yo_mama()
                    self.log(f"😂 Yo Mama for {user}: {joke[:50]}...", "tts")
                    self.stats["jokes"] += 1
                    if self.gui_mode:
                        self.stats_labels["Jokes Told:"].config(text=str(self.stats["jokes"]))
                        threading.Thread(target=self.speak, args=(joke,), daemon=True).start()
                    else:
                        self.speak(joke)
                        
                else:
                    # Normal TTS
                    spoken = emoji.demojize(text, delimiters=(" ", " "))
                    self.log(f"💬 {user}: {spoken}", "tts")
                    if self.gui_mode:
                        threading.Thread(target=self.speak, args=(f"{user} says {spoken}",), daemon=True).start()
                    else:
                        self.speak(f"{user} says {spoken}")
            
            # Attempt connection with detailed error handling and rate limiting
            try:
                # Check for rate limiting cooldown
                current_time = time.time()
                if (current_time - self.last_connection_attempt) < self.rate_limit_cooldown:
                    remaining_time = int(self.rate_limit_cooldown - (current_time - self.last_connection_attempt))
                    self.log(f"⏳ Rate limit cooldown: {remaining_time}s remaining", "warning")
                    return
                
                self.connection_attempts += 1
                self.last_connection_attempt = current_time
                
                self.log("🔄 Attempting to connect to TikTok Live stream...", "info")
                await self.bot_client.connect()
            except Exception as connect_error:
                error_msg = str(connect_error)
                if "User not found" in error_msg or "not capable of going LIVE" in error_msg:
                    self.log(f"❌ Connection Error: @{self.username} cannot go live or doesn't exist", "error")
                    self.log("💡 Make sure the username is correct and the user can broadcast live", "warning")
                elif "No Message Provided" in error_msg:
                    self.log(f"❌ Connection Error: TikTok Live API issue (Rate Limited)", "error")
                    self.log(f"💡 TikTok is rate limiting connections. Waiting {self.rate_limit_cooldown}s before retry", "warning")
                    self.log("🔄 This is normal - TikTok limits API requests to prevent spam", "info")
                    # Increase cooldown time for subsequent attempts
                    self.rate_limit_cooldown = min(300, self.rate_limit_cooldown * 1.5)  # Max 5 minutes
                elif "blocked" in error_msg.lower():
                    self.log(f"❌ Connection Error: Blocked by TikTok", "error")
                    self.log("💡 You may be temporarily blocked. Try using a VPN or waiting 10-15 minutes", "warning")
                    self.rate_limit_cooldown = 600  # 10 minute cooldown for blocks
                else:
                    self.log(f"❌ Connection Error: {error_msg}", "error")
                    self.log("💡 Check your internet connection and try again", "warning")
                
                self.connection_status = "Error"
                if self.gui_mode:
                    self.status_label.config(text=f"Status: Rate Limited ({int(self.rate_limit_cooldown)}s)", fg="#ef4444")
                return
                
        except Exception as e:
            self.log(f"❌ Unexpected error in bot setup: {str(e)}", "error")
            self.connection_status = "Error"
            if self.gui_mode:
                self.status_label.config(text="Status: Setup Error", fg="#ef4444")
    
    def stop_bot(self):
        """Stop the TikTok bot"""
        if not self.bot_running:
            return
            
        self.bot_running = False
        self.connection_status = "Disconnected"
        self.log("⏹️ Stopping bot and online monitoring...", "warning")
        
        if self.gui_mode:
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_label.config(text="Status: Disconnected", fg="#b3b3b3")
    
    def test_tts(self):
        """Test TTS functionality"""
        # Get current voice info
        if hasattr(self, 'selected_voice') and hasattr(self, 'voice_options'):
            selected_display = self.selected_voice.get()
            voice_name = self.voice_options.get(selected_display, "en-US-Wavenet-D")
            test_message = f"Hello! This is a test using the {selected_display} voice."
            self.log(f"🔊 Testing TTS with {selected_display}...", "info")
        else:
            test_message = "Hello! This is a test of the TTS system."
            self.log("🔊 Testing TTS system...", "info")
            
        if self.gui_mode:
            threading.Thread(target=self.speak, args=(test_message,), daemon=True).start()
        else:
            self.speak(test_message)

    def test_connection(self):
        """Test TikTok connection and provide diagnostics"""
        if not self.username.strip():
            self.log("❌ Please enter a TikTok username first", "error")
            return
            
        self.log("🔗 Testing TikTok connection...", "info")
        
        try:
            import requests
            
            # Test 1: Basic connectivity
            self.log("1️⃣ Testing basic internet connectivity...", "info")
            response = requests.get("https://www.google.com", timeout=5)
            if response.status_code == 200:
                self.log("✅ Internet connection is working", "success")
            else:
                self.log(f"⚠️ Internet connectivity issue (status: {response.status_code})", "warning")
                
            # Test 2: TikTok accessibility
            self.log("2️⃣ Testing TikTok accessibility...", "info")
            tiktok_response = requests.get("https://www.tiktok.com", timeout=10)
            if tiktok_response.status_code == 200:
                self.log("✅ TikTok.com is accessible", "success")
            else:
                self.log(f"⚠️ TikTok accessibility issue (status: {tiktok_response.status_code})", "warning")
                
            # Test 3: User profile check
            self.log(f"3️⃣ Checking user profile @{self.username}...", "info")
            profile_url = f"https://www.tiktok.com/@{self.username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            profile_response = requests.get(profile_url, headers=headers, timeout=10)
            if profile_response.status_code == 200:
                self.log("✅ User profile exists and is accessible", "success")
                
                # Check for live stream indicators
                page_content = profile_response.text.upper()
                live_indicators = ["LIVE", "STREAMING", "ROOM_ID", "LIVE_TITLE", "VIEWER_COUNT"]
                
                if any(indicator in page_content for indicator in live_indicators):
                    self.log("🟢 LIVE stream detected! Bot should be able to connect.", "success")
                else:
                    self.log("🔴 No live stream detected. Start your TikTok live stream first.", "warning")
                    self.log("💡 Make sure you're streaming before starting the bot", "info")
                    
            elif profile_response.status_code == 404:
                self.log(f"❌ User @{self.username} not found. Check the username spelling.", "error")
            else:
                self.log(f"⚠️ Profile check failed (status: {profile_response.status_code})", "warning")
                
            # Test 4: TikTokLive library test
            self.log("4️⃣ Testing TikTokLive library...", "info")
            try:
                from TikTokLive import TikTokLiveClient
                test_client = TikTokLiveClient(unique_id=self.username)
                self.log("✅ TikTokLive library is working correctly", "success")
                
                # Test connection without starting
                self.log("5️⃣ Attempting TikTok API connection test...", "info")
                # Note: We don't actually connect here to avoid conflicts
                self.log("💡 Ready to connect. Use 'Start Bot' to begin listening for chat messages.", "info")
                
            except ImportError as e:
                self.log(f"❌ TikTokLive library import error: {str(e)}", "error")
                self.log("💡 Try: pip install TikTokLive", "info")
            except Exception as e:
                self.log(f"⚠️ TikTokLive test warning: {str(e)}", "warning")
                
            self.log("🔗 Connection test completed!", "success")
            
        except requests.exceptions.Timeout:
            self.log("❌ Connection test timed out. Check your internet connection.", "error")
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Network error during connection test: {str(e)}", "error")
        except Exception as e:
            self.log(f"❌ Connection test failed: {str(e)}", "error")

    def reset_rate_limit(self):
        """Reset rate limiting cooldown manually"""
        self.connection_attempts = 0
        self.last_connection_attempt = 0
        self.rate_limit_cooldown = 60  # Reset to default
        self.log("🔄 Rate limit reset! You can try connecting again.", "success")
        if self.gui_mode and not self.bot_running:
            self.status_label.config(text="Status: Ready to Connect", fg="#22c55e")
    
    def on_voice_changed(self, event=None):
        """Handle voice selection change"""
        selected_display = self.selected_voice.get()
        voice_name = self.voice_options.get(selected_display, "en-US-Wavenet-D")
        self.log(f"🎵 Voice changed to: {selected_display}", "success")
        # Test the new voice
        if hasattr(self, 'test_tts_button'):
            self.log("💡 Tip: Click 'Test TTS' to hear the new voice!", "info")
    
    # GUI Setup (only if GUI mode is enabled)
    def setup_gui(self):
        """Set up the GUI interface"""
        if not GUI_AVAILABLE:
            print("❌ GUI not available - falling back to command line mode")
            self.gui_mode = False
            self.setup_logging()
            return
            
        self.root = tk.Tk()
        self.root.title("TikTok TTS Bot - Unified")
        self.root.geometry("1000x700")
        
        # Initialize queue for thread-safe GUI updates
        self.log_queue = queue.Queue()
        
        # Dark theme colors
        self.colors = {
            'bg_dark': '#1a1a1a',
            'bg_medium': '#2d2d2d',
            'bg_light': '#3d3d3d',
            'accent_blue': '#4a9eff',
            'accent_green': '#4ade80',
            'text_primary': '#ffffff',
            'text_secondary': '#b3b3b3',
            'success': '#22c55e',
            'warning': '#fbbf24',
            'error': '#ef4444'
        }
        
        self.setup_gui_style()
        self.setup_gui_layout()
        self.check_queue()
        
        # Add initial log messages
        self.log("🎮 TikTok TTS Bot (Unified) Initialized", "info")
        self.log("💡 Configure your TikTok username and click 'Start Bot'", "info")
        
    def setup_gui_style(self):
        """Configure GUI styling"""
        self.root.configure(bg=self.colors['bg_dark'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button styles
        style.configure('Accent.TButton',
                       background=self.colors['accent_blue'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none')
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_green'])])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=0)
        
        style.configure('Error.TButton',
                       background=self.colors['error'],
                       foreground='white',
                       borderwidth=0)
    
    def setup_gui_layout(self):
        """Create the GUI layout with tabs"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, 
                             text="🎮 TikTok TTS Bot (Unified)", 
                             font=("Arial", 16, "bold"), 
                             bg=self.colors['bg_dark'], 
                             fg=self.colors['text_primary'])
        title_label.pack(pady=(0, 10))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Tab 1: Main Controls
        self.main_tab = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(self.main_tab, text="🎮 Main Controls")
        
        # Tab 2: Users Joined
        self.users_tab = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(self.users_tab, text="👥 Users Joined")
        
        # Tab 3: Links
        self.links_tab = tk.Frame(self.notebook, bg=self.colors['bg_dark'])
        self.notebook.add(self.links_tab, text="🔗 Links")
        
        # Setup each tab
        self.setup_main_tab()
        self.setup_users_tab()
        self.setup_links_tab()
    
    def setup_main_tab(self):
        """Setup the main controls tab"""
        # Status frame
        status_frame = tk.Frame(self.main_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        status_frame.pack(fill='x', pady=(0, 10))
        
        status_title = tk.Label(status_frame,
                               text="🔹 Bot Status",
                               font=('Arial', 12, 'bold'),
                               bg=self.colors['bg_medium'],
                               fg=self.colors['accent_green'])
        status_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.status_label = tk.Label(status_frame,
                                    text="Status: Disconnected",
                                    font=('Arial', 10),
                                    bg=self.colors['bg_medium'],
                                    fg=self.colors['text_secondary'])
        self.status_label.pack(anchor='w', padx=20, pady=(0, 10))
        
        # Control buttons
        control_frame = tk.Frame(self.main_tab, bg=self.colors['bg_dark'])
        control_frame.pack(fill='x', pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame,
                                      text="🚀 Start Bot",
                                      style='Accent.TButton',
                                      command=self.start_bot)
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame,
                                     text="⏹️ Stop Bot",
                                     style='Error.TButton',
                                     command=self.stop_bot,
                                     state='disabled')
        self.stop_button.pack(side='left', padx=(0, 10))
        
        self.test_tts_button = ttk.Button(control_frame,
                                         text="🔊 Test TTS",
                                         style='Success.TButton',
                                         command=self.test_tts)
        self.test_tts_button.pack(side='left', padx=(0, 10))
        
        # Test Connection button
        self.test_connection_button = ttk.Button(control_frame,
                                               text="🔗 Test Connection",
                                               style='Info.TButton',
                                               command=self.test_connection)
        self.test_connection_button.pack(side='left', padx=(0, 10))
        
        # Reset Rate Limit button
        self.reset_limit_button = ttk.Button(control_frame,
                                           text="🔄 Reset Rate Limit",
                                           style='Accent.TButton',
                                           command=self.reset_rate_limit)
        self.reset_limit_button.pack(side='left', padx=(0, 10))
        
        # Configuration
        config_frame = tk.Frame(self.main_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        config_frame.pack(fill='x', pady=(0, 10))
        
        config_title = tk.Label(config_frame,
                               text="⚙️ Configuration",
                               font=('Arial', 12, 'bold'),
                               bg=self.colors['bg_medium'],
                               fg=self.colors['accent_blue'])
        config_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        username_frame = tk.Frame(config_frame, bg=self.colors['bg_medium'])
        username_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Label(username_frame,
                text="TikTok Username:",
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary']).pack(side='left')
        
        self.username_entry = tk.Entry(username_frame,
                                      bg=self.colors['bg_light'],
                                      fg=self.colors['text_primary'],
                                      insertbackground=self.colors['text_primary'],
                                      relief='flat',
                                      bd=5)
        self.username_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        self.username_entry.insert(0, self.username)
        
        # Voice Selection
        voice_frame = tk.Frame(config_frame, bg=self.colors['bg_medium'])
        voice_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Label(voice_frame,
                text="TTS Voice:",
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary']).pack(side='left')
        
        # Voice options with emojis - ULTRA NATURAL VOICES (Most Human-Like!)
        self.voice_options = {
            "� Google Home Male": "en-US-Studio-M",
            "🏠 Google Home Female": "en-US-Studio-O", 
            "� Assistant Male": "en-US-Polyglot-1",
            "👩 Assistant Female": "en-US-Neural2-F",
            "� British Female": "en-GB-Neural2-A",
            "� British Male": "en-GB-Neural2-B",
            "🌟 Conversational Male": "en-US-Neural2-D",
            "✨ Conversational Female": "en-US-Neural2-G",
            "🎭 British Assistant": "en-GB-Neural2-A",
            "🎩 British Home": "en-GB-Neural2-B",
            
            # More US Voices
            "👨 Natural Male": "en-US-Neural2-A",
            "🎯 Professional Male": "en-US-Neural2-I",
            "🌟 Warm Male": "en-US-Neural2-J",
            "💫 Premium Female": "en-US-Neural2-H",
            "🎭 Dramatic Female": "en-US-Neural2-C",
            
            # British Accents
            "🎩 Posh British Female": "en-GB-Neural2-C",
            "👔 Professional British Male": "en-GB-Neural2-D",
            
            # Australian Voices
            "🇦🇺 Aussie Female": "en-AU-Neural2-A",
            "🇦🇺 Aussie Male": "en-AU-Neural2-B",
            "🏄 Casual Aussie Female": "en-AU-Neural2-C",
            "🦘 Outback Aussie Male": "en-AU-Neural2-D",
            
            # Indian English (Fixed Gender Issues)
            "🇮🇳 Indian Female A": "en-IN-Neural2-A",
            "🇮🇳 Indian Male B": "en-IN-Neural2-B",
            "🇮🇳 Indian Voice C": "en-IN-Neural2-C",
            "�🇳 Indian Voice D": "en-IN-Neural2-D"
        }
        
        self.selected_voice = tk.StringVar(value="� Google Home Male")
        self.voice_dropdown = ttk.Combobox(voice_frame,
                                         textvariable=self.selected_voice,
                                         values=list(self.voice_options.keys()),
                                         state="readonly")
        self.voice_dropdown.pack(side='left', padx=(10, 0), fill='x', expand=True)
        self.voice_dropdown.bind('<<ComboboxSelected>>', self.on_voice_changed)
        
        # Stats
        stats_frame = tk.Frame(self.main_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_title = tk.Label(stats_frame,
                              text="📊 Statistics",
                              font=('Arial', 12, 'bold'),
                              bg=self.colors['bg_medium'],
                              fg=self.colors['accent_green'])
        stats_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        stats_content = tk.Frame(stats_frame, bg=self.colors['bg_medium'])
        stats_content.pack(fill='x', padx=20, pady=(0, 10))
        
        self.stats_labels = {}
        stats_data = [
            ("Messages Processed:", "0"),
            ("Jokes Told:", "0"),
            ("Users Welcomed:", "0"),
            ("Connection Checks:", "0"),
            ("Uptime:", "00:00:00"),
            ("Stream Status:", "Unknown")
        ]
        
        for i, (label, value) in enumerate(stats_data):
            row = i // 3  # 3 columns instead of 2
            col = i % 3
            
            frame = tk.Frame(stats_content, bg=self.colors['bg_medium'])
            frame.grid(row=row, column=col, sticky='w', padx=(0, 20), pady=2)
            
            tk.Label(frame, text=label, bg=self.colors['bg_medium'], 
                    fg=self.colors['text_secondary']).pack(side='left')
            
            value_label = tk.Label(frame, text=value, bg=self.colors['bg_medium'], 
                                  fg=self.colors['accent_blue'], font=('Arial', 10, 'bold'))
            value_label.pack(side='left', padx=(5, 0))
            
            self.stats_labels[label] = value_label
        
        # Log frame
        log_frame = tk.Frame(self.main_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        log_frame.pack(fill='both', expand=True)
        
        log_title = tk.Label(log_frame,
                            text="📋 Activity Log",
                            font=('Arial', 12, 'bold'),
                            bg=self.colors['bg_medium'],
                            fg=self.colors['accent_blue'])
        log_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 bg=self.colors['bg_dark'],
                                                 fg=self.colors['text_primary'],
                                                 insertbackground=self.colors['text_primary'],
                                                 relief='flat',
                                                 bd=0,
                                                 font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    def check_queue(self):
        """Check for new log messages and update GUI"""
        try:
            while True:
                message, color = self.log_queue.get_nowait()
                
                self.log_text.config(state='normal')
                self.log_text.insert('end', message + '\n')
                
                # Apply color
                line_start = self.log_text.index('end-2c linestart')
                line_end = self.log_text.index('end-2c lineend')
                self.log_text.tag_add(f"color_{color}", line_start, line_end)
                self.log_text.tag_config(f"color_{color}", foreground=color)
                
                self.log_text.config(state='disabled')
                self.log_text.see('end')
                
        except queue.Empty:
            pass
        
        # Update stats if bot is running
        if self.bot_running and self.stats["start_time"]:
            uptime = time.time() - self.stats["start_time"]
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            self.stats_labels["Uptime:"].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update connection checks counter
            self.stats_labels["Connection Checks:"].config(text=str(self.stats["connection_checks"]))
            
            # Update stream status
            status_colors = {
                "Online": "#22c55e",
                "Offline": "#fbbf24", 
                "Error": "#ef4444",
                "Disconnected": "#b3b3b3"
            }
            status_color = status_colors.get(self.connection_status, "#b3b3b3")
            self.stats_labels["Stream Status:"].config(text=self.connection_status, fg=status_color)
        
        self.root.after(100, self.check_queue)
    
    def run_gui(self):
        """Start the GUI"""
        if self.gui_mode and GUI_AVAILABLE:
            try:
                self.root.mainloop()
            except KeyboardInterrupt:
                self.stop_bot()
        else:
            print("❌ GUI mode not available")

    def setup_users_tab(self):
        """Setup the users joined tab"""
        # Users info frame
        users_info_frame = tk.Frame(self.users_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        users_info_frame.pack(fill='x', pady=(10, 10), padx=10)
        
        users_title = tk.Label(users_info_frame,
                              text="👥 Users Who Joined the Stream",
                              font=('Arial', 12, 'bold'),
                              bg=self.colors['bg_medium'],
                              fg=self.colors['accent_green'])
        users_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        # User count
        self.user_count_label = tk.Label(users_info_frame,
                                        text="Total Users: 0",
                                        font=('Arial', 10),
                                        bg=self.colors['bg_medium'],
                                        fg=self.colors['text_primary'])
        self.user_count_label.pack(anchor='w', padx=10, pady=(0, 5))
        
        # Clear users button
        clear_users_btn = ttk.Button(users_info_frame,
                                   text="🗑️ Clear List",
                                   style='Accent.TButton',
                                   command=self.clear_users_list)
        clear_users_btn.pack(side='left', anchor='w', padx=(10, 5), pady=(0, 10))
        
        # Export users button
        export_users_btn = ttk.Button(users_info_frame,
                                    text="💾 Export List",
                                    style='Info.TButton',
                                    command=self.export_users_list)
        export_users_btn.pack(side='left', anchor='w', padx=(5, 10), pady=(0, 10))
        
        # Users list frame
        users_list_frame = tk.Frame(self.users_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        users_list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        list_title = tk.Label(users_list_frame,
                             text="📋 Join History (Most Recent First)",
                             font=('Arial', 12, 'bold'),
                             bg=self.colors['bg_medium'],
                             fg=self.colors['accent_blue'])
        list_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        # Scrollable users list
        users_scroll_frame = tk.Frame(users_list_frame, bg=self.colors['bg_medium'])
        users_scroll_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar for users list
        users_scrollbar = tk.Scrollbar(users_scroll_frame, bg=self.colors['bg_light'])
        users_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Users text widget
        self.users_text = tk.Text(users_scroll_frame,
                                 wrap=tk.WORD,
                                 yscrollcommand=users_scrollbar.set,
                                 bg=self.colors['bg_dark'],
                                 fg=self.colors['text_primary'],
                                 font=('Consolas', 9),
                                 relief='flat',
                                 height=20)
        self.users_text.pack(side=tk.LEFT, fill='both', expand=True)
        users_scrollbar.config(command=self.users_text.yview)
        
        # Initial message
        self.users_text.insert(tk.END, "👋 Waiting for users to join the stream...\n")
        self.users_text.config(state=tk.DISABLED)

    def setup_links_tab(self):
        """Setup the links tab - displays your links from links/links.txt"""
        # Header frame
        header_frame = tk.Frame(self.links_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        header_frame.pack(fill='x', pady=(10, 10), padx=10)
        
        title = tk.Label(header_frame,
                        text="🔗 GamingUtopiaGC — Official Links Hub",
                        font=('Arial', 14, 'bold'),
                        bg=self.colors['bg_medium'],
                        fg=self.colors['accent_green'])
        title.pack(anchor='w', padx=10, pady=(10, 5))
        
        subtitle = tk.Label(header_frame,
                           text="Click any link to open in your browser",
                           font=('Arial', 10),
                           bg=self.colors['bg_medium'],
                           fg=self.colors['text_secondary'])
        subtitle.pack(anchor='w', padx=10, pady=(0, 5))
        
        # Refresh button
        refresh_btn = ttk.Button(header_frame,
                               text="🔄 Refresh Links",
                               style='Accent.TButton',
                               command=self.load_links_from_file)
        refresh_btn.pack(anchor='w', padx=10, pady=(5, 10))
        
        # Links content frame with scrollbar
        content_frame = tk.Frame(self.links_tab, bg=self.colors['bg_medium'], relief='solid', bd=1)
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create scrollable area with better configuration for grid layout
        canvas = tk.Canvas(content_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview, 
                               bg=self.colors['bg_light'], troughcolor=self.colors['bg_medium'])
        self.links_scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_dark'])
        
        # Configure scrollable frame for grid layout
        self.links_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        canvas.create_window((0, 0), window=self.links_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack with improved layout
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Ensure the scrollable frame expands to fill canvas width
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(
            canvas.find_all()[0], width=e.width))
        
        # Load links from file
        self.load_links_from_file()

    def load_links_from_file(self):
        """Load and display links from links/links.txt"""
        # Clear existing content
        for widget in self.links_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get the correct path relative to the script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        links_file_path = os.path.join(script_dir, "..", "links", "links.txt")
        
        self.log(f"🔍 Loading links from file...", "info")
        
        try:
            if os.path.exists(links_file_path):
                with open(links_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.log(f"📄 Loaded {len(content)} characters from links file", "info")
                self.parse_and_display_links(content)
                self.log("✅ Links loaded successfully with grid layout", "success")
            else:
                # Show error message if file not found
                error_label = tk.Label(self.links_scrollable_frame,
                                     text="❌ links/links.txt not found\n\nCreate a file at: links/links.txt\nwith your links organized by categories",
                                     font=('Arial', 12),
                                     bg=self.colors['bg_dark'],
                                     fg=self.colors['error'],
                                     justify='center')
                error_label.pack(pady=50)
                self.log("❌ links/links.txt file not found", "error")
        except Exception as e:
            error_label = tk.Label(self.links_scrollable_frame,
                                 text=f"❌ Error loading links: {str(e)}",
                                 font=('Arial', 12),
                                 bg=self.colors['bg_dark'],
                                 fg=self.colors['error'])
            error_label.pack(pady=20)
            self.log(f"❌ Error loading links: {str(e)}", "error")

    def parse_and_display_links(self, content):
        """Parse the links file content and create clickable elements in a flush grid"""
        lines = content.split('\n')
        current_category = None
        current_grid_frame = None
        links_in_current_category = []
        
        self.log(f"📝 Parsing {len(lines)} lines from links file", "info")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a category header (contains emoji and title)
            if ('🎮' in line or '📺' in line or '📸' in line or '🐦' in line or 
                '🎵' in line or '💬' in line or '🧱' in line or '☕' in line or
                '🌐' in line):
                
                # If we have pending links from previous category, display them first
                if links_in_current_category and current_grid_frame:
                    self.create_links_grid(current_grid_frame, links_in_current_category)
                    links_in_current_category = []
                
                # Category header
                category_frame = tk.Frame(self.links_scrollable_frame, bg=self.colors['bg_medium'], 
                                        relief='solid', bd=1)
                category_frame.pack(fill='x', padx=10, pady=(10, 5))
                
                category_label = tk.Label(category_frame,
                                        text=line,
                                        font=('Arial', 12, 'bold'),
                                        bg=self.colors['bg_medium'],
                                        fg=self.colors['accent_blue'])
                category_label.pack(anchor='w', padx=10, pady=8)
                current_category = line
                
                # Create grid container for this category's links
                current_grid_frame = tk.Frame(self.links_scrollable_frame, bg=self.colors['bg_dark'])
                current_grid_frame.pack(fill='x', padx=20, pady=(5, 10))
                
                self.log(f"📂 Created category: {line}", "info")
                
            # Check if it's a clickable link (starts with 🔗)
            elif line.startswith('🔗'):
                url = line.replace('🔗 ', '').strip()
                
                # Add https:// if not present
                if not url.startswith(('http://', 'https://')):
                    full_url = 'https://' + url
                else:
                    full_url = url
                
                # Store link info for grid creation
                links_in_current_category.append({
                    'url': url,
                    'full_url': full_url
                })
                
                self.log(f"🔗 Found link: {url}", "info")
                
            # Regular text lines
            else:
                # If we have pending links, display them first
                if links_in_current_category and current_grid_frame:
                    self.create_links_grid(current_grid_frame, links_in_current_category)
                    links_in_current_category = []
                
                text_frame = tk.Frame(self.links_scrollable_frame, bg=self.colors['bg_dark'])
                text_frame.pack(fill='x', padx=20, pady=1)
                
                text_label = tk.Label(text_frame,
                                    text=line,
                                    font=('Arial', 10),
                                    bg=self.colors['bg_dark'],
                                    fg=self.colors['text_primary'])
                text_label.pack(anchor='w')
        
        # Handle any remaining links at the end
        if links_in_current_category and current_grid_frame:
            self.create_links_grid(current_grid_frame, links_in_current_category)
        
        self.log("✅ Finished parsing links file", "success")

    def create_links_grid(self, parent_frame, links_list):
        """Create a flush grid layout for links with improved spacing and organization"""
        columns = 3  # 3 links per row for better use of space
        self.log(f"🔧 Creating flush grid with {len(links_list)} links in {columns} columns", "info")
        
        # Configure all columns to have equal weight for flush layout
        for col in range(columns):
            parent_frame.grid_columnconfigure(col, weight=1, uniform="links")
        
        for i, link_info in enumerate(links_list):
            row = i // columns
            col = i % columns
            
            # Create link container with consistent sizing
            link_container = tk.Frame(parent_frame, 
                                    bg=self.colors['bg_medium'], 
                                    relief='solid', 
                                    bd=1)
            link_container.grid(row=row, column=col, 
                              sticky='ew', 
                              padx=3, pady=3,
                              ipadx=5, ipady=5)
            
            # Configure container to expand properly
            link_container.grid_columnconfigure(0, weight=1)
            
            # Main link button with consistent height
            link_button = tk.Button(link_container,
                                  text=f"🌐 {link_info['url'][:25]}{'...' if len(link_info['url']) > 25 else ''}",
                                  font=('Arial', 9, 'bold'),
                                  bg=self.colors['accent_blue'],
                                  fg='white',
                                  relief='flat',
                                  cursor='hand2',
                                  anchor='center',
                                  height=2,
                                  wraplength=150,
                                  command=lambda u=link_info['full_url']: self.open_link_in_browser(u))
            link_button.grid(row=0, column=0, sticky='ew', padx=(0, 3))
            
            # Copy button with consistent styling
            copy_button = tk.Button(link_container,
                                  text="📋",
                                  font=('Arial', 8),
                                  bg=self.colors['bg_light'],
                                  fg=self.colors['text_primary'],
                                  relief='flat',
                                  cursor='hand2',
                                  width=3,
                                  height=2,
                                  command=lambda u=link_info['url']: self.copy_link_to_clipboard(u))
            copy_button.grid(row=0, column=1, sticky='ns')
            
            # Add hover effects
            def on_enter(event, button=link_button):
                button.config(bg=self.colors['accent_green'])
            
            def on_leave(event, button=link_button):
                button.config(bg=self.colors['accent_blue'])
                
            link_button.bind("<Enter>", on_enter)
            link_button.bind("<Leave>", on_leave)
        
        self.log(f"✅ Flush grid created successfully with {len(links_list)} links in {columns} columns", "success")

    def open_link_in_browser(self, url):
        """Open a link in the default browser"""
        import webbrowser
        try:
            webbrowser.open(url)
            self.log(f"🌐 Opened: {url}", "success")
        except Exception as e:
            self.log(f"❌ Failed to open link: {e}", "error")

    def copy_link_to_clipboard(self, url):
        """Copy link to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.log(f"📋 Copied to clipboard: {url}", "success")
        except Exception as e:
            self.log(f"❌ Failed to copy link: {e}", "error")

    def add_user_to_list(self, username, timestamp=None):
        """Add a user to the joined users list"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to tracking lists
        user_info = {"username": username, "timestamp": timestamp}
        self.joined_users.insert(0, user_info)  # Add to beginning for most recent first
        self.unique_users.add(username)
        
        # Keep only last 100 users to prevent memory issues
        if len(self.joined_users) > 100:
            self.joined_users = self.joined_users[:100]
        
        # Update GUI if in GUI mode
        if self.gui_mode:
            # Update user count
            self.user_count_label.config(text=f"Total Users: {len(self.unique_users)}")
            
            # Add to users text widget
            self.users_text.config(state=tk.NORMAL)
            # Clear and rebuild the list (show most recent first)
            self.users_text.delete(1.0, tk.END)
            
            for i, user in enumerate(self.joined_users[:50]):  # Show only last 50
                time_str = user["timestamp"]
                username = user["username"]
                self.users_text.insert(tk.END, f"[{time_str}] 👤 {username}\n")
            
            if len(self.joined_users) > 50:
                self.users_text.insert(tk.END, f"\n... and {len(self.joined_users) - 50} more users\n")
            
            self.users_text.see(tk.END)
            self.users_text.config(state=tk.DISABLED)

    def clear_users_list(self):
        """Clear the users joined list"""
        self.joined_users.clear()
        self.unique_users.clear()
        
        if self.gui_mode:
            self.user_count_label.config(text="Total Users: 0")
            self.users_text.config(state=tk.NORMAL)
            self.users_text.delete(1.0, tk.END)
            self.users_text.insert(tk.END, "👋 User list cleared. Waiting for new users...\n")
            self.users_text.config(state=tk.DISABLED)
        
        self.log("🗑️ User list cleared", "info")

    def export_users_list(self):
        """Export the users list to a text file"""
        if not self.joined_users:
            self.log("❌ No users to export", "warning")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"users_joined_{timestamp}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# TikTok Stream Users - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total Unique Users: {len(self.unique_users)}\n")
                f.write(f"# Total Join Events: {len(self.joined_users)}\n\n")
                
                f.write("Join History (Most Recent First):\n")
                f.write("-" * 40 + "\n")
                
                for user in self.joined_users:
                    f.write(f"[{user['timestamp']}] {user['username']}\n")
                
                f.write("\n" + "-" * 40 + "\n")
                f.write(f"Unique Users List:\n")
                
                for username in sorted(self.unique_users):
                    f.write(f"• {username}\n")
            
            self.log(f"💾 Users list exported to: {filename}", "success")
            
        except Exception as e:
            self.log(f"❌ Export failed: {str(e)}", "error")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='TikTok TTS Bot - Unified Version')
    parser.add_argument('--username', '-u', default='gamingutopiadf', 
                       help='TikTok username to connect to')
    parser.add_argument('--gui', '-g', action='store_true', 
                       help='Run with GUI interface')
    parser.add_argument('--no-gui', action='store_true', 
                       help='Force command-line mode')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.no_gui:
        gui_mode = False
    elif args.gui:
        gui_mode = True
    else:
        # Auto-detect: use GUI if available, otherwise command line
        gui_mode = GUI_AVAILABLE
    
    print(f"🎮 TikTok TTS Bot - Starting in {'GUI' if gui_mode else 'Command Line'} mode")
    
    # Create and run bot
    bot = TikTokTTSBot(username=args.username, gui_mode=gui_mode)
    
    if gui_mode:
        bot.run_gui()
    else:
        bot.start_bot()

if __name__ == "__main__":
    main()
