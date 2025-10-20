# 🎤 CRM Voice Assistant Setup Guide
## faster-whisper + Claude Code Integration

Complete setup guide for integrating voice capabilities into your CRM with faster-whisper STT and Claude Code as the backend LLM.

---

## 📋 Prerequisites

- **Python 3.8+** installed
- **Claude Code** installed and in your PATH
- **Modern web browser** (Chrome, Edge, Firefox)
- **Microphone** access for voice input

### Optional for GPU Acceleration:
- CUDA 12.x for NVIDIA GPUs
- 4GB+ VRAM recommended

---

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip portaudio19-dev ffmpeg

# Install Python packages
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
# Basic (CPU)
python3 crm-backend.py

# With GPU (if available)
python3 crm-backend.py --device cuda

# Custom configuration
python3 crm-backend.py --host 0.0.0.0 --port 5000 --model base --device cpu
```

### 3. Open the Web UI

```bash
# Open in your default browser
open crm-voice-ui.html

# Or serve with a simple HTTP server
python3 -m http.server 8000
# Then navigate to: http://localhost:8000/crm-voice-ui.html
```

### 4. Configure the UI

1. In the web interface, set the API endpoint to: `http://localhost:5000`
2. Choose your preferred Whisper model size
3. Select your language
4. Click "Click to Record" and start speaking!

---

## 📦 Complete Installation

### Method 1: Automatic Installation Script

```bash
#!/bin/bash
# crm-voice-install.sh

echo "🎤 Installing CRM Voice Assistant..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
if (( $(echo "$python_version < 3.8" | bc -l) )); then
    echo "❌ Python 3.8+ required. Current: $python_version"
    exit 1
fi

# Check Claude Code
if ! command -v claude &> /dev/null; then
    echo "⚠️  Claude Code not found in PATH"
    echo "Please install Claude Code from: https://docs.claude.com/en/docs/claude-code"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y python3-pip portaudio19-dev ffmpeg build-essential
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew install portaudio ffmpeg
fi

# Create virtual environment (recommended)
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Download Whisper model (optional, will auto-download on first use)
echo "📥 Downloading Whisper base model..."
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base')"

echo ""
echo "✅ Installation complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python3 crm-backend.py"
echo ""
echo "Then open crm-voice-ui.html in your browser"
```

Save as `crm-voice-install.sh` and run:
```bash
chmod +x crm-voice-install.sh
./crm-voice-install.sh
```

### Method 2: Manual Installation

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    ffmpeg \
    build-essential
```

**macOS:**
```bash
brew install python portaudio ffmpeg
```

**Windows:**
```powershell
# Install Python from python.org
# Install Visual C++ Build Tools
# Install ffmpeg from ffmpeg.org
```

#### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Verify Installation

```bash
# Test imports
python3 << EOF
from faster_whisper import WhisperModel
from flask import Flask
import subprocess

print("✅ All imports successful!")
EOF

# Test Claude Code
echo "test" | claude
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# Whisper Configuration
WHISPER_MODEL_SIZE=base        # tiny, base, small, medium, large-v3
WHISPER_DEVICE=cpu             # cpu or cuda
WHISPER_COMPUTE_TYPE=int8      # int8, int16, float16, float32

# Claude Code
CLAUDE_CODE_PATH=claude        # Path to Claude Code executable

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
```

Load with:
```bash
export $(cat .env | xargs)
python3 crm-backend.py
```

### Backend Configuration Options

```bash
# Show all options
python3 crm-backend.py --help

# Common configurations
python3 crm-backend.py --host 0.0.0.0 --port 5000 --model base --device cpu
python3 crm-backend.py --host localhost --port 8080 --model small --device cuda
python3 crm-backend.py --model medium --device cuda --debug
```

### Web UI Configuration

Edit the settings in the web interface or modify the HTML:
- **API Endpoint**: Backend server URL
- **Whisper Model**: Model size (affects speed vs accuracy)
- **Language**: Input language for better accuracy

---

## 🎯 Usage Guide

### Voice Recording

1. **Click to Record Method:**
   - Click "🎤 Click to Record" button
   - Speak your query clearly
   - Click "⏹️ Stop Recording" when done
   - Wait for transcription and response

2. **Keyboard Shortcut:**
   - Press `Ctrl+R` to start/stop recording

3. **Upload Audio File:**
   - Click "📁 Upload Audio File"
   - Select any audio file (WAV, MP3, etc.)
   - System will transcribe and process

### Quick Actions

Use pre-defined CRM actions:
- **Find Customer**: Search for customer records
- **Create New Lead**: Add new lead to pipeline
- **Schedule Follow-up**: Set up future tasks
- **View Pipeline**: Check current sales pipeline
- **Send Email**: Compose and send emails

### API Endpoints

The backend provides these endpoints:

#### POST /transcribe
Transcribe audio and get Claude Code response
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@recording.wav" \
  -F "model=base" \
  -F "language=en"
```

#### POST /query
Direct text query (no transcription)
```bash
curl -X POST http://localhost:5000/query \
  -F "text=Find customer John Smith"
```

#### GET /health
Health check
```bash
curl http://localhost:5000/health
```

#### GET /models
List available models
```bash
curl http://localhost:5000/models
```

---

## 🚢 Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 crm-backend:app

# With timeout for long transcriptions
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 crm-backend:app
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY crm-backend.py .

# Expose port
EXPOSE 5000

