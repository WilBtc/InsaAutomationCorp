# 🎤 CRM Voice Assistant - Quick Reference

## 🚀 Quick Start

```bash
# 1. Install (one-time setup)
chmod +x crm-voice-install.sh
./crm-voice-install.sh

# 2. Start backend
./start-crm-voice.sh

# 3. Open web UI
open crm-voice-ui.html
```

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `crm-voice-ui.html` | Web interface (frontend) |
| `crm-backend.py` | Flask API server (backend) |
| `requirements.txt` | Python dependencies |
| `crm-voice-install.sh` | Automated installer |
| `CRM-SETUP-GUIDE.md` | Complete documentation |

## 🎯 Common Commands

### Start/Stop Backend

```bash
# Start (CPU)
./start-crm-voice.sh

# Start (GPU)
./start-crm-voice-gpu.sh

# Custom configuration
python3 crm-backend.py --host 0.0.0.0 --port 5000 --model base --device cpu

# Stop (Ctrl+C in terminal)
```

### Test Installation

```bash
./test-installation.sh
```

### Access Web UI

```bash
# Option 1: Direct file
open crm-voice-ui.html

# Option 2: HTTP server
python3 -m http.server 8000
# Then: http://localhost:8000/crm-voice-ui.html
```

## 🔧 Configuration

### Backend Settings

```bash
# Environment variables
export WHISPER_MODEL_SIZE=base
export WHISPER_DEVICE=cpu
export CLAUDE_CODE_PATH=claude

# Command line
python3 crm-backend.py \
  --model base \
  --device cpu \
  --host 0.0.0.0 \
  --port 5000
```

### Web UI Settings

1. Open crm-voice-ui.html
2. Settings section (bottom left):
   - **Whisper Model**: tiny/base/small/medium
   - **Language**: en/es/fr/de/etc
   - **API Endpoint**: http://localhost:5000

## 📊 Model Comparison

| Model | Speed | Accuracy | Memory | Best For |
|-------|-------|----------|--------|----------|
| tiny | ⚡⚡⚡⚡⚡ | ⭐⭐ | 1GB | Testing |
| base | ⚡⚡⚡⚡ | ⭐⭐⭐ | 1GB | **Recommended** |
| small | ⚡⚡⚡ | ⭐⭐⭐⭐ | 2GB | Better accuracy |
| medium | ⚡⚡ | ⭐⭐⭐⭐⭐ | 5GB | High accuracy + GPU |

## 🎤 Using Voice Input

### Method 1: Click to Record
1. Click "🎤 Click to Record"
2. Speak your query
3. Click "⏹️ Stop Recording"

### Method 2: Keyboard Shortcut
- Press `Ctrl+R` to start/stop

### Method 3: Upload Audio
1. Click "📁 Upload Audio File"
2. Select audio file
3. Wait for processing

## 📡 API Endpoints

### POST /transcribe
Transcribe audio + get Claude response
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@recording.wav" \
  -F "model=base" \
  -F "language=en"
```

### POST /query
Text query only (no audio)
```bash
curl -X POST http://localhost:5000/query \
  -F "text=Find customer John Smith"
```

### GET /health
Check server status
```bash
curl http://localhost:5000/health
```

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check Python
python3 --version

# Check dependencies
source venv/bin/activate
pip list | grep -E "Flask|whisper"

# Check Claude Code
which claude
echo "test" | claude
```

### "No audio file" error
- Grant microphone permissions in browser
- Settings → Privacy → Microphone

### "Claude Code not found"
```bash
# Find Claude
which claude

# Set path
export CLAUDE_CODE_PATH=/path/to/claude
./start-crm-voice.sh
```

### Slow transcription
```bash
# Use smaller model
python3 crm-backend.py --model tiny

# Or use GPU
python3 crm-backend.py --device cuda --model base
```

### Port already in use
```bash
# Find process
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port
python3 crm-backend.py --port 5001
```

## 🔥 Pro Tips

1. **Faster transcription**: Use `tiny` model for demos
2. **Better accuracy**: Use `small` or `medium` model
3. **GPU acceleration**: Add `--device cuda` for 5-10x speedup
4. **Multiple languages**: Select language in UI for better accuracy
5. **Quick actions**: Use pre-defined CRM commands
6. **Keyboard shortcuts**: `Ctrl+R` to record
7. **Copy responses**: Click 📋 Copy button

## 📊 Performance Metrics

### CPU (Intel i7)
- tiny: ~8x real-time
- base: ~4x real-time
- small: ~2x real-time

### GPU (NVIDIA RTX 3070)
- base: ~60x real-time
- small: ~40x real-time
- medium: ~25x real-time

## 🔐 Security Notes

For production:
- [ ] Enable HTTPS
- [ ] Add authentication
- [ ] Rate limiting
- [ ] Input validation
- [ ] CORS restrictions
- [ ] API keys

## 📚 Resources

- **Setup Guide**: CRM-SETUP-GUIDE.md
- **faster-whisper**: https://github.com/SYSTRAN/faster-whisper
- **Claude Code**: https://docs.claude.com/en/docs/claude-code
- **Flask**: https://flask.palletsprojects.com/

## 🎉 Common Use Cases

### CRM Tasks
- "Find customer John Smith"
- "Create new lead for Acme Corp"
- "Schedule follow-up for next Tuesday"
- "Show me today's pipeline"
- "Send email to Sarah about the proposal"

### Voice Commands
- "What are my tasks for today?"
- "Update customer status to closed won"
- "Add note to deal: Great conversation"
- "Find all deals over $10,000"
- "Export report for Q4 sales"

## ✅ Daily Workflow

```bash
# Morning
./start-crm-voice.sh        # Start backend
open crm-voice-ui.html       # Open UI

# During day
# Use voice/text to interact with CRM

# Evening
# Ctrl+C to stop backend
```

## 🔄 Updates

```bash
# Update Python packages
source venv/bin/activate
pip install --upgrade faster-whisper flask flask-cors

# Update models
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', download_root='./models')"

# Check versions
pip list | grep -E "whisper|flask"
```

---

**Need help?** Check CRM-SETUP-GUIDE.md or run `./test-installation.sh`
