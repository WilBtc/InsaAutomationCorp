#!/bin/bash

# CRM Voice Assistant Installation Script
# Installs faster-whisper + Claude Code integration

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🎤 CRM Voice Assistant Installation                          ║"
echo "║   Powered by faster-whisper & Claude Code                     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Check Python version is 3.8+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo -e "${RED}❌ Python 3.8+ required. Current: $PYTHON_VERSION${NC}"
    exit 1
fi

# Check Claude Code
echo ""
echo "🤖 Checking Claude Code..."
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠️  Claude Code not found in PATH${NC}"
    echo "Please install Claude Code from: https://docs.claude.com/en/docs/claude-code"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Claude Code found at: $(which claude)${NC}"
fi

# Detect OS
echo ""
echo "🔍 Detecting operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo -e "${GREEN}✅ Linux detected${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo -e "${GREEN}✅ macOS detected${NC}"
else
    OS="unknown"
    echo -e "${YELLOW}⚠️  Unknown OS: $OSTYPE${NC}"
fi

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."
if [[ "$OS" == "linux" ]]; then
    if command -v apt-get &> /dev/null; then
        echo "Using apt-get..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq \
            python3-pip \
            python3-venv \
            portaudio19-dev \
            ffmpeg \
            build-essential
        echo -e "${GREEN}✅ System dependencies installed${NC}"
    elif command -v yum &> /dev/null; then
        echo "Using yum..."
        sudo yum install -y python3-pip python3-devel portaudio-devel ffmpeg gcc
        echo -e "${GREEN}✅ System dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Package manager not recognized. Please install manually:${NC}"
        echo "  - python3-pip"
        echo "  - portaudio19-dev"
        echo "  - ffmpeg"
        echo "  - build-essential"
    fi
elif [[ "$OS" == "macos" ]]; then
    if command -v brew &> /dev/null; then
        echo "Using Homebrew..."
        brew install portaudio ffmpeg
        echo -e "${GREEN}✅ System dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Homebrew not found. Please install from https://brew.sh${NC}"
        echo "Then run: brew install portaudio ffmpeg"
    fi
fi

# Create virtual environment
echo ""
echo "🐍 Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing...${NC}"
    rm -rf venv
fi

python3 -m venv venv
echo -e "${GREEN}✅ Virtual environment created${NC}"

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --quiet --upgrade pip
echo -e "${GREEN}✅ pip upgraded${NC}"

# Install Python dependencies
echo ""
echo "📦 Installing Python packages (this may take a few minutes)..."
pip install --quiet Flask==3.0.0
pip install --quiet flask-cors==4.0.0
pip install --quiet faster-whisper==1.0.3
echo -e "${GREEN}✅ Python packages installed${NC}"

# Download base model
echo ""
echo "📥 Downloading Whisper base model (this will take a few minutes)..."
python3 << EOF
from faster_whisper import WhisperModel
print("Downloading model...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("Model downloaded successfully!")
EOF
echo -e "${GREEN}✅ Whisper model downloaded${NC}"

# Create convenience scripts
echo ""
echo "📝 Creating convenience scripts..."

# Start script
cat > start-crm-voice.sh << 'STARTSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🚀 Starting CRM Voice Assistant Backend..."
echo "Backend will be available at: http://localhost:5000"
echo ""
python3 crm-backend.py "$@"
STARTSCRIPT
chmod +x start-crm-voice.sh

# Start with GPU script
cat > start-crm-voice-gpu.sh << 'GPUSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🚀 Starting CRM Voice Assistant Backend (GPU)..."
echo "Backend will be available at: http://localhost:5000"
echo ""
python3 crm-backend.py --device cuda "$@"
GPUSCRIPT
chmod +x start-crm-voice-gpu.sh

# Test script
cat > test-installation.sh << 'TESTSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

echo "🧪 Testing installation..."
echo ""

echo "1️⃣  Testing Python imports..."
python3 << EOF
try:
    from faster_whisper import WhisperModel
    from flask import Flask
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF

echo ""
echo "2️⃣  Testing Whisper model..."
python3 << EOF
try:
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu")
    print("✅ Whisper model loaded")
except Exception as e:
    print(f"❌ Model error: {e}")
    exit(1)
EOF

echo ""
echo "3️⃣  Testing Claude Code..."
if command -v claude &> /dev/null; then
    echo "test" | claude > /dev/null 2>&1 && echo "✅ Claude Code working" || echo "⚠️  Claude Code found but not responding"
else
    echo "⚠️  Claude Code not in PATH"
fi

echo ""
echo "✅ Installation test complete!"
TESTSCRIPT
chmod +x test-installation.sh

echo -e "${GREEN}✅ Convenience scripts created${NC}"

# Create systemd service (optional, for Linux)
if [[ "$OS" == "linux" ]]; then
    echo ""
    read -p "Create systemd service for auto-start? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        INSTALL_DIR=$(pwd)
        SERVICE_FILE="/etc/systemd/system/crm-voice-assistant.service"
        
        sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=CRM Voice Assistant Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/crm-backend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable crm-voice-assistant.service
        echo -e "${GREEN}✅ Systemd service created and enabled${NC}"
        echo "Start with: sudo systemctl start crm-voice-assistant.service"
    fi
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   ✅ Installation Complete!                                    ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}📂 Installation directory:${NC} $(pwd)"
echo ""
echo -e "${BLUE}🚀 To start the backend:${NC}"
echo "   ./start-crm-voice.sh"
echo ""
echo -e "${BLUE}🌐 To open the web UI:${NC}"
echo "   1. Start the backend (above)"
echo "   2. Open crm-voice-ui.html in your browser"
echo "   Or serve with: python3 -m http.server 8000"
echo ""
echo -e "${BLUE}🧪 To test installation:${NC}"
echo "   ./test-installation.sh"
echo ""
echo -e "${BLUE}⚡ For GPU acceleration:${NC}"
echo "   ./start-crm-voice-gpu.sh"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "   CRM-SETUP-GUIDE.md"
echo ""
echo -e "${GREEN}Enjoy your CRM Voice Assistant! 🎉${NC}"
echo ""
