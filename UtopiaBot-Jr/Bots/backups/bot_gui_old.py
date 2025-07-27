import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
import sys
import asyncio
import logging
from datetime import datetime
import queue
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, JoinEvent
from google.cloud import texttospeech
from playsound import playsound
import emoji
import random

class TikTokBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TikTok TTS Bot - Dark Theme")
        self.root.geometry("1000x700")
        
        # Initialize queue first for thread-safe GUI updates
        self.log_queue = queue.Queue()
        
        # Dark theme colors with blue and green accents
        self.colors = {
            'bg_dark': '#1a1a1a',           # Dark background
            'bg_medium': '#2d2d2d',         # Medium background
            'bg_light': '#3d3d3d',          # Light background
            'accent_blue': '#4a9eff',       # Blue accent
            'accent_green': '#4ade80',      # Green accent
            'text_primary': '#ffffff',      # Primary text
            'text_secondary': '#b3b3b3',    # Secondary text
            'success': '#22c55e',           # Success green
            'warning': '#fbbf24',           # Warning yellow
            'error': '#ef4444'              # Error red
        }
        
        self.setup_style()
        self.setup_gui()
        self.setup_bot()
        self.check_queue()
        
    def setup_style(self):
        """Configure dark theme styling"""
        self.root.configure(bg=self.colors['bg_dark'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styles
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
                       borderwidth=0,
                       focuscolor='none')
        
        style.configure('Error.TButton',
                       background=self.colors['error'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none')
        
    def setup_gui(self):
        """Create the GUI layout"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="🎮 TikTok TTS Bot Control Panel",
                              font=('Arial', 20, 'bold'),
                              bg=self.colors['bg_dark'],
                              fg=self.colors['accent_blue'])
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg=self.colors['bg_medium'], relief='solid', bd=1)
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
        
        # Control buttons frame
        control_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
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
        
        # Configuration frame
        config_frame = tk.Frame(main_frame, bg=self.colors['bg_medium'], relief='solid', bd=1)
        config_frame.pack(fill='x', pady=(0, 10))
        
        config_title = tk.Label(config_frame,
                               text="⚙️ Configuration",
                               font=('Arial', 12, 'bold'),
                               bg=self.colors['bg_medium'],
                               fg=self.colors['accent_blue'])
        config_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        # TikTok username
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
        self.username_entry.insert(0, "gamingutopiadf")
        
        # Stats frame
        stats_frame = tk.Frame(main_frame, bg=self.colors['bg_medium'], relief='solid', bd=1)
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
            ("Uptime:", "00:00:00")
        ]
        
        for i, (label, value) in enumerate(stats_data):
            row = i // 2
            col = i % 2
            
            frame = tk.Frame(stats_content, bg=self.colors['bg_medium'])
            frame.grid(row=row, column=col, sticky='w', padx=(0, 40), pady=2)
            
            tk.Label(frame, text=label, bg=self.colors['bg_medium'], 
                    fg=self.colors['text_secondary']).pack(side='left')
            
            value_label = tk.Label(frame, text=value, bg=self.colors['bg_medium'], 
                                  fg=self.colors['accent_blue'], font=('Arial', 10, 'bold'))
            value_label.pack(side='left', padx=(5, 0))
            
            self.stats_labels[label] = value_label
        
        # Log frame
        log_frame = tk.Frame(main_frame, bg=self.colors['bg_medium'], relief='solid', bd=1)
        log_frame.pack(fill='both', expand=True)
        
        log_title = tk.Label(log_frame,
                            text="📋 Activity Log",
                            font=('Arial', 12, 'bold'),
                            bg=self.colors['bg_medium'],
                            fg=self.colors['accent_blue'])
        log_title.pack(anchor='w', padx=10, pady=(10, 5))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 bg=self.colors['bg_dark'],
                                                 fg=self.colors['text_primary'],
                                                 insertbackground=self.colors['text_primary'],
                                                 relief='flat',
                                                 bd=0,
                                                 font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Add welcome message
        self.add_log("🎮 TikTok TTS Bot GUI Initialized", "info")
        self.add_log("💡 Configure your TikTok username and click 'Start Bot'", "info")
        
        # Initialize stats
        self.stats = {
            "messages": 0,
            "jokes": 0,
            "welcomes": 0,
            "start_time": None
        }
        
    def setup_bot(self):
        """Initialize bot variables"""
        self.bot_client = None
        self.bot_thread = None
        self.bot_running = False
        
        # TTS setup
        self.audio_dir = "tts_audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Set up Google Cloud credentials
        credentials_path = os.path.abspath("../key/ivory-oarlock-410506-865276f8b548.json")
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            self.add_log("✅ Google Cloud credentials loaded", "success")
        else:
            self.add_log("⚠️ Google Cloud credentials not found", "warning")
        
        # Deduplication
        self.spoken_messages = set()
        self.last_reset = time.time()
        self.reset_interval = 300  # 5 minutes
        
    def add_log(self, message, level="info"):
        """Add a log message to the queue for thread-safe GUI updates"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on level
        colors = {
            "info": self.colors['text_primary'],
            "success": self.colors['success'],
            "warning": self.colors['warning'],
            "error": self.colors['error'],
            "tts": self.colors['accent_blue'],
            "welcome": self.colors['accent_green']
        }
        
        color = colors.get(level, self.colors['text_primary'])
        self.log_queue.put((f"[{timestamp}] {message}", color))
        
    def check_queue(self):
        """Check for new log messages and update GUI"""
        try:
            while True:
                message, color = self.log_queue.get_nowait()
                
                # Insert message with color
                self.log_text.config(state='normal')
                self.log_text.insert('end', message + '\n')
                
                # Apply color to the last line
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
        
        self.root.after(100, self.check_queue)
        
    def speak(self, text):
        """Text-to-speech function"""
        try:
            # Ensure credentials are set
            credentials_path = os.path.abspath("../key/ivory-oarlock-410506-865276f8b548.json")
            if os.path.exists(credentials_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            else:
                self.add_log("❌ TTS Error: Credentials file not found", "error")
                return
                
            client = texttospeech.TextToSpeechClient()
            ssml = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-D")
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            result = client.synthesize_speech(input=ssml, voice=voice, audio_config=audio_config)
            
            fn = os.path.join(self.audio_dir, f"{int(time.time())}.mp3")
            with open(fn, "wb") as f:
                f.write(result.audio_content)
            playsound(fn)
            os.remove(fn)
            self.add_log("✅ TTS played successfully", "success")
        except Exception as e:
            self.add_log(f"❌ TTS Error: {str(e)}", "error")
            
    def get_joke(self):
        """Load a random joke"""
        jokes_file = "jokes/random/random.txt"
        if os.path.exists(jokes_file):
            with open(jokes_file, "r", encoding="utf-8") as f:
                jokes = [line.strip() for line in f if line.strip()]
            return random.choice(jokes) if jokes else "No jokes found."
        return "No jokes file found."
        
    def get_yo_mama(self):
        """Load a yo mama joke"""
        yo_mama_file = "jokes/yo_mama/yo_mama.txt"
        if os.path.exists(yo_mama_file):
            with open(yo_mama_file, "r", encoding="utf-8") as f:
                jokes = [line.strip() for line in f if line.strip()]
            return random.choice(jokes) if jokes else "No yo mama jokes found."
        return "No yo mama jokes file found."
        
    def reset_spoken(self):
        """Reset spoken messages cache"""
        if time.time() - self.last_reset > self.reset_interval:
            self.spoken_messages.clear()
            self.last_reset = time.time()
            self.add_log("🔄 TTS deduplication cache reset", "info")
            
    def start_bot(self):
        """Start the TikTok bot"""
        if self.bot_running:
            return
            
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a TikTok username")
            return
            
        self.bot_running = True
        self.stats["start_time"] = time.time()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Status: Starting...", fg=self.colors['warning'])
        
        self.add_log(f"🚀 Starting bot for @{username}", "info")
        
        # Start bot in separate thread
        self.bot_thread = threading.Thread(target=self.run_bot, args=(username,), daemon=True)
        self.bot_thread.start()
        
    def run_bot(self, username):
        """Run the bot in a separate thread"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.bot_client = TikTokLiveClient(unique_id=username)
            
            @self.bot_client.on(ConnectEvent)
            async def on_connect(evt):
                self.add_log("✅ Connected to TikTok Live chat", "success")
                self.status_label.config(text="Status: Connected", fg=self.colors['success'])
                
            @self.bot_client.on(JoinEvent)
            async def on_join(evt):
                self.reset_spoken()
                user = evt.user.unique_id
                welcome_message = f"Thanks for joining {user}!"
                
                dedup_key = f"welcome:{user}"
                if dedup_key in self.spoken_messages:
                    return
                self.spoken_messages.add(dedup_key)
                
                self.add_log(f"👋 Welcome: {user}", "welcome")
                self.stats["welcomes"] += 1
                self.stats_labels["Users Welcomed:"].config(text=str(self.stats["welcomes"]))
                
                threading.Thread(target=self.speak, args=(welcome_message,), daemon=True).start()
                
            @self.bot_client.on(CommentEvent)
            async def on_comment(evt):
                self.reset_spoken()
                text = evt.comment.strip()
                user = evt.user.unique_id
                
                dedup_key = f"{user}:{text}"
                if dedup_key in self.spoken_messages:
                    return
                self.spoken_messages.add(dedup_key)
                
                self.stats["messages"] += 1
                self.stats_labels["Messages Processed:"].config(text=str(self.stats["messages"]))
                
                if text.lower().startswith("!joke"):
                    joke = self.get_joke()
                    self.add_log(f"😂 Joke for {user}: {joke[:50]}...", "tts")
                    self.stats["jokes"] += 1
                    self.stats_labels["Jokes Told:"].config(text=str(self.stats["jokes"]))
                    threading.Thread(target=self.speak, args=(joke,), daemon=True).start()
                    
                elif text.lower().startswith("!yo-mama"):
                    joke = self.get_yo_mama()
                    self.add_log(f"😂 Yo Mama for {user}: {joke[:50]}...", "tts")
                    self.stats["jokes"] += 1
                    self.stats_labels["Jokes Told:"].config(text=str(self.stats["jokes"]))
                    threading.Thread(target=self.speak, args=(joke,), daemon=True).start()
                    
                else:
                    spoken = emoji.demojize(text, delimiters=(" ", " "))
                    self.add_log(f"💬 {user}: {spoken}", "tts")
                    threading.Thread(target=self.speak, args=(f"{user} says {spoken}",), daemon=True).start()
            
            loop.run_until_complete(self.bot_client.connect())
            
        except Exception as e:
            self.add_log(f"❌ Bot error: {str(e)}", "error")
            self.status_label.config(text="Status: Error", fg=self.colors['error'])
        finally:
            self.bot_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_label.config(text="Status: Disconnected", fg=self.colors['text_secondary'])
            
    def stop_bot(self):
        """Stop the TikTok bot"""
        if not self.bot_running:
            return
            
        self.bot_running = False
        self.add_log("⏹️ Stopping bot...", "warning")
        
        if self.bot_client:
            try:
                # This will stop the bot gracefully
                pass
            except:
                pass
                
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Status: Disconnected", fg=self.colors['text_secondary'])
        
    def test_tts(self):
        """Test TTS functionality"""
        test_message = "Hello! This is a test of the TTS system."
        self.add_log("🔊 Testing TTS system...", "info")
        threading.Thread(target=self.speak, args=(test_message,), daemon=True).start()
        
    def run(self):
        """Start the GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_bot()

if __name__ == "__main__":
    app = TikTokBotGUI()
    app.run()
