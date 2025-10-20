# 🎤 INSA CRM Voice Assistant - Quick Start Guide

**Status:** ✅ INSTALLED & RUNNING
**Server:** iac1 (100.100.101.1)
**Date:** October 19, 2025

---

## 🚀 System Status

### Backend Server
- **URL:** http://100.100.101.1:5000
- **Status:** ✅ RUNNING (PID: 89871)
- **Log File:** `~/insa-crm-platform/crm voice/crm-voice.log`
- **Auto-start:** systemd service configured

### Configuration
- **Speech-to-Text:** faster-whisper (base model, CPU-only)
- **AI Engine:** Claude Code (subprocess integration)
- **Device:** CPU only (int8 compute type)
- **Resource Limits:** 50% CPU, 2GB RAM

---

## 📡 Available Endpoints

### Health Check
```bash
curl http://100.100.101.1:5000/health
```

### Voice Transcription + AI Response
```bash
curl -X POST http://100.100.101.1:5000/transcribe \
  -F "audio=@recording.wav" \
  -F "model=base" \
  -F "language=en"
```

### Text-Only Query (No Voice)
```bash
curl -X POST http://100.100.101.1:5000/query \
  -F "text=Show me today's CRM pipeline"
```

### List Available Models
```bash
curl http://100.100.101.1:5000/models
```

---

## 🎯 How to Use

### Option 1: Web Interface (Recommended)
```bash
# On iac1 server
cd ~/insa-crm-platform/crm\ voice
python3 -m http.server 8001
# Then open: http://100.100.101.1:8001/crm-voice-ui.html
```

### Option 2: Direct File (Local Browser)
```bash
# Copy crm-voice-ui.html to your workstation
scp wil@100.100.101.1:"~/insa-crm-platform/crm voice/crm-voice-ui.html" .
# Then open it in browser and configure endpoint to http://100.100.101.1:5000
```

### Option 3: API Integration
See examples in CRM-SETUP-GUIDE.md

---

## 🛠️ Management Commands

### Check Service Status
```bash
sudo systemctl status crm-voice-assistant
```

### View Live Logs
```bash
tail -f ~/insa-crm-platform/crm\ voice/crm-voice.log
```

### Start/Stop/Restart
```bash
sudo systemctl start crm-voice-assistant
sudo systemctl stop crm-voice-assistant
sudo systemctl restart crm-voice-assistant
```

### Enable Auto-start on Boot
```bash
sudo systemctl enable crm-voice-assistant
```

### Manual Start (for testing)
```bash
cd ~/insa-crm-platform/crm\ voice
./start-crm-voice.sh
```

---

## 🎤 Example Voice Commands

### CRM Operations
- "Find customer Acme Corporation"
- "Create new lead for TechStart Industries"
- "Show me all deals over $50,000"
- "Update lead status to qualified"
- "Schedule follow-up call for tomorrow at 2pm"

### Data Queries
- "What's my pipeline for this week?"
- "Show me high priority leads"
- "Export sales report for Q4"
- "List all open opportunities"

### Task Management
- "Add task: Send proposal to John"
- "Show my tasks for today"
- "Mark task as complete"

---

## 🔧 Configuration

### Environment Variables
```bash
export WHISPER_MODEL_SIZE=base     # tiny, base, small, medium
export WHISPER_DEVICE=cpu          # cpu only (no GPU)
export WHISPER_COMPUTE_TYPE=int8   # int8 for CPU efficiency
export CLAUDE_CODE_PATH=/home/wil/.local/bin/claude
```

### Change Whisper Model (Trade-off: Speed vs Accuracy)
```bash
# Faster (less accurate) - good for testing
sudo systemctl stop crm-voice-assistant
# Edit: /etc/systemd/system/crm-voice-assistant.service
# Change: --model tiny
sudo systemctl daemon-reload
sudo systemctl start crm-voice-assistant

# Better accuracy (slower) - production
# Change: --model small
```

---

## 📊 Performance

### CPU Performance (Intel Xeon - iac1)
| Model | Speed | Accuracy | Memory | Recommended |
|-------|-------|----------|--------|-------------|
| tiny | ~8x realtime | ⭐⭐ | 1GB | Testing only |
| **base** | **~4x realtime** | **⭐⭐⭐** | **1GB** | **✅ Current** |
| small | ~2x realtime | ⭐⭐⭐⭐ | 2GB | Production |
| medium | ~1x realtime | ⭐⭐⭐⭐⭐ | 5GB | High accuracy |

**Current Setup:** Base model provides good balance for CPU-only server

---

## 🔗 Integration with INSA CRM Platform

