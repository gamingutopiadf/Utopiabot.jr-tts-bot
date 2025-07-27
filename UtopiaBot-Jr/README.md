# 🎮 TikTok TTS Bot - Complete User Guide

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/yourusername/UtopiaBot-Jr)](https://github.com/yourusername/UtopiaBot-Jr/issues)
[![GitHub Stars](https://img.shields.io/github/stars/yourusername/UtopiaBot-Jr)](https://github.com/yourusername/UtopiaBot-Jr/stargazers)

A powerful, unified TikTok Text-to-Speech bot with 24 natural voices that reads chat messages aloud, welcomes new viewers, and responds to commands. Features a beautiful GUI with tabbed interface and optimized performance.

## 🚀 Quick Start Guide

### 📋 Prerequisites
1. **Python 3.8+** installed on your system
2. **Google Cloud TTS credentials** - [See detailed setup guide below](#-google-cloud-tts-setup)
3. **TikTok account** that can go live
4. **Required packages** (install with: `pip install TikTokLive google-cloud-texttospeech playsound emoji`)

### 🎯 Launch Methods

#### GUI Mode (Recommended) - Full Featured Interface
```bash
cd Bots
python tiktok_bot_unified.py
```

#### Command Line Mode - Lightweight Terminal
```bash
cd Bots
python tiktok_bot_unified.py --no-gui
```

#### Custom Username
```bash
python tiktok_bot_unified.py --username "your_tiktok_username"
```

## 🎤 Voice Selection (24 Natural Voices)

The bot includes 24 ultra-natural voices across different regions:

### 🇺🇸 **US Voices** (Most Popular)
- 🏠 **Google Home Male/Female** - Smart speaker quality
- 👨 **Assistant Male/Female** - Professional AI voices  
- 🌟 **Conversational** - Natural conversation style
- 💫 **Premium** - High-quality studio voices

### 🇬🇧 **British Voices**
- 🎩 **Posh British** - Elegant accent
- 👔 **Professional British** - Business appropriate
- 🎭 **British Assistant** - Refined and clear

### 🇦🇺 **Australian Voices**
- 🦘 **Outback Aussie** - Authentic Australian accent
- 🏄 **Casual Aussie** - Relaxed and friendly

### 🇮🇳 **Indian English Voices**
- 🇮🇳 **Professional Indian** - Clear English with Indian accent

**Voice Quality**: All voices use Google Cloud's latest neural technology for maximum naturalness!

## 📁 Project Structure

```
UtopiaBot-Jr/
├── .github/                    # 🤖 GitHub templates and workflows
│   ├── ISSUE_TEMPLATE/        # Issue templates for bugs and features
│   ├── workflows/             # GitHub Actions CI/CD
│   └── pull_request_template.md
├── Bots/
│   └── tiktok_bot_unified.py  # 🎯 MAIN BOT FILE (Complete Solution)
├── jokes/                     # 😂 Joke collections
│   ├── random/random.txt      # Random jokes
│   └── yo_mama/yo_mama.txt    # Yo mama jokes
├── key/                       # 🔑 Google Cloud credentials folder
│   └── README.md              # Setup instructions
├── links/
│   └── links.txt             # 🔗 Your personal links for Links tab  
├── updates/
│   └── changelog.txt         # 📝 Development roadmap and updates
├── .gitignore                # Git ignore file
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
├── README.md                 # 📖 This guide
└── requirements.txt          # 📦 Python dependencies
```

## 🎮 Complete Feature Overview

### 🎯 **Core TTS Functionality**
- ✅ **24 Natural Voices**: Ultra-realistic Google Cloud neural voices
- ✅ **Smart Voice Detection**: Automatic language code selection per region
- ✅ **Optimized Performance**: Eliminated redundant credentials checking
- ✅ **Real-time Processing**: Instant chat-to-speech conversion
- ✅ **Message Deduplication**: Prevents spam (5-minute auto-reset)

### 👥 **User Interaction**  
- ✅ **Welcome Messages**: Automatic greetings for new viewers
- ✅ **User Tracking**: Live list of joined users with count
- ✅ **Command System**: Interactive joke commands
- ✅ **Live Statistics**: Real-time metrics and uptime

### 🖥️ **Interface Features**
- ✅ **Tabbed GUI**: Three organized tabs (Main, Users, Links)
- ✅ **Dark Theme**: Professional blue/green accent design
- ✅ **Links Tab**: 3-column grid of your personal links
- ✅ **Live Monitoring**: Stream status and connection health
- ✅ **CLI Support**: Full command-line compatibility

### 🔗 **Links Management**
- ✅ **File-Based**: Reads from `links/links.txt`
- ✅ **Clickable Grid**: 3-column flush layout
- ✅ **Copy Function**: Right-click to copy URLs
- ✅ **Hover Effects**: Interactive visual feedback
## � Step-by-Step Usage Guide

### 🎬 **Before You Start**
1. **Start Your TikTok Live Stream** - The bot only works when you're live!
2. **Check Your Username** - Make sure it's spelled correctly
3. **Verify Credentials** - Google Cloud TTS file should be in `key/` folder

### 🚀 **Getting Started**

#### **Method 1: GUI Mode (Recommended)**
1. Open terminal/command prompt
2. Navigate to the Bots folder: `cd Bots`
3. Run: `python tiktok_bot_unified.py`
4. **Configuration Tab (Main Controls)**:
   - Enter your TikTok username
   - Select your preferred voice from 24 options
   - Click "🔗 Test Connection" to verify setup
   - Click "🔊 Test TTS" to hear your selected voice
5. Click "🚀 Start Bot" to begin

#### **Method 2: Command Line Mode**
1. Navigate to Bots folder: `cd Bots`
2. Run: `python tiktok_bot_unified.py --no-gui`
3. The bot will use default settings and connect automatically

### 🎮 **Using the GUI Interface**

#### **📋 Tab 1: Main Controls**
- **🔹 Bot Status**: Shows connection status and stream detection
- **⚙️ Configuration**: 
  - Set TikTok username
  - Choose from 24 natural voices
- **🎛️ Control Buttons**:
  - 🚀 **Start Bot**: Begin listening to chat
  - ⏹️ **Stop Bot**: Disconnect from chat
  - 🔊 **Test TTS**: Preview selected voice
  - 🔗 **Test Connection**: Verify TikTok connectivity
  - � **Reset Rate Limit**: Clear connection cooldowns
- **📊 Statistics**: Live metrics (messages, jokes, uptime, etc.)
- **📋 Activity Log**: Real-time event monitoring with color coding

#### **👥 Tab 2: Users Joined**
- **Live User List**: See everyone who joined your stream
- **User Count**: Total unique viewers
- **�️ Clear List**: Reset the user list
- **Export Function**: Save user list to file

#### **🔗 Tab 3: Links**
- **Personal Links**: Your links from `links/links.txt`
- **3-Column Grid**: Organized, professional layout
- **Clickable**: Click any link to open in browser
- **Copy Function**: Right-click to copy URLs
- **Hover Effects**: Visual feedback on interaction

## 🎤 **Chat Commands Your Viewers Can Use**

| Command | Description | Example Response |
|---------|-------------|------------------|
| `!help` | Show available commands | Lists all commands |
| `!joke` | Random joke from collection | Tells a random joke |
| `!yo-mama` | Yo mama joke | Tells a yo mama joke |
| *Regular chat* | Normal TTS | "Username says: your message" |

## 🔧 **Customization Options**

### 🎵 **Voice Selection**
Choose from 24 ultra-natural voices:
- **🇺🇸 US Voices**: Google Home, Assistant, Conversational styles
- **🇬🇧 British Voices**: Posh, Professional, Assistant variants  
- **🇦🇺 Australian Voices**: Casual, Outback styles
- **🇮🇳 Indian English**: Professional Indian accents

### � **Links Setup**
1. Create `links/links.txt` file
2. Add your links in this format:
```
Social Media
https://twitter.com/yourusername
https://instagram.com/yourusername

Gaming
https://twitch.tv/yourusername
https://discord.gg/yourserver

Business
https://yourwebsite.com
mailto:your@email.com
```

### 😂 **Adding Custom Jokes**
1. Edit `jokes/random/random.txt` for regular jokes
2. Edit `jokes/yo_mama/yo_mama.txt` for yo mama jokes
3. Add one joke per line

## ⚙️ **Advanced Configuration**

### 🔑 **Google Cloud TTS Setup**

#### **Getting Your Google Cloud API Key (Step-by-Step)**

**📋 Prerequisites:**
- Google account (Gmail, etc.)
- Credit card for verification (Google offers $300 free credit)

**🚀 Step 1: Create Google Cloud Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click "Select a Project" → "New Project"
4. Enter project name (e.g., "TikTok-TTS-Bot")
5. Click "Create"

**🔧 Step 2: Enable Text-to-Speech API**
1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Cloud Text-to-Speech API"
3. Click on it and press "Enable"
4. Wait for API to be enabled (usually takes a few seconds)

**🔐 Step 3: Create Service Account & Download Key**
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Enter service account name (e.g., "tiktok-tts-bot")
4. Click "Create and Continue"
5. For role, select "Basic" → "Editor" (or "Project" → "Owner")
6. Click "Continue" → "Done"
7. Find your new service account in the list
8. Click the pencil icon (Edit) next to it
9. Go to "Keys" tab → "Add Key" → "Create New Key"
10. Select "JSON" format → "Create"
11. **Important**: Save the downloaded JSON file as `ivory-oarlock-410506-865276f8b548.json`

**📁 Step 4: Place Key File**
1. **Create `key` folder** in your `UtopiaBot-Jr` directory if it doesn't exist
2. **Move the downloaded JSON file** to `UtopiaBot-Jr/key/`
3. **Rename the file** to exactly: `ivory-oarlock-410506-865276f8b548.json`
4. **Final path**: `UtopiaBot-Jr/key/ivory-oarlock-410506-865276f8b548.json`

**💰 Cost Information:**
- Google gives **$300 free credit** for new accounts
- Text-to-Speech costs about **$4 per 1 million characters**
- For typical streaming, you'll use **$1-5 per month**
- Free tier includes 1 million characters per month

**✅ Verification:**
- Run the bot - you should see "✅ Google Cloud credentials loaded"
- Use "🔊 Test TTS" button to verify it's working
- If you see errors, double-check the file name and location

#### **File Setup Requirements**
1. **Credentials File**: Must be named `ivory-oarlock-410506-865276f8b548.json`
2. **Location**: Place in `key/` folder (create if doesn't exist)
3. **Path Structure**: `UtopiaBot-Jr/key/ivory-oarlock-410506-865276f8b548.json`
4. **Verification**: Bot will show "✅ Google Cloud credentials loaded" when correct

### 🌐 **Network & Connection**
- **Rate Limiting**: Built-in protection against TikTok API limits
- **Auto-Retry**: Automatic reconnection with exponential backoff
- **Connection Monitoring**: 5-second interval stream status checks
- **Timeout Handling**: Smart timeout and error recovery

### 📊 **Performance Optimization**
- **Optimized TTS**: Removed redundant credentials checking for faster processing
- **Memory Management**: Automatic audio file cleanup
- **Cache System**: 5-minute message deduplication reset
- **Thread Safety**: Separate threads for GUI updates and bot operations

## 🛡️ **Troubleshooting Guide**

### ❌ **Common Issues & Solutions**

#### **"❌ Google Cloud credentials not found"**
```
Solution: 
1. Check file exists: key/ivory-oarlock-410506-865276f8b548.json
2. Verify file name spelling (exact match required)
3. Ensure file is valid JSON format
4. Follow the Google Cloud setup guide above to create credentials
5. Make sure you enabled the Text-to-Speech API
```

#### **"❌ User not found" or "cannot go LIVE"**
```
Solution:
1. Verify TikTok username spelling (no @ symbol)
2. Confirm the user account can broadcast live
3. Check if account exists and is public
```

#### **"🔴 Stream appears to be OFFLINE"**
```
Solution:
1. Start your TikTok live stream first
2. Wait 30 seconds for detection
3. Check your streaming software/app
```

#### **"❌ Connection Error: Rate Limited"**
```
Solution:
1. Click "🔄 Reset Rate Limit" button
2. Wait 60-300 seconds before retrying
3. This is normal TikTok API protection
```

#### **"❌ TTS Error" or No Audio**
```
Solution:
1. Check Google Cloud credentials
2. Verify internet connection
3. Test with "🔊 Test TTS" button
4. Check system audio/speakers
```

### 🔍 **Diagnostic Tools**

#### **Built-in Connection Test**
1. Click "🔗 Test Connection" in GUI
2. Tests: Internet → TikTok → User Profile → Live Status
3. Provides detailed diagnostic information

#### **Voice Testing**
1. Select different voice from dropdown
2. Click "🔊 Test TTS" to preview
3. Verify audio output and quality

#### **Log Monitoring**
- **GUI**: Watch Activity Log tab for real-time status
- **CLI**: Monitor terminal output for errors
- **Color Coding**: Green=success, Red=error, Yellow=warning

## 📋 **Command Line Arguments**

```bash
# Launch options
python tiktok_bot_unified.py [options]

Options:
--username "name"     # Set TikTok username
--no-gui             # Force command line mode  
--gui                # Force GUI mode (default)
--help               # Show help information

# Examples
python tiktok_bot_unified.py --username "streamername"
python tiktok_bot_unified.py --no-gui
python tiktok_bot_unified.py --username "test" --no-gui
```

## 🎯 **Project Status & Features**

### ✅ **Completed Features (Production Ready)**
1. **🎤 Advanced TTS System** - 24 natural voices with regional support
2. **🔗 TikTok Live Integration** - Real-time chat connection and monitoring  
3. **🎮 Unified Interface** - Both GUI and CLI modes in single file
4. **👥 User Management** - Welcome messages and user tracking
5. **😂 Interactive Commands** - Joke system with multiple categories
6. **🔗 Links Dashboard** - 3-column grid with your personal links
7. **📊 Live Analytics** - Real-time statistics and performance metrics
8. **⚡ Performance Optimization** - Streamlined TTS processing
9. **🛡️ Error Handling** - Comprehensive error recovery and diagnostics
10. **🎨 Professional UI** - Dark theme with intuitive tabbed interface

### 🔮 **Future Enhancement Ideas**
- 🎵 **Music Integration**: Background music controls
- 🎨 **Custom Themes**: User-selectable color schemes  
- 🌍 **Multi-language**: Support for non-English TTS
- 🤖 **AI Responses**: Smart chatbot responses
- 📱 **Mobile App**: Companion mobile application
- 🔐 **Admin Panel**: Moderator commands and controls
- 📺 **Multi-Platform**: Discord, Twitch, YouTube integration
- 🎁 **Viewer Rewards**: Point system and rewards

## 🔒 **Important Files - DO NOT DELETE**

### 🚨 **Critical Files**
- `tiktok_bot_unified.py` - Main bot application
- `key/ivory-oarlock-410506-865276f8b548.json` - Google Cloud credentials
- `links/links.txt` - Your personal links data
- `jokes/random/random.txt` - Random jokes collection
- `jokes/yo_mama/yo_mama.txt` - Yo mama jokes collection

### 📁 **Auto-Created Folders**
- `tts_audio/` - Temporary audio files (safe to clear when bot not running)

## 🆘 **Getting Help & Support**

### 📞 **Quick Help Commands**
```bash
# Built-in help
python tiktok_bot_unified.py --help

# Test connection
python tiktok_bot_unified.py  # Then click "Test Connection"

# Verify TTS
python tiktok_bot_unified.py  # Then click "Test TTS"
```

### 🔍 **Self-Diagnosis Steps**
1. **Check Prerequisites**: Python 3.8+, pip packages installed
2. **Verify Credentials**: Google Cloud file in correct location
3. **Test Connection**: Use built-in connection tester
4. **Start Stream**: Make sure you're live on TikTok first
5. **Monitor Logs**: Watch activity log for specific errors

### 📋 **Common Setup Checklist**
- [ ] Python 3.8+ installed
- [ ] Required packages: `pip install TikTokLive google-cloud-texttospeech playsound emoji`
- [ ] **Google Cloud project created with Text-to-Speech API enabled**
- [ ] **Service account created and JSON key downloaded**
- [ ] Google Cloud credentials file in `key/` folder with correct name
- [ ] TikTok account capable of going live
- [ ] Active TikTok live stream running
- [ ] Correct TikTok username (no @ symbol)
- [ ] Audio/speakers working on computer

## 🎊 **Success Tips**

### 🏆 **Best Practices**
1. **Start Stream First** - Always go live on TikTok before starting the bot
2. **Test Everything** - Use connection and TTS tests before going live
3. **Monitor Status** - Watch the bot status indicator for issues
4. **Choose Good Voice** - Test different voices to find your favorite
5. **Prepare Links** - Set up your links.txt file with relevant URLs
6. **Check Audio** - Ensure system volume and speakers are working

### 💡 **Pro Tips**
- **Voice Selection**: US voices tend to be most natural for English
- **Rate Limiting**: If you get rate limited, wait 2-5 minutes before retry
- **Stream Quality**: Better internet = more reliable bot connection
- **Interaction**: Encourage viewers to use !joke and !yo-mama commands
- **Customization**: Add your own jokes to the text files for personality

---

## 🚀 **Ready to Stream?**

1. **📁 Navigate**: `cd Bots`
2. **🎮 Launch**: `python tiktok_bot_unified.py`  
3. **⚙️ Configure**: Set username and select voice
4. **🔗 Test**: Click "Test Connection" and "Test TTS"
5. **📺 Go Live**: Start your TikTok live stream
6. **🚀 Start Bot**: Click "Start Bot" and enjoy!

**🎉 Your TikTok TTS Bot is ready to make your streams more interactive and engaging!** 🎉

---

## 📈 **Development & Contributing**

### 🔄 **Roadmap**
Check out our [development roadmap](updates/changelog.txt) for upcoming features and version plans.

### 🤝 **Contributing**
We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:
- Reporting bugs
- Suggesting features  
- Code contributions
- Development setup

### 📝 **Issue Templates**
- 🐛 [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- ✨ [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)

### 📄 **License**
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⭐ If you find this bot helpful, please give it a star on GitHub! ⭐**
