#!/usr/bin/env python3
"""
Script to enhance INSA Command Center V2 with TTS and Authentication
"""

# Read the original HTML
with open('insa-command-center-v2.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Additional CSS for login modal and TTS button
additional_css = """
        /* Login Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 2rem;
            max-width: 400px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .modal-title {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.25rem;
            line-height: 1;
        }

        .modal-close:hover {
            color: var(--text-primary);
        }

        .form-group {
            margin-bottom: 1rem;
        }

        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .form-input {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            color: var(--text-primary);
            font-size: 1rem;
            transition: border-color 0.3s;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--primary);
        }

        .form-button {
            width: 100%;
            padding: 0.75rem 1rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            border-radius: 0.5rem;
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .form-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(14, 165, 233, 0.3);
        }

        .form-button:active {
            transform: translateY(0);
        }

        .form-link {
            display: block;
            text-align: center;
            margin-top: 1rem;
            color: var(--primary);
            text-decoration: none;
            font-size: 0.875rem;
        }

        .form-link:hover {
            text-decoration: underline;
        }

        .user-badge {
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid var(--secondary);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            transition: background 0.3s;
        }

        .user-badge:hover {
            background: rgba(139, 92, 246, 0.2);
        }

        .tts-toggle {
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid var(--secondary);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            cursor: pointer;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s;
        }

        .tts-toggle:hover {
            background: rgba(139, 92, 246, 0.2);
        }

        .tts-toggle.active {
            background: var(--secondary);
            color: white;
        }
"""

# Insert additional CSS before the closing </style> tag
html = html.replace('</style>', additional_css + '\n    </style>')

# Add login modal HTML before closing </body> tag
login_modal_html = """
    <!-- Login Modal -->
    <div id="loginModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="modalTitle">Iniciar Sesión</h2>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div id="loginForm">
                <div class="form-group">
                    <label class="form-label">Usuario o Email</label>
                    <input type="text" id="loginUsername" class="form-input" placeholder="usuario@ejemplo.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Contraseña</label>
                    <input type="password" id="loginPassword" class="form-input" placeholder="••••••••">
                </div>
                <button class="form-button" onclick="handleLogin()">Entrar</button>
                <a href="#" class="form-link" onclick="showRegisterForm()">¿No tienes cuenta? Regístrate</a>
            </div>
            <div id="registerForm" style="display:none;">
                <div class="form-group">
                    <label class="form-label">Nombre Completo</label>
                    <input type="text" id="registerFullName" class="form-input" placeholder="Tu nombre">
                </div>
                <div class="form-group">
                    <label class="form-label">Usuario</label>
                    <input type="text" id="registerUsername" class="form-input" placeholder="usuario">
                </div>
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" id="registerEmail" class="form-input" placeholder="correo@ejemplo.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Contraseña</label>
                    <input type="password" id="registerPassword" class="form-input" placeholder="Mínimo 6 caracteres">
                </div>
                <button class="form-button" onclick="handleRegister()">Registrarse</button>
                <a href="#" class="form-link" onclick="showLoginForm()">¿Ya tienes cuenta? Inicia sesión</a>
            </div>
        </div>
    </div>
"""

html = html.replace('</body>', login_modal_html + '\n</body>')

# Update header to include TTS toggle and user badge (before existing status indicators)
header_updates = """                <button class="tts-toggle" id="ttsToggle" onclick="toggleTTS()">
                    <span id="ttsIcon">🔇</span>
                    <span id="ttsText">TTS: OFF</span>
                </button>
                <div class="user-badge" id="userBadge" onclick="showLoginModal()">
                    <span>👤</span>
                    <span id="userBadgeText">Iniciar Sesión</span>
                </div>
"""

# Insert before the status badge div
html = html.replace(
    '<div class="status-badge">',
    header_updates + '                <div class="status-badge">'
)

# Add JavaScript functions before the closing </script> tag
js_additions = """
        // ==================== AUTHENTICATION ====================
        let authToken = localStorage.getItem('auth_token');
        let currentUser = null;

        async function showLoginModal() {
            if (authToken && currentUser) {
                // Already logged in, show logout option
                if (confirm(`Cerrar sesión como ${currentUser.username}?`)) {
                    handleLogout();
                }
            } else {
                document.getElementById('loginModal').classList.add('active');
            }
        }

        function closeModal() {
            document.getElementById('loginModal').classList.remove('active');
        }

        function showLoginForm() {
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('registerForm').style.display = 'none';
            document.getElementById('modalTitle').textContent = 'Iniciar Sesión';
        }

        function showRegisterForm() {
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('registerForm').style.display = 'block';
            document.getElementById('modalTitle').textContent = 'Registrarse';
        }

        async function handleLogin() {
            const username_or_email = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;

            if (!username_or_email || !password) {
                showToast('Por favor completa todos los campos', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username_or_email, password })
                });

                const data = await response.json();

                if (data.success) {
                    authToken = data.token;
                    currentUser = {
                        user_id: data.user_id,
                        username: data.username,
                        email: data.email,
                        full_name: data.full_name
                    };
                    localStorage.setItem('auth_token', authToken);
                    localStorage.setItem('current_user', JSON.stringify(currentUser));

                    updateUserBadge();
                    closeModal();
                    showToast(`¡Bienvenido ${currentUser.username}!`, 'success');

                    // Clear chat to start fresh authenticated session
                    clearChat();
                } else {
                    showToast(data.error || 'Error al iniciar sesión', 'error');
                }
            } catch (error) {
                showToast('Error de conexión', 'error');
                console.error('Login error:', error);
            }
        }

        async function handleRegister() {
            const full_name = document.getElementById('registerFullName').value.trim();
            const username = document.getElementById('registerUsername').value.trim();
            const email = document.getElementById('registerEmail').value.trim();
            const password = document.getElementById('registerPassword').value;

            if (!username || !email || !password) {
                showToast('Por favor completa todos los campos requeridos', 'error');
                return;
            }

            if (password.length < 6) {
                showToast('La contraseña debe tener al menos 6 caracteres', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password, full_name })
                });

                const data = await response.json();

                if (data.success) {
                    showToast('¡Registro exitoso! Ahora inicia sesión', 'success');
                    showLoginForm();
                    document.getElementById('loginUsername').value = username;
                } else {
                    showToast(data.error || 'Error al registrarse', 'error');
                }
            } catch (error) {
                showToast('Error de conexión', 'error');
                console.error('Register error:', error);
            }
        }

        async function handleLogout() {
            try {
                await fetch(`${API_BASE}/auth/logout`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: authToken })
                });
            } catch (error) {
                console.error('Logout error:', error);
            }

            authToken = null;
            currentUser = null;
            localStorage.removeItem('auth_token');
            localStorage.removeItem('current_user');

            updateUserBadge();
            showToast('Sesión cerrada', 'success');
            clearChat();
        }

        function updateUserBadge() {
            const badge = document.getElementById('userBadgeText');
            if (currentUser) {
                badge.textContent = currentUser.full_name || currentUser.username;
            } else {
                badge.textContent = 'Iniciar Sesión';
            }
        }

        async function verifyToken() {
            if (!authToken) return;

            try {
                const response = await fetch(`${API_BASE}/auth/verify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: authToken })
                });

                const data = await response.json();

                if (data.success) {
                    currentUser = data.user;
                    updateUserBadge();
                } else {
                    // Token expired or invalid
                    authToken = null;
                    currentUser = null;
                    localStorage.removeItem('auth_token');
                    localStorage.removeItem('current_user');
                    updateUserBadge();
                }
            } catch (error) {
                console.error('Token verification error:', error);
            }
        }

        // ==================== TEXT-TO-SPEECH ====================
        let ttsEnabled = localStorage.getItem('tts_enabled') === 'true';
        let speechSynthesis = window.speechSynthesis;
        let currentUtterance = null;

        function toggleTTS() {
            ttsEnabled = !ttsEnabled;
            localStorage.setItem('tts_enabled', ttsEnabled);

            const toggle = document.getElementById('ttsToggle');
            const icon = document.getElementById('ttsIcon');
            const text = document.getElementById('ttsText');

            if (ttsEnabled) {
                toggle.classList.add('active');
                icon.textContent = '🔊';
                text.textContent = 'TTS: ON';
                showToast('TTS activado', 'success');
            } else {
                toggle.classList.remove('active');
                icon.textContent = '🔇';
                text.textContent = 'TTS: OFF';
                stopSpeaking();
                showToast('TTS desactivado', 'info');
            }
        }

        function speak(text) {
            if (!ttsEnabled) return;

            // Stop any ongoing speech
            stopSpeaking();

            // Clean up text (remove markdown, emojis, etc.)
            const cleanText = text
                .replace(/\*\*/g, '')  // Remove bold
                .replace(/\*/g, '')    // Remove italic
                .replace(/#{1,6}\s/g, '')  // Remove headers
                .replace(/```[^```]*```/g, '')  // Remove code blocks
                .replace(/`[^`]*`/g, '')  // Remove inline code
                .replace(/\[[^\]]*\]\([^)]*\)/g, '')  // Remove links
                .replace(/[🎤🤖📊🎛️💼🔧🛡️🔬🖥️📐✅⚠️❌📍]/g, '');  // Remove common emojis

            currentUtterance = new SpeechSynthesisUtterance(cleanText);

            // Set Spanish voice if available
            const voices = speechSynthesis.getVoices();
            const spanishVoice = voices.find(voice => voice.lang.startsWith('es'));
            if (spanishVoice) {
                currentUtterance.voice = spanishVoice;
            }
            currentUtterance.lang = 'es-ES';
            currentUtterance.rate = 1.0;
            currentUtterance.pitch = 1.0;
            currentUtterance.volume = 0.9;

            // Event handlers
            currentUtterance.onend = () => {
                currentUtterance = null;
            };

            currentUtterance.onerror = (event) => {
                console.error('TTS error:', event);
                currentUtterance = null;
            };

            speechSynthesis.speak(currentUtterance);
        }

        function stopSpeaking() {
            if (speechSynthesis.speaking) {
                speechSynthesis.cancel();
            }
            currentUtterance = null;
        }

        // Load voices (needed for some browsers)
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = () => {
                speechSynthesis.getVoices();
            };
        }

        // Update TTS button on load
        function updateTTSButton() {
            const toggle = document.getElementById('ttsToggle');
            const icon = document.getElementById('ttsIcon');
            const text = document.getElementById('ttsText');

            if (ttsEnabled) {
                toggle.classList.add('active');
                icon.textContent = '🔊';
                text.textContent = 'TTS: ON';
            } else {
                toggle.classList.remove('active');
                icon.textContent = '🔇';
                text.textContent = 'TTS: OFF';
            }
        }

"""

# Insert before the closing </script> tag
html = html.replace('    </script>', js_additions + '    </script>')

# Update the sendTextMessage function to include auth token and TTS
send_text_update = """        async function sendTextMessage() {
            const input = document.getElementById('textInput');
            const text = input.value.trim();

            if (!text) return;

            input.value = '';
            addMessage('user', text);
            showTyping();

            const formData = new FormData();
            formData.append('text', text);
            if (authToken) {
                formData.append('token', authToken);
            }

            try {
                const response = await fetch(`${API_BASE}/query`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                hideTyping();

                if (data.response) {
                    addMessage('ai', data.response, data.agent || 'general');
                    speak(data.response);  // TTS
                } else {
                    showToast('❌ Sin respuesta del servidor', 'error');
                }
            } catch (error) {
                hideTyping();
                showToast('❌ Error al enviar mensaje', 'error');
            }
        }"""

html = html.replace(
    '''        async function sendTextMessage() {
            const input = document.getElementById('textInput');
            const text = input.value.trim();

            if (!text) return;

            input.value = '';
            addMessage('user', text);
            showTyping();

            const formData = new FormData();
            formData.append('text', text);

            try {
                const response = await fetch(`${API_BASE}/query`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                hideTyping();

                if (data.response) {
                    addMessage('ai', data.response, data.agent || 'general');
                } else {
                    showToast('❌ Sin respuesta del servidor', 'error');
                }
            } catch (error) {
                hideTyping();
                showToast('❌ Error al enviar mensaje', 'error');
            }
        }''',
    send_text_update
)

# Update sendVoiceMessage to include auth token and TTS
send_voice_update = """        async function sendVoiceMessage(audioBlob) {
            showTyping();

            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice.wav');
            if (authToken) {
                formData.append('token', authToken);
            }

            try {
                const response = await fetch(`${API_BASE}/transcribe`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                hideTyping();

                if (data.transcription) {
                    addMessage('user', data.transcription);
                    if (data.response) {
                        addMessage('ai', data.response, data.agent || 'general');
                        speak(data.response);  // TTS
                    }
                } else {
                    showToast('❌ No se detectó voz', 'error');
                }
            } catch (error) {
                hideTyping();
                showToast('❌ Error al procesar audio', 'error');
            }
        }"""

html = html.replace(
    '''        async function sendVoiceMessage(audioBlob) {
            showTyping();

            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice.wav');

            try {
                const response = await fetch(`${API_BASE}/transcribe`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                hideTyping();

                if (data.transcription) {
                    addMessage('user', data.transcription);
                    if (data.response) {
                        addMessage('ai', data.response, data.agent || 'general');
                    }
                } else {
                    showToast('❌ No se detectó voz', 'error');
                }
            } catch (error) {
                hideTyping();
                showToast('❌ Error al procesar audio', 'error');
            }
        }''',
    send_voice_update
)

# Update checkHealth to also verify token and update TTS button
check_health_update = """        async function checkHealth() {
            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();

                if (data.status === 'ok') {
                    document.getElementById('statusText').textContent = 'Sistema Operativo';
                }

                // Verify auth token if exists
                if (authToken) {
                    await verifyToken();
                }

                // Update TTS button state
                updateTTSButton();

                // Load user from localStorage
                const savedUser = localStorage.getItem('current_user');
                if (savedUser && authToken) {
                    currentUser = JSON.parse(savedUser);
                    updateUserBadge();
                }
            } catch (error) {
                document.getElementById('statusText').textContent = 'Sistema Offline';
            }
        }"""

html = html.replace(
    '''        async function checkHealth() {
            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();

                if (data.status === 'ok') {
                    document.getElementById('statusText').textContent = 'Sistema Operativo';
                }
            } catch (error) {
                document.getElementById('statusText').textContent = 'Sistema Offline';
            }
        }''',
    check_health_update
)

# Write the enhanced HTML
with open('insa-command-center-v3.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Enhanced UI created: insa-command-center-v3.html")
print("🔊 TTS support added")
print("🔐 User authentication added")
print("📱 Features:")
print("   - Text-to-Speech toggle button")
print("   - User login/registration modal")
print("   - Session persistence with auth tokens")
print("   - User badge in header")