### Architecture
```
┌──────────────────┐
│  Web Browser/    │
│  Mobile App      │
└────────┬─────────┘
         │ HTTP
         ▼
┌──────────────────┐
│  CRM Voice API   │ ← YOU ARE HERE
│  :5000           │
├──────────────────┤
│ faster-whisper   │ (Speech-to-Text)
├──────────────────┤
│  Claude Code     │ (AI Understanding)
└────────┬─────────┘
         │ Subprocess
         ▼
┌──────────────────┐
│  INSA CRM Core   │
│  :8003           │
├──────────────────┤
│  ERPNext :9000   │
│  Mautic :9700    │
│  n8n :5678       │
└──────────────────┘
```

### Integration Points
1. **Voice → Text:** faster-whisper transcribes audio
2. **Text → Intent:** Claude Code understands user intent
3. **Intent → Action:** Claude Code can call:
   - INSA CRM Core API (lead scoring, quotes)
   - ERPNext MCP (customers, opportunities, sales orders)
   - Mautic MCP (marketing campaigns, contacts)
   - n8n MCP (trigger workflows)

---

## 🆘 Troubleshooting

### Backend Not Responding
```bash
# Check if service is running
sudo systemctl status crm-voice-assistant

# Check logs
tail -50 ~/insa-crm-platform/crm\ voice/crm-voice.log

# Restart service
sudo systemctl restart crm-voice-assistant
```

### Claude Code Not Found
```bash
# Verify Claude Code installation
which claude
/home/wil/.local/bin/claude

# Test Claude Code
echo "test" | claude
```

### Slow Transcription
```bash
# Switch to tiny model for faster processing
# Edit service file and change --model to tiny
sudo nano /etc/systemd/system/crm-voice-assistant.service
sudo systemctl daemon-reload
sudo systemctl restart crm-voice-assistant
```

### Port 5000 Conflict
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Option 1: Kill the process
sudo kill <PID>

# Option 2: Use different port
# Edit service file and change --port 5001
```

### High CPU Usage
```bash
# Check resource usage
docker stats
ps aux | grep python

# Reduce CPU limit in service file
sudo nano /etc/systemd/system/crm-voice-assistant.service
# Change CPUQuota=50% to 30%
```

---

## 📝 Next Steps

### 1. Test the Web Interface
```bash
cd ~/insa-crm-platform/crm\ voice
python3 -m http.server 8001
# Open: http://100.100.101.1:8001/crm-voice-ui.html
```

### 2. Try Voice Commands
- Click "🎤 Click to Record"
- Say: "Show me my CRM pipeline"
- Watch it transcribe and respond

### 3. Integrate with Your Workflow
- Use API endpoints in your applications
- Build mobile apps that connect to voice API
- Create custom voice commands for INSA-specific tasks

### 4. Production Hardening
- [ ] Add authentication (JWT tokens)
- [ ] Enable HTTPS (SSL certificates)
- [ ] Add rate limiting
- [ ] Set up monitoring/alerts
- [ ] Regular backups of configuration

---

## 📚 Documentation

- **Main README:** CRM-README.md (features, architecture)
- **Setup Guide:** CRM-SETUP-GUIDE.md (detailed installation)
- **Quick Reference:** CRM-QUICK-REFERENCE.md (commands, tips)
- **Open Source STT/TTS:** OSS-STT-TTS-GUIDE.md (alternatives)
- **This Guide:** INSA-CRM-VOICE-QUICK-START.md (INSA-specific)

---

## 🔐 Security Notes

### Current Setup (Development)
- ⚠️ No authentication (public API)
- ⚠️ HTTP only (not HTTPS)
- ⚠️ CORS enabled for all origins
- ✅ File size limits (25MB)
- ✅ Input validation
- ✅ Resource limits (CPU, memory)

### Production Recommendations
1. **Add Authentication:** JWT tokens or API keys
2. **Enable HTTPS:** Use Let's Encrypt certificates
3. **Restrict CORS:** Only allow trusted domains
4. **Rate Limiting:** Prevent abuse
5. **Input Sanitization:** Additional validation
6. **Audit Logging:** Track all requests

---

## 📞 Support

**Project:** INSA CRM Platform
**Owner:** Wil Aroca (INSA Automation Corp)
**Email:** w.aroca@insaing.com
**Server:** iac1 (100.100.101.1)

---

## ✅ Verification Checklist

- [x] Backend installed (faster-whisper + Flask)
- [x] Service configured (systemd)
- [x] Backend running (PID: 89871)
- [x] Health check passing (http://100.100.101.1:5000/health)
- [x] CPU-only mode configured
- [x] Claude Code integration working
- [x] Resource limits set (50% CPU, 2GB RAM)
- [x] Logs configured
- [ ] Web UI tested (do this next!)
- [ ] Production hardening (future)

---

🤖 **Built with Claude Code for INSA Automation Corp**

**Ready to transform your CRM with voice! 🎤✨**
