# 🎤🔊 Open Source Speech-to-Text & Text-to-Speech for Claude Code

A curated list of the best open-source STT and TTS GitHub repositories for building a complete voice assistant with Claude Code as the LLM agent.

---

## 📊 Quick Comparison Table

| Tool | Type | Speed | Quality | Languages | Easy Setup | Best For |
|------|------|-------|---------|-----------|------------|----------|
| **faster-whisper** | STT | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 100+ | ✅ Easy | Real-time, Production |
| **whisper.cpp** | STT | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 100+ | ✅ Easy | Low-resource, Edge |
| **WhisperLive** | STT | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 100+ | ⚠️ Medium | Real-time server |
| **Piper TTS** | TTS | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 50+ | ✅ Easy | Fast, Natural |
| **Coqui TTS** | TTS | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 1100+ | ⚠️ Medium | Voice cloning |
| **Bark** | TTS | ⚡⚡ | ⭐⭐⭐⭐⭐ | Multi | ⚠️ Medium | Emotional, Creative |

---

## 🎙️ SPEECH-TO-TEXT (STT) SOLUTIONS

### 1. **faster-whisper** ⭐ RECOMMENDED
**GitHub:** https://github.com/SYSTRAN/faster-whisper

**Why This is Best:**
- Up to 4x faster than OpenAI Whisper with same accuracy
- Low memory usage with 8-bit quantization support
- Production-ready, battle-tested backend
- Easy Python API integration

**Key Features:**
- Real-time capable with proper batching
- Runs on CPU or GPU (CUDA/ROCm)
- No FFmpeg dependency (uses PyAV)
- Multiple model sizes (tiny to large-v3)

**Installation:**
```bash
pip install faster-whisper
```

**Basic Usage with Claude Code:**
```python
from faster_whisper import WhisperModel
import subprocess

# Initialize model
model = WhisperModel("base", device="cpu", compute_type="int8")

# Transcribe audio
segments, info = model.transcribe("audio.wav", beam_size=5)

# Send to Claude Code
for segment in segments:
    text = segment.text
    result = subprocess.run(
        ['claude'], 
        input=text, 
        text=True, 
        capture_output=True
    )
    print(result.stdout)
```

**Performance:**
- RTFx (Real-Time Factor): 13.5x on CPU, 60x+ on GPU
- Memory: ~1GB RAM for base model
- Latency: ~200-500ms for short clips

---

### 2. **whisper.cpp** ⭐ BEST FOR LOW-RESOURCE
**GitHub:** https://github.com/ggml-org/whisper.cpp

**Why This is Best:**
- C/C++ implementation for maximum performance
- Runs on Raspberry Pi, mobile devices, edge hardware
- Real-time streaming support built-in
- Minimal dependencies

**Key Features:**
- Integer quantization support (Q5_0, Q8_0)
- Apple Silicon acceleration via Core ML
- Metal, CUDA, OpenVINO backends
- Real-time streaming with `whisper-stream`

**Installation:**
```bash
git clone https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
make

# Download model
bash ./models/download-ggml-model.sh base.en
```

**Real-time Usage with Claude Code:**
```bash
# Stream from microphone to Claude Code
./build/bin/whisper-stream \
  -m ./models/ggml-base.en.bin \
  -t 8 \
  --step 500 \
  --length 5000 | \
while IFS= read -r line; do
  echo "$line" | claude
done
```

**Performance:**
- Can run on Raspberry Pi 4
- <100MB RAM usage
- Faster than real-time on most hardware

---

### 3. **WhisperLive** - REAL-TIME SERVER
**GitHub:** https://github.com/collabora/WhisperLive

**Why This is Best:**
- Nearly-live transcription with WebSocket support
- Multiple backend support (faster-whisper, TensorRT, OpenVINO)
- Multi-client server architecture
- Voice Activity Detection (VAD) included

**Key Features:**
- Real-time translation support
- Can save recordings during transcription
- Configurable max clients and connection time
- WebSocket streaming for web interfaces

**Installation:**
```bash
pip install whisper-live
```

**Server Setup:**
```bash
# Start server
python3 run_server.py \
  --port 9090 \
  --backend faster_whisper \
  --max_clients 4

# Client connection streams to Claude Code
python3 run_client.py \
  --host localhost \
  --port 9090 \
  --process_with claude
```

**Use Case:** Perfect for building web-based voice interfaces that connect to Claude Code backend.

---

### 4. **WhisperX** - WORD-LEVEL TIMESTAMPS
**GitHub:** https://github.com/m-bain/whisperX

**Why Use This:**
- 70x real-time speed with batched inference
- Word-level timestamps and speaker diarization
- Under 8GB GPU memory for large-v2