# Run application
CMD ["python3", "crm-backend.py", "--host", "0.0.0.0", "--port", "5000"]
```

Build and run:
```bash
docker build -t crm-voice-backend .
docker run -p 5000:5000 crm-voice-backend
```

### Using Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - WHISPER_MODEL_SIZE=base
      - WHISPER_DEVICE=cpu
      - CLAUDE_CODE_PATH=/usr/local/bin/claude
    volumes:
      - ./models:/root/.cache/huggingface
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name crm.yourdomain.com;

    location / {
        root /var/www/crm;
        try_files $uri $uri/ /crm-voice-ui.html;
    }

    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Large file upload support
        client_max_body_size 25M;
        
        # Timeout for long transcriptions
        proxy_read_timeout 120s;
    }
}
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "No audio file provided" Error
**Solution:** Ensure your browser has microphone permissions enabled.
```bash
# Chrome: Settings → Privacy and security → Site Settings → Microphone
# Firefox: Preferences → Privacy & Security → Permissions → Microphone
```

#### 2. "Claude Code not found" Error
**Solution:** Install Claude Code or set the correct path
```bash
# Check if Claude Code is installed
which claude

# If not in PATH, set environment variable
export CLAUDE_CODE_PATH=/path/to/claude
python3 crm-backend.py
```

#### 3. "Failed to load Whisper model" Error
**Solution:** Model will auto-download on first use. Check internet connection.
```bash
# Manually download model
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

#### 4. Slow Transcription
**Solutions:**
- Use a smaller model: `--model tiny` or `--model base`
- Enable GPU: `--device cuda` (requires NVIDIA GPU with CUDA)
- Use quantization: `WHISPER_COMPUTE_TYPE=int8`

#### 5. CORS Errors in Browser
**Solution:** Backend has CORS enabled. If issues persist:
```bash
# Run backend on same host as web UI
python3 crm-backend.py --host localhost --port 5000

# Or serve HTML with Flask
python3 -m http.server 8000
```

#### 6. "Port already in use" Error
**Solution:** Change port or kill existing process
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use different port
python3 crm-backend.py --port 5001
```

---

## 📊 Performance Optimization

### Model Selection

| Model | Speed | Accuracy | Memory | Use Case |
|-------|-------|----------|--------|----------|
| tiny | ⚡⚡⚡⚡⚡ | ⭐⭐ | 1GB | Quick demos, testing |
| base | ⚡⚡⚡⚡ | ⭐⭐⭐ | 1GB | **Recommended for most** |
| small | ⚡⚡⚡ | ⭐⭐⭐⭐ | 2GB | Better accuracy needed |
| medium | ⚡⚡ | ⭐⭐⭐⭐⭐ | 5GB | High accuracy, GPU |
| large-v3 | ⚡ | ⭐⭐⭐⭐⭐ | 10GB | Best accuracy, GPU required |

### GPU Acceleration

**NVIDIA GPU:**
```bash
# Install CUDA toolkit
# https://developer.nvidia.com/cuda-downloads

# Install with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Run with GPU
python3 crm-backend.py --device cuda --model medium
```

**AMD GPU (ROCm):**
```bash
# Install ROCm
# https://rocmdocs.amd.com/

# Set environment
export ROCM_HOME=/opt/rocm
python3 crm-backend.py --device cuda
```

### Performance Tuning

```python
# In crm-backend.py, adjust these parameters:

# VAD (Voice Activity Detection) - reduces processing of silence
vad_filter=True,
vad_parameters=dict(
    threshold=0.5,              # Lower = more sensitive
    min_speech_duration_ms=250, # Minimum speech length
    min_silence_duration_ms=2000 # Silence before cut
)

# Beam size - higher = more accurate but slower
beam_size=5  # Default. Try 1 for faster, 10 for better
```

---

## 🔐 Security Considerations

### Production Checklist

- [ ] Enable HTTPS with SSL certificates
- [ ] Add authentication (JWT, OAuth, API keys)
- [ ] Implement rate limiting
- [ ] Validate and sanitize all inputs
- [ ] Set maximum file upload sizes
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted domains
- [ ] Regular security updates
- [ ] Monitor and log all requests
- [ ] Implement request timeouts

### Example: Adding API Key Authentication

```python
# In crm-backend.py, add:
from functools import wraps

API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Then add to routes:
@app.route('/transcribe', methods=['POST'])
@require_api_key
def transcribe():
    # ... existing code
```

---

## 📚 Additional Resources

### Documentation
- **faster-whisper:** https://github.com/SYSTRAN/faster-whisper
- **Claude Code:** https://docs.claude.com/en/docs/claude-code
- **Flask:** https://flask.palletsprojects.com/

### Community
- faster-whisper Issues: https://github.com/SYSTRAN/faster-whisper/issues
- Claude AI Discord: https://discord.gg/claude-ai
- Stack Overflow: Tag `faster-whisper` or `flask`

### Model Performance
- Whisper Models: https://huggingface.co/openai
- Benchmarks: https://github.com/openai/whisper#available-models-and-languages

---

## 🎉 You're Ready!

Your CRM voice assistant is now set up with:
✅ faster-whisper for accurate speech-to-text
✅ Claude Code as the intelligent backend
✅ Modern web UI with real-time feedback
✅ Production-ready Flask API
✅ Easy deployment options

**Start the system:**
```bash
# Terminal 1: Start backend
python3 crm-backend.py

# Terminal 2: Serve frontend
python3 -m http.server 8000

# Then open: http://localhost:8000/crm-voice-ui.html
```

**Need help?** Check the troubleshooting section or review the logs with `--debug` flag.
