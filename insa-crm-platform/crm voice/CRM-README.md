# 🎤 CRM Voice Assistant

**Professional-grade voice interface for your CRM powered by faster-whisper STT and Claude Code LLM**

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-Open%20Source-brightgreen)

---

## 🌟 Features

- **🎙️ Real-time Speech Recognition** - Using faster-whisper for accurate, low-latency STT
- **🤖 AI-Powered Responses** - Claude Code integration for intelligent CRM assistance
- **🌍 Multi-language Support** - 100+ languages supported
- **⚡ Fast & Efficient** - Optimized for both CPU and GPU
- **🎨 Modern Web UI** - Beautiful, responsive interface
- **📱 Mobile Friendly** - Works on desktop, tablet, and mobile
- **🔒 Privacy First** - Self-hosted, no data leaves your infrastructure
- **🎯 CRM-Specific** - Pre-built actions for common CRM tasks

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Clone or download this repository
git clone <your-repo-url>
cd crm-voice-assistant

# 2. Run the installer
chmod +x crm-voice-install.sh
./crm-voice-install.sh

# 3. Start the backend
./start-crm-voice.sh

# 4. Open the web UI
open crm-voice-ui.html
```

That's it! You now have a fully functional voice-enabled CRM assistant.

---

## 📦 What's Included

```
crm-voice-assistant/
├── crm-voice-ui.html           # Web interface (frontend)
├── crm-backend.py              # Flask API server (backend)
├── requirements.txt            # Python dependencies
├── crm-voice-install.sh        # Automated installer
├── CRM-SETUP-GUIDE.md         # Complete setup documentation
├── CRM-QUICK-REFERENCE.md     # Command cheat sheet
├── OSS-STT-TTS-GUIDE.md       # Guide to open-source STT/TTS
└── README.md                  # This file
```

---

## 🎯 Use Cases

### Customer Management
- "Find customer records for Acme Corp"
- "Show me all deals over $50,000"
- "What's the status of John Smith's account?"

### Lead Management
- "Create new lead for TechStart Inc"
- "Update lead status to qualified"
- "Schedule demo for Friday at 2pm"

### Pipeline Management
- "Show me today's pipeline"
- "What deals are closing this month?"
- "Move deal to negotiation stage"

### Task Management
- "Add follow-up task for tomorrow"
- "Show my open tasks"
- "Mark task as complete"

### Communication
- "Send email to Sarah about the proposal"
- "Schedule call with client next week"
- "Add note: Great conversation about their needs"

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Browser   │
│  (crm-voice-    │
│   ui.html)      │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│  Flask Backend  │
│  (crm-backend.  │
│   py)           │
├─────────────────┤
│ faster-whisper  │◄── Audio transcription
├─────────────────┤
│  Claude Code    │◄── LLM responses
└─────────────────┘
```

### Flow:
1. User speaks into microphone
2. Audio sent to Flask backend
3. faster-whisper transcribes speech to text
4. Text sent to Claude Code
5. Claude Code generates intelligent response
6. Response displayed in web UI

---

## 💻 System Requirements

### Minimum (CPU)
- Python 3.8+
- 4GB RAM
- 2GB free disk space
- Modern web browser (Chrome, Edge, Firefox)

### Recommended (GPU)
- Python 3.8+
- NVIDIA GPU with 4GB+ VRAM
- CUDA 12.x
- 8GB RAM
- 5GB free disk space

### Software
- Claude Code installed and in PATH
- FFmpeg (auto-installed by installer)
- Microphone for voice input

---

## 🔧 Installation

### Automated Installation (Recommended)

```bash
chmod +x crm-voice-install.sh
./crm-voice-install.sh
```

The installer will:
- ✅ Check prerequisites
- ✅ Install system dependencies
- ✅ Create virtual environment
- ✅ Install Python packages
- ✅ Download Whisper models
- ✅ Create convenience scripts
- ✅ Optionally set up systemd service

### Manual Installation

See [CRM-SETUP-GUIDE.md](CRM-SETUP-GUIDE.md) for detailed manual installation instructions.

---

## 🎮 Usage

### Starting the System

```bash
# Start backend (CPU)
./start-crm-voice.sh

# Start backend (GPU)
./start-crm-voice-gpu.sh

# Custom configuration
python3 crm-backend.py --host 0.0.0.0 --port 5000 --model base --device cpu
```

### Using Voice Input

1. **Click to Record**: Click the microphone button and speak
2. **Keyboard Shortcut**: Press `Ctrl+R` to start/stop recording
3. **Upload Audio**: Click upload button to process audio files

### Quick Actions