**Best For:** When you need to know exactly when each word was spoken, or who said what in multi-speaker scenarios.

**Installation:**
```bash
pip install whisperx
```

**Usage:**
```bash
whisperx audio.wav \
  --model large-v2 \
  --diarize \
  --highlight_words True
```

---

### 5. **Real-time-STT** - PYTHON WRAPPER
**GitHub:** https://github.com/rudymohammadbali/Real-time-STT

**Why Use This:**
- Simple Python API for real-time STT
- Background listening with thread safety
- Easy integration with existing Python code

**Installation:**
```bash
pip install faster-whisper sounddevice
```

**Usage with Claude Code:**
```python
from real_time_stt import STT
import subprocess
import time

stt = STT(model_size="base.en", device="cuda")
stt.listen()

while stt.is_listening:
    transcription = stt.get_last_transcription()
    if len(transcription) > 0:
        # Send to Claude Code
        result = subprocess.run(
            ['claude'],
            input=transcription,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        
    if "stop" in transcription.lower():
        stt.stop()
    time.sleep(1)
```

---

## 🔊 TEXT-TO-SPEECH (TTS) SOLUTIONS

### 1. **Piper TTS** ⭐ RECOMMENDED
**GitHub:** https://github.com/rhasspy/piper

**Why This is Best:**
- Most natural sounding speech quality
- Extremely fast (5x+ faster than real-time)
- Low resource usage (~50MB RAM)
- 50+ languages with multiple voices per language

**Key Features:**
- Neural TTS with VITS architecture
- Single executable, no Python required
- Voice samples: https://rhasspy.github.io/piper-samples/
- Easy integration via command-line or Python

**Installation:**
```bash
# Download binary
wget https://github.com/rhasspy/piper/releases/download/latest/piper_linux_x86_64.tar.gz
tar -xzf piper_linux_x86_64.tar.gz

# Or via Python
pip install piper-tts
```

**Usage with Claude Code:**
```bash
# Pipe Claude Code output to Piper
echo "What is quantum computing?" | claude | \
  piper --model en_US-lessac-medium \
  --output_file response.wav

# Play the audio
aplay response.wav
```

**Python Integration:**
```python
from piper import PiperVoice
import subprocess

# Get response from Claude Code
result = subprocess.run(
    ['claude'],
    input="Explain relativity simply",
    text=True,
    capture_output=True
)

# Convert to speech
voice = PiperVoice.load("en_US-lessac-medium")
with open("output.wav", "wb") as f:
    voice.synthesize(result.stdout, f)
```

---

### 2. **Coqui TTS (XTTS-v2)** ⭐ VOICE CLONING
**GitHub:** https://github.com/idiap/coqui-ai-TTS

**Why This is Best:**
- Voice cloning with just 6 seconds of audio
- 17 languages supported
- Under 200ms streaming latency
- Production-ready, actively maintained fork

**Key Features:**
- Multiple TTS architectures (VITS, Tacotron2, etc.)
- 1100+ Fairseq models available
- Voice conversion and emotion control
- Both CLI and Python API

**Installation:**
```bash
pip install coqui-tts
```

**Voice Cloning with Claude Code:**
```python
from TTS.api import TTS
import subprocess

# Initialize TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

# Get Claude Code response
result = subprocess.run(
    ['claude'],
    input="Tell me a story",
    text=True,
    capture_output=True
)

# Clone your voice and speak the response
tts.tts_to_file(
    text=result.stdout,
    speaker_wav="my_voice_sample.wav",
    language="en",
    file_path="output.wav"
)
```

**Multilingual Support:**
```python
# Automatic language detection
tts.tts_to_file(
    text="Bonjour le monde",
    speaker_wav="voice.wav",
    language="fr",  # French
    file_path="output.wav"
)
```

---

### 3. **Bark** - EMOTIONAL & CREATIVE
**GitHub:** https://github.com/suno-ai/bark

**Why Use This:**
- Generates emotional and expressive speech
- Can include music, sound effects, laughter
- Multiple languages and accents
- Zero-shot voice cloning

**Best For:** Creative applications, storytelling, character voices, podcasts

**Installation:**
```bash
pip install git+https://github.com/suno-ai/bark.git
```

**Usage with Claude Code:**
```python
from bark import generate_audio, SAMPLE_RATE
import subprocess
import scipy.io.wavfile as wavfile

# Get story from Claude Code
story = subprocess.run(
    ['claude'],
    input="Write a short scary story",
    text=True,
    capture_output=True
).stdout

# Generate with emotion
audio = generate_audio(
    story,
    history_prompt="v2/en_speaker_6"  # Different voices
)

wavfile.write("story.wav", SAMPLE_RATE, audio)
```

---

