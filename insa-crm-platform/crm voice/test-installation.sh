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