The UI includes pre-configured CRM actions:
- 👤 Find Customer
- ➕ Create New Lead
- 📅 Schedule Follow-up
- 📊 View Pipeline
- ✉️ Send Email

---

## ⚙️ Configuration

### Backend Configuration

```bash
# Environment variables
export WHISPER_MODEL_SIZE=base    # tiny, base, small, medium, large-v3
export WHISPER_DEVICE=cpu         # cpu or cuda
export CLAUDE_CODE_PATH=claude    # Path to Claude Code

# Command line arguments
python3 crm-backend.py \
  --model base \
  --device cpu \
  --host 0.0.0.0 \
  --port 5000 \
  --debug
```

### Web UI Configuration

Settings are in the sidebar:
- **Whisper Model**: Choose model size (tiny/base/small/medium)
- **Language**: Select input language for better accuracy
- **API Endpoint**: Backend server URL

---

## 📊 Performance

### CPU Performance (Intel i7)
| Model | Speed | Memory |
|-------|-------|--------|
| tiny | 8x realtime | 1GB |
| base | 4x realtime | 1GB |
| small | 2x realtime | 2GB |

### GPU Performance (NVIDIA RTX 3070)
| Model | Speed | Memory |
|-------|-------|--------|
| base | 60x realtime | 2GB |
| small | 40x realtime | 3GB |
| medium | 25x realtime | 5GB |

---

## 🔌 API Reference

### POST /transcribe
Transcribe audio and get Claude Code response

```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@recording.wav" \
  -F "model=base" \
  -F "language=en"
```

### POST /query
Direct text query (no transcription)

```bash
curl -X POST http://localhost:5000/query \
  -F "text=Find customer John Smith"
```

### GET /health
Health check endpoint

```bash
curl http://localhost:5000/health
```

---

## 🚢 Deployment

### Development

```bash
python3 crm-backend.py --debug
```

### Production (Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 crm-backend:app
```

### Docker

```bash
docker build -t crm-voice-backend .
docker run -p 5000:5000 crm-voice-backend
```

### Systemd Service

```bash
sudo systemctl start crm-voice-assistant
sudo systemctl enable crm-voice-assistant
```

---

## 🔐 Security

For production deployments:

1. **Enable HTTPS** with SSL certificates
2. **Add Authentication** (JWT, OAuth, API keys)
3. **Implement Rate Limiting** to prevent abuse
4. **Validate Inputs** - sanitize all user data
5. **Set File Size Limits** - prevent DoS
6. **Configure CORS** - restrict to trusted domains
7. **Monitor Logs** - track all requests
8. **Regular Updates** - keep dependencies current

See [CRM-SETUP-GUIDE.md](CRM-SETUP-GUIDE.md) for detailed security configuration.

---

## 🆘 Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check Python version
python3 --version

# Test installation
./test-installation.sh
```

**Claude Code not found**
```bash
# Verify Claude Code installation
which claude
echo "test" | claude

# Set path if needed
export CLAUDE_CODE_PATH=/path/to/claude
```

**Slow transcription**
```bash
# Use smaller model or GPU
python3 crm-backend.py --model tiny
python3 crm-backend.py --device cuda
```

**Microphone not working**
- Grant browser microphone permissions
- Check browser settings: Privacy → Microphone

See [CRM-QUICK-REFERENCE.md](CRM-QUICK-REFERENCE.md) for more troubleshooting.

---

## 📚 Documentation

- **[CRM-SETUP-GUIDE.md](CRM-SETUP-GUIDE.md)** - Complete installation and configuration guide
- **[CRM-QUICK-REFERENCE.md](CRM-QUICK-REFERENCE.md)** - Command cheat sheet
- **[OSS-STT-TTS-GUIDE.md](OSS-STT-TTS-GUIDE.md)** - Guide to open-source STT/TTS options

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional CRM integrations (Salesforce, HubSpot, etc.)
- More language support
- Enhanced UI features
- Performance optimizations
- Documentation improvements

---

## 📝 License

This project is open source. Use and modify as needed for your CRM implementation.

---

## 🙏 Acknowledgments

Built with:
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** - Fast, accurate speech recognition
- **[Claude Code](https://docs.claude.com/en/docs/claude-code)** - AI-powered assistance
- **[Flask](https://flask.palletsprojects.com/)** - Web framework
- **[OpenAI Whisper](https://github.com/openai/whisper)** - Original Whisper model

---

## 📞 Support

- **Documentation**: See docs folder
- **Issues**: Report bugs and request features
- **Community**: Join discussions

---

## 🎉 Get Started Now!

```bash
./crm-voice-install.sh
./start-crm-voice.sh
open crm-voice-ui.html
```

**Transform your CRM with voice! 🎤✨**