### 4. **OpenedAI-Speech** - UNIFIED TTS API
**GitHub:** https://github.com/matatonic/openedai-speech

**Why Use This:**
- OpenAI API compatible server
- Supports both Coqui XTTS and Piper backends
- Easy switching between TTS engines
- Voice cloning built-in

**Installation:**
```bash
git clone https://github.com/matatonic/openedai-speech
cd openedai-speech
pip install -r requirements.txt
```

**Server Usage:**
```bash
# Start server
python server.py

# Use with Claude Code
curl -X POST http://localhost:5000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1-hd",
    "input": "$(echo 'Explain AI' | claude)",
    "voice": "alloy"
  }' --output speech.wav
```

---

## 🔄 COMPLETE INTEGRATION ARCHITECTURES

### Architecture 1: Minimal Setup (Best for Beginners)
```
Microphone → whisper.cpp → Claude Code → Piper TTS → Speakers
```

**Setup Script:**
```bash
#!/bin/bash
# Real-time voice assistant

./whisper-stream -m model.bin --step 500 --length 5000 | \
while IFS= read -r line; do
  # Skip empty lines
  [ -z "$line" ] && continue
  
  # Send to Claude Code and get response
  response=$(echo "$line" | claude)
  
  # Speak the response
  echo "$response" | piper --model en_US-lessac-medium --output_file - | aplay
done
```

---

### Architecture 2: Python Integration (Most Flexible)
```
Python Script:
  ├─ faster-whisper (STT)
  ├─ Claude Code (LLM)
  └─ Coqui TTS (TTS with voice cloning)
```

**Full Implementation:**
```python
#!/usr/bin/env python3
"""
Voice Assistant with Claude Code
"""
import subprocess
from faster_whisper import WhisperModel
from TTS.api import TTS
import sounddevice as sd
import numpy as np
import wave
import tempfile
import os

class VoiceAssistant:
    def __init__(self):
        # Initialize STT
        print("Loading Whisper model...")
        self.stt_model = WhisperModel("base.en", device="cpu")
        
        # Initialize TTS
        print("Loading TTS model...")
        self.tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC")
        
        print("Ready!")
    
    def record_audio(self, duration=5, sample_rate=16000):
        """Record audio from microphone"""
        print("Recording...")
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()
        print("Recording complete!")
        return audio, sample_rate
    
    def transcribe(self, audio_file):
        """Convert speech to text"""
        segments, info = self.stt_model.transcribe(audio_file)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    
    def query_claude(self, text):
        """Send query to Claude Code"""
        result = subprocess.run(
            ['claude'],
            input=text,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    
    def speak(self, text, output_file="response.wav"):
        """Convert text to speech"""
        self.tts_model.tts_to_file(text=text, file_path=output_file)
        return output_file
    
    def run(self):
        """Main loop"""
        print("\nVoice Assistant Started!")
        print("Press Ctrl+C to exit\n")
        
        while True:
            try:
                input("Press Enter to speak...")
                
                # Record audio
                audio, sample_rate = self.record_audio(duration=5)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(
                    suffix='.wav', 
                    delete=False
                ) as tmp:
                    with wave.open(tmp.name, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(audio.tobytes())
                    temp_file = tmp.name
                
                # Transcribe
                print("Transcribing...")
                text = self.transcribe(temp_file)
                print(f"You said: {text}")
                
                # Clean up temp file
                os.unlink(temp_file)
                
                if not text:
                    print("No speech detected. Try again.")
                    continue
                
                # Query Claude Code
                print("Thinking...")
                response = self.query_claude(text)
                print(f"Claude: {response}")
                
                # Speak response
                print("Speaking...")
                audio_file = self.speak(response)
                
                # Play audio
                os.system(f"aplay {audio_file}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
```

**Run It:**
```bash
chmod +x voice_assistant.py
./voice_assistant.py
```

---

### Architecture 3: Web-Based (Your Current Setup + Additions)
```
Browser (Web Speech API) → Node.js Server → Claude Code
                              ↓
                         Piper TTS Server → Browser Audio
```

**Enhanced Node.js Server:**
```javascript
const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');

const PORT = 3000;

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    if (req.url === '/transcribe' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            const { text } = JSON.parse(body);
            
            // Send to Claude Code
            const claude = spawn('claude', [], { stdio: ['pipe', 'pipe', 'pipe'] });
            claude.stdin.write(text + '\n');
            claude.stdin.end();
            
            let claudeResponse = '';
            claude.stdout.on('data', data => claudeResponse += data);
            
            claude.on('close', () => {
                // Generate speech with Piper
                const piper = spawn('piper', [
                    '--model', 'en_US-lessac-medium',
                    '--output_file', '-'
                ]);
                
                piper.stdin.write(claudeResponse);
                piper.stdin.end();
                
                let audioBuffer = Buffer.alloc(0);
                piper.stdout.on('data', chunk => {
                    audioBuffer = Buffer.concat([audioBuffer, chunk]);
                });
                
                piper.on('close', () => {
                    res.writeHead(200, {
                        'Content-Type': 'application/json'
                    });
                    res.end(JSON.stringify({
                        text: claudeResponse,
                        audio: audioBuffer.toString('base64')
                    }));
                });
            });
        });
    }
});

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

---

## 📦 RECOMMENDED INSTALLATION SCRIPT

```bash
#!/bin/bash
# Install all recommended tools for voice assistant with Claude Code

echo "🎤 Installing Voice Assistant Components..."

# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip \
    ffmpeg \
    portaudio19-dev \
    alsa-utils \
    build-essential

# Install Python packages
pip3 install \
    faster-whisper \
    coqui-tts \
    sounddevice \
    numpy \
    scipy

# Install Piper TTS
echo "📦 Installing Piper TTS..."
wget https://github.com/rhasspy/piper/releases/download/latest/piper_linux_x86_64.tar.gz
tar -xzf piper_linux_x86_64.tar.gz
sudo mv piper /usr/local/bin/
rm piper_linux_x86_64.tar.gz

# Download Piper voice model
mkdir -p ~/.local/share/piper/voices
cd ~/.local/share/piper/voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Install whisper.cpp (optional, for low-resource devices)
echo "📦 Installing whisper.cpp..."
git clone https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
make -j
bash ./models/download-ggml-model.sh base.en
cd ..

echo "✅ Installation complete!"
echo ""
echo "Test your setup:"
echo "  STT: python3 -c 'from faster_whisper import WhisperModel; print(\"STT ready!\")'"
echo "  TTS: echo 'test' | piper --model en_US-lessac-medium --output_file - | aplay"
echo "  Claude Code: echo 'hello' | claude"
```

---

## 🎯 BEST PRACTICES

### Performance Optimization
1. **Use quantized models** for faster inference
2. **Batch processing** for multiple requests
3. **VAD (Voice Activity Detection)** to avoid processing silence
4. **Async processing** for better responsiveness

### Production Considerations
1. **Error handling** - Always handle timeouts and failures gracefully
2. **Rate limiting** - Prevent resource exhaustion
3. **Logging** - Track performance and errors
4. **Model caching** - Load models once, reuse
5. **Queue system** - For concurrent requests

### Security
1. **Input validation** - Sanitize audio inputs
2. **Resource limits** - Max audio duration, file size
3. **Authentication** - Protect your endpoints
4. **HTTPS** - Encrypt data in transit

---

## 🚀 QUICK START TEMPLATES

### 1. Simple Voice Chat
```bash
# One-liner voice chat with Claude
record -c 1 -r 16000 -t wav - | \
  whisper --model base.en --output_format txt - | \
  claude | \
  piper --model en_US-lessac-medium --output_file - | \
  aplay
```

### 2. Continuous Voice Assistant
```python
# See Architecture 2 above for full implementation
```

### 3. Web Voice Interface
```javascript
// See Architecture 3 above for full implementation
```

---

## 📚 ADDITIONAL RESOURCES

### Model Repositories
- **Whisper Models:** https://huggingface.co/openai
- **Piper Voices:** https://huggingface.co/rhasspy/piper-voices
- **Coqui Models:** https://huggingface.co/coqui

### Community & Support
- Whisper Discussions: https://github.com/openai/whisper/discussions
- Piper Discord: https://discord.gg/rhasspy
- Coqui Discussions: https://github.com/idiap/coqui-ai-TTS/discussions

### Performance Benchmarks
- Open ASR Leaderboard: https://huggingface.co/spaces/hf-audio/open_asr_leaderboard
- TTS Arena: Community-driven TTS model comparisons

---

## 🎉 SUMMARY

**For Your Use Case (Voice → Claude Code → Voice):**

**Easiest Setup:**
- STT: `faster-whisper` (Python API, great performance)
- TTS: `Piper` (fastest, natural voices)

**Best Quality:**
- STT: `WhisperX` (word-level accuracy)
- TTS: `Coqui XTTS-v2` (voice cloning, emotions)

**Lowest Resource:**
- STT: `whisper.cpp` (runs on Raspberry Pi)
- TTS: `Piper` (minimal RAM usage)

**Most Flexible:**
- STT: `WhisperLive` (server-based, multi-client)
- TTS: `Coqui TTS` (1100+ languages, many models)

All of these integrate seamlessly with Claude Code via subprocess calls, HTTP APIs, or direct piping. Choose based on your specific requirements for speed, quality, resource usage, and features!
