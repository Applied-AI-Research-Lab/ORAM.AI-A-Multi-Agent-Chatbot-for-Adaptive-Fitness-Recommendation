// IIFE (Immediately Invoked Function Expression) to create an isolated scope and prevent global namespace pollution
(function () {
    // Capture the script element and its attributes BEFORE anything else
    // (document.currentScript becomes null after initial script execution)
    // This reference must be captured immediately when the script first runs
    const scriptElement = document.currentScript;

    // Extract API key from the script tag's data-api-key attribute for authentication
    const apiKey = scriptElement.getAttribute('data-api-key');

    // Extract unique user identifier from data-user-key attribute for session management
    const userKey = scriptElement.getAttribute('data-user-key');

    // Extract theme preference (light/dark) from data-theme attribute, defaults to 'light'
    const theme = scriptElement.getAttribute('data-theme') || 'light';

    // Check if stealth mode is enabled (data-stealth-mode="on" means messages won't be saved to database)
    const stealthModeAttr = scriptElement.getAttribute('data-stealth-mode') === 'on';

    // Get conversation mode setting from data-chat-conversation attribute (enables hands-free mode)
    const chatConversationAttr = scriptElement.getAttribute('data-chat-conversation');

    // Get auto-speak setting from data-chat-speaker attribute (enables TTS for bot responses)
    const chatSpeakerAttr = scriptElement.getAttribute('data-chat-speaker');

    // Get microphone button setting from data-chat-mic-btn attribute (enables voice input)
    const chatMicBtnAttr = scriptElement.getAttribute('data-chat-mic-btn');

    // Extract UI language from data-chat-ui-lang attribute, defaults to 'en' (English)
    const uiLang = scriptElement.getAttribute('data-chat-ui-lang') || 'en';

    // Check if fullscreen mode is enabled from data-fullscreen attribute
    const fullscreen = scriptElement.getAttribute('data-fullscreen') === 'on';

    // LANGUAGE CONFIGURATION - Store the selected language code for UI translations
    const LANGUAGE = uiLang; // Get from HTML attribute (e.g., 'en', 'el')

    // Get translations object from globally loaded language file
    // The language file (en.js or el.js) was loaded before this script by the server based on ?lang= parameter
    // Each language file exports translations to window[LANGUAGE] (e.g., window['en'] or window['el'])
    const t = window[LANGUAGE];

    // Fallback mechanism if translation file failed to load or wasn't included
    if (!t) {
        // Log error to console for debugging
        console.error(`Language '${LANGUAGE}' not loaded. Using fallback empty object.`);

        // Create a minimal fallback object with essential UI text to prevent errors
        const fallback = {
            headerTitle: 'ORAM.AI',
            inputPlaceholder: 'Type your message...',
            clearHistory: 'Clear history',
            close: 'Close'
        };

        // Assign fallback to the global window object so the rest of the code works
        window[LANGUAGE] = fallback;
    }

    // MASTER FEATURE FLAGS - Global switches to enable/disable features for all users
    // Change these to control which features are available globally across all widget instances
    const MASTER_FEATURES = {
        conversationMode: true,  // Hands-free conversation mode (continuous listening and speaking)
        autoSpeak: true,         // Text-to-speech for bot responses
        voiceInput: true         // Voice input via microphone
    };

    // Note: Domain and API key restrictions are now handled server-side in app.py
    // The chat-loader.js sends domain and API key to the server for validation
    // This ensures security is enforced on the backend, not just the frontend

    // Extract the base URL from the script's source to make API calls to the same server
    // The script source is set by chat-loader.js which captures it from its own URL
    const scriptSrc = scriptElement.src;
    // Remove '/embed/chat.js' to get the base domain (e.g., 'https://my-orama.my-domain.com')
    const baseApiUrl = scriptSrc ? scriptSrc.replace(/\/embed\/chat\.js.*$/, '') : window.location.origin;

    // Configuration object - Central configuration for the chat widget instance
    const config = {
        apiKey: apiKey,                    // API key for authentication with backend
        userKey: userKey,                  // Unique user identifier for session management
        theme: theme,                      // Visual theme (light/dark)
        stealthMode: stealthModeAttr,      // Whether to save messages to database or only session storage
        apiUrl: `${baseApiUrl}/chat`,      // Backend API endpoint for chat messages (dynamic based on script origin)

        // Feature toggles - Each feature is enabled only if BOTH conditions are true:
        // 1. MASTER_FEATURES flag is true (global enable)
        // 2. HTML attribute is NOT explicitly set to 'off' (per-instance enable)
        enableConversation: MASTER_FEATURES.conversationMode && chatConversationAttr !== 'off',
        enableSpeaker: MASTER_FEATURES.autoSpeak && chatSpeakerAttr !== 'off',
        enableMic: MASTER_FEATURES.voiceInput && chatMicBtnAttr !== 'off',
        fullscreen: fullscreen
    };

    // Session storage key for stealth mode - unique per user to isolate chat histories
    const sessionKey = `chat_history_${config.userKey}`;

    // Initialize or retrieve session storage for stealth mode
    // In stealth mode, messages are stored only in browser's sessionStorage (not persisted to database)
    let sessionMessages = [];

    // Check if stealth mode is enabled
    if (config.stealthMode) {
        // Try to retrieve existing chat history from sessionStorage
        const stored = sessionStorage.getItem(sessionKey);

        // If history exists, parse JSON string back to array of message objects
        if (stored) {
            sessionMessages = JSON.parse(stored);
        }
    }

    // Load Bootstrap CSS and Icons if not already present on the page
    // This check prevents duplicate CSS loading if Bootstrap is already included by the host page
    if (!document.querySelector('link[href*="bootstrap"]')) {
        // Create link element for Bootstrap CSS framework
        const bootstrapCSS = document.createElement('link');
        bootstrapCSS.rel = 'stylesheet'; // Define as stylesheet
        bootstrapCSS.href = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css'; // CDN URL
        document.head.appendChild(bootstrapCSS); // Add to document head

        // Create link element for Bootstrap Icons font
        const bootstrapIcons = document.createElement('link');
        bootstrapIcons.rel = 'stylesheet'; // Define as stylesheet
        bootstrapIcons.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css'; // CDN URL
        document.head.appendChild(bootstrapIcons); // Add to document head
    }

    // Create chat widget HTML structure using template literal
    // This is the main chat interface that users interact with
    const chatHTML = `
        <div id="chat-widget" class="position-fixed bottom-0 end-0 m-3 transition-all ${config.fullscreen ? 'chat-maximized' : ''}" style="z-index: 1000; width: 350px;">
            <!-- Main chat card container with conditional dark theme styling -->
            <div class="card ${config.theme === 'dark' ? 'bg-dark text-white' : ''}" id="chat-card">
                <!-- Header section with title and control buttons -->
                <div class="card-header d-flex justify-content-between align-items-center">
                    <!-- Chat title from translation file -->
                    <span>${t.headerTitle}</span>
                    
                    <!-- Control buttons group -->
                    <div class="d-flex gap-2">
                        <!-- Clear chat history button -->
                        <button class="btn btn-sm btn-link text-decoration-none p-0" id="chat-clear" title="${t.clearHistory}">
                            <i class="bi bi-trash"></i>
                        </button>
                        
                        <!-- Maximize/restore button -->
                        <button class="btn btn-sm btn-link text-decoration-none p-0" id="chat-maximize">
                            <i class="bi bi-arrows-angle-expand"></i>
                        </button>
                        
                        <!-- Close/minimize button -->
                        <button class="btn btn-sm btn-link text-decoration-none p-0" id="chat-close" title="${t.close}">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Chat messages container with fixed height and vertical scrolling -->
                <div class="card-body" style="height: 400px; overflow-y: auto;">
                    <!-- Messages will be dynamically added to this container -->
                    <div id="chat-messages" class="d-flex flex-column gap-2"></div>
                </div>
                
                <!-- Footer section containing the input form and feature controls -->
                <div class="card-footer p-0">
                    <!-- Main input form for typing and sending messages -->
                    <form id="chat-form" class="d-flex gap-2 p-3 align-items-center" style="background: #f8f9fa; position: relative;">
                        
                        <!-- Features menu button container (stealth mode, voice, etc.) -->
                        <div style="position: relative;" id="features-menu-container">
                            <!-- Three-dots menu button to show/hide features dropdown -->
                            <button type="button" class="btn btn-sm p-1" id="features-menu-btn" style="background: transparent; border: 1px solid #dee2e6; color: #6c757d; width: 36px; height: 36px; border-radius: 8px;">
                                <i class="bi bi-three-dots-vertical" style="font-size: 16px;"></i>
                            </button>
                            
                            <!-- Dropdown menu with advanced features (initially hidden) -->
                            <div id="features-dropdown" style="
                                position: absolute;
                                bottom: 45px;
                                left: 0;
                                background: white;
                                border: 1px solid #dee2e6;
                                border-radius: 12px;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                padding: 8px;
                                min-width: 180px;
                                display: none;
                                z-index: 1000;
                            ">
                                ${config.enableConversation ? `
                                <button type="button" class="btn btn-sm w-100 text-start d-flex align-items-center gap-2 mb-1" id="chat-conversation" style="background: transparent; border: none; color: #6c757d; padding: 8px 12px; border-radius: 6px; transition: all 0.2s ease;">
                                    <i class="bi bi-chat-left-dots" style="font-size: 16px;"></i>
                                    <span style="font-size: 13px;">${t.conversation}</span>
                                </button>
                                ` : ''}
                                ${config.enableMic ? `
                                <button type="button" class="btn btn-sm w-100 text-start d-flex align-items-center gap-2 mb-1" id="chat-mic-btn" style="background: transparent; border: none; color: #6c757d; padding: 8px 12px; border-radius: 6px; transition: all 0.2s ease;">
                                    <i class="bi bi-mic-fill" style="font-size: 16px;"></i>
                                    <span style="font-size: 13px;">${t.voiceInput}</span>
                                </button>
                                ` : ''}
                                ${config.enableSpeaker ? `
                                <button type="button" class="btn btn-sm w-100 text-start d-flex align-items-center gap-2 mb-1" id="chat-speaker" style="background: transparent; border: none; color: #6c757d; padding: 8px 12px; border-radius: 6px; transition: all 0.2s ease;">
                                    <i class="bi bi-volume-mute-fill" style="font-size: 16px;"></i>
                                    <span style="font-size: 13px;">${t.autoSpeak}</span>
                                </button>
                                ` : ''}
                                <button type="button" class="btn btn-sm w-100 text-start d-flex align-items-center gap-2" id="chat-stealth" style="background: transparent; border: none; color: #6c757d; padding: 8px 12px; border-radius: 6px; transition: all 0.2s ease;">
                                    <i class="bi bi-shield-lock-fill" style="font-size: 16px;"></i>
                                    <span style="font-size: 13px;">${t.stealthMode}</span>
                                </button>
                            </div>
                        </div>
                        <input type="text" class="form-control" id="chat-input" placeholder="${t.inputPlaceholder}" style="border-radius: 20px;">
                        <button type="submit" class="btn btn-primary" id="chat-send-btn" style="border-radius: 50%; width: 40px; height: 40px; padding: 0;">
                            <i class="bi bi-send-fill"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    `;

    // Create minimized chat icon HTML - displayed when chat is closed
    // This provides a way for users to reopen the chat widget
    const minimizedChatHTML = `
        <div id="chat-widget-minimized" class="position-fixed bottom-0 end-0 m-3 d-none" style="z-index: 1000;">
            <!-- Circular floating button with chat icon -->
            <button class="btn btn-primary rounded-circle p-3 d-flex align-items-center justify-content-center" 
                    style="width: 60px; height: 60px;" id="chat-expand">
                <i class="bi bi-chat-dots-fill fs-4"></i>
            </button>
        </div>
    `;

    // Create Bootstrap modal dialogs for user confirmations
    // Modals are used to confirm destructive actions before executing them
    const modalsHTML = `
        <!-- Stealth Mode Modal - Confirms enabling stealth mode -->
        <!-- (Currently not actively used, but available for future implementation) -->
        <div class="modal fade" id="stealthModeModal" tabindex="-1" aria-labelledby="stealthModeModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <!-- Modal header with title and close button -->
                    <div class="modal-header">
                        <h5 class="modal-title" id="stealthModeModalLabel">Stealth Mode</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    
                    <!-- Modal body with confirmation message -->
                    <div class="modal-body" id="stealthModeModalBody">
                        Are you sure you want to enable stealth mode? New messages will not be stored in the database.
                    </div>
                    
                    <!-- Modal footer with action buttons -->
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirmStealthMode">Confirm</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Clear Chat Modal - Confirms clearing chat history -->
        <div class="modal fade" id="clearChatModal" tabindex="-1" aria-labelledby="clearChatModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <!-- Modal header with title and close button -->
                    <div class="modal-header">
                        <h5 class="modal-title" id="clearChatModalLabel">Clear Chat History</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    
                    <!-- Modal body with warning message -->
                    <div class="modal-body">
                        Are you sure you want to clear the chat history? This cannot be undone.
                    </div>
                    
                    <!-- Modal footer with action buttons -->
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" id="confirmClearChat">Clear Chat</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Create container element and inject all HTML into the page
    const container = document.createElement('div');
    // Combine all HTML templates into a single innerHTML assignment
    container.innerHTML = chatHTML + minimizedChatHTML + modalsHTML;
    // Append the entire widget structure to the document body
    document.body.appendChild(container);

    // Load Bootstrap JavaScript if not already present on the page
    // Bootstrap JS is needed for modal functionality and other interactive components
    if (!document.querySelector('script[src*="bootstrap.bundle.min.js"]')) {
        // Create script element for Bootstrap bundle (includes Popper.js)
        const bootstrapJS = document.createElement('script');
        bootstrapJS.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js';
        // Append to body (script will load asynchronously)
        document.body.appendChild(bootstrapJS);
    }

    // Function to scroll to bottom of chat messages container
    // Used after loading history or when new messages are added
    function scrollToBottom(delay = 100) {
        // Use setTimeout to allow DOM to update before scrolling
        setTimeout(() => {
            // Scroll the chat messages container to the bottom
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,  // scrollHeight gives total height of content
                behavior: 'instant'              // 'instant' = no animation, 'smooth' = animated
            });
        }, delay); // Default delay of 100ms ensures DOM has rendered
    }

    // Function to load chat history on widget initialization
    // Retrieves messages from either sessionStorage (stealth mode) or backend API (normal mode)
    async function loadChatHistory() {
        try {
            // Check if stealth mode is enabled
            if (config.stealthMode) {
                // In stealth mode: Load from browser's sessionStorage only
                if (sessionMessages.length === 0) {
                    // No history exists, show welcome message
                    addMessage(t.welcomeMessage, false);
                } else {
                    // Display each stored message from sessionStorage
                    sessionMessages.forEach(msg => {
                        // msg.role === 'user' determines message alignment (right for user, left for bot)
                        // true parameter indicates this is an initial load (affects scrolling behavior)
                        addMessage(msg.content, msg.role === 'user', true);
                    });
                }
                // Scroll to bottom to show most recent messages
                scrollToBottom();
            } else {
                // In normal mode: Load from server database via API
                // Construct the history endpoint URL with userKey as query parameter
                const historyUrl = `${config.apiUrl.replace('/chat', '/chat/history')}?userKey=${config.userKey}`;

                // Debug logging for troubleshooting
                console.log('Loading chat history from:', historyUrl);
                console.log('Using API key:', config.apiKey);
                console.log('Using user key:', config.userKey);

                // Make GET request to backend to retrieve chat history
                const response = await fetch(historyUrl, {
                    method: 'GET',
                    headers: {
                        // Send API key in Authorization header for authentication
                        'Authorization': `Bearer ${config.apiKey}`
                    }
                });

                // Check if request was successful
                if (!response.ok) {
                    // Parse error response from server
                    const errorData = await response.json();
                    throw new Error(`Failed to load chat history: ${errorData.error || response.statusText}`);
                }

                // Parse successful response as JSON
                const data = await response.json();

                // Display messages in chat UI
                if (data.messages.length === 0) {
                    // No history found, show welcome message
                    addMessage(t.welcomeMessage, false);
                } else {
                    // Display each message from the database
                    data.messages.forEach(msg => {
                        // true parameter indicates initial load (affects scrolling)
                        addMessage(msg.content, msg.role === 'user', true);
                    });
                }
                // Scroll to bottom to show most recent messages
                scrollToBottom();
            }
        } catch (error) {
            // Handle any errors during history loading
            console.error('Error loading chat history:', error);
            // Display error message to user
            addMessage(t.loadHistoryFailed, false);
        }
    }

    // Load chat history when widget is initialized (called immediately on script execution)
    loadChatHistory();

    // Add custom CSS styles dynamically to the page
    // These styles provide animations, themes, and visual effects for the widget
    const styles = document.createElement('style');
    styles.textContent = `
        /* Smooth transition for all properties (used for animations) */
        .transition-all {
            transition: all 0.3s ease-in-out;
        }
        
        /* Maximized chat widget styles - takes full viewport */
        .chat-maximized {
            width: 100% !important;      /* Full width */
            height: 100vh !important;    /* Full viewport height */
            margin: 0 !important;        /* Remove margins */
        }
        .chat-maximized .card {
            height: 100vh;               /* Full height card */
            border-radius: 0;            /* Remove rounded corners when maximized */
        }
        .chat-maximized .card-body {
            height: calc(100vh - 120px) !important; /* Subtract header and footer height */
        }
        
        /* Recording indicator style with gradient and pulse animation */
        .recording {
            background: linear-gradient(135deg, #f093fb, #f5576c) !important;
            animation: pulse 1.5s infinite !important;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }    /* Normal size */
            50% { transform: scale(1.05); }      /* Slightly larger */
        }
        
        /* Default header color */
        .card-header {
            color: rgb(108, 117, 125);           /* Gray color */
        }
        .card-header * {
            color: rgb(108, 117, 125);           /* Apply to all child elements */
        }
        
        /* Conversation mode active indicator - gradient background with glow animation */
        .conversation-active .card-header {
            background: linear-gradient(135deg, #a8edea, #fed6e3) !important; /* Teal to pink gradient */
            animation: glow 2s ease-in-out infinite !important;
        }
        @keyframes glow {
            0%, 100% { opacity: 1; }             /* Full opacity */
            50% { opacity: 0.8; }                /* Slightly transparent */
        }
        
        /* Stealth mode active indicator - dark background with subtle glow */
        .stealth-active .card-header {
            background: rgb(108, 117, 125) !important; /* Dark gray background */
            animation: stealthGlow 2s ease-in-out infinite !important;
            color: white !important;             /* White text for contrast */
        }
        .stealth-active .card-header * {
            color: white !important;             /* White text for all child elements */
        }
        @keyframes stealthGlow {
            0%, 100% { opacity: 1; }             /* Full opacity */
            50% { opacity: 0.9; }                /* Slightly transparent */
        }
    `;
    // Inject the styles into the document head
    document.head.appendChild(styles);

    // DOM element references - Cache references to frequently accessed elements for better performance
    const chatWidget = document.getElementById('chat-widget');              // Main widget container
    const chatCard = document.getElementById('chat-card');                  // Chat card element
    const minimizedWidget = document.getElementById('chat-widget-minimized'); // Minimized floating button
    const chatForm = document.getElementById('chat-form');                  // Message input form
    const chatInput = document.getElementById('chat-input');                // Text input field
    const chatMessages = document.getElementById('chat-messages');          // Messages container
    const chatClose = document.getElementById('chat-close');                // Close button
    const chatMinimize = document.getElementById('chat-minimize');          // Minimize button (may not exist)
    const chatMaximize = document.getElementById('chat-maximize');          // Maximize/restore button
    const chatExpand = document.getElementById('chat-expand');              // Expand from minimized button
    const chatClear = document.getElementById('chat-clear');                // Clear history button
    const chatStealth = document.getElementById('chat-stealth');            // Stealth mode toggle

    // Conditional element references - Only get references if features are enabled
    const chatSpeaker = config.enableSpeaker ? document.getElementById('chat-speaker') : null;  // Auto-speak toggle
    const chatConversation = config.enableConversation ? document.getElementById('chat-conversation') : null; // Conversation mode toggle
    const chatSendBtn = document.getElementById('chat-send-btn');           // Send message button
    const chatMicBtn = config.enableMic ? document.getElementById('chat-mic-btn') : null; // Microphone button

    // Features menu elements for the dropdown menu
    const featuresMenuBtn = document.getElementById('features-menu-btn');   // Three-dots menu button
    const featuresDropdown = document.getElementById('features-dropdown');  // Dropdown container
    const featuresMenuContainer = document.getElementById('features-menu-container'); // Menu wrapper
    let featuresMenuOpen = false; // Track dropdown open/close state

    // Widget state variables
    let isMaximized = config.fullscreen; // Track if widget is in maximized (fullscreen) mode

    // Set initial maximize button icon based on fullscreen state
    if (isMaximized) {
        chatMaximize.innerHTML = '<i class="bi bi-arrows-angle-contract"></i>';
    }

    // Voice recording variables
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    // Auto-speak state
    let autoSpeakEnabled = false;
    let currentAudio = null;

    // Conversation mode state
    let conversationModeEnabled = false;
    let conversationRecorder = null;
    let conversationChunks = [];
    let silenceTimer = null;
    let audioContext = null;
    let analyser = null;
    let silenceThreshold = 10; // Minimum average volume to consider as speech
    let silenceDuration = 5000; // 5 seconds
    let isProcessingConversation = false;
    let hasDetectedSpeech = false; // Track if we've detected actual speech
    let consecutiveSilentFrames = 0; // Count silent frames
    let requiredSilentFrames = 75;          // ~5 seconds at 15 fps (frames needed before stopping)

    // Update stealth mode icon and styling based on current state
    // This provides visual feedback to users about whether stealth mode is active
    function updateStealthIcon() {
        // Get the icon element inside the stealth button
        const stealthIcon = chatStealth.querySelector('i');

        if (config.stealthMode) {
            // Stealth mode is ON - show locked shield icon
            stealthIcon.className = 'bi bi-shield-lock-fill';
            chatStealth.title = t.stealthOnTitle;  // Tooltip text
            // Add 3D pressed/active effect
            chatStealth.style.boxShadow = 'inset 2px 2px 5px rgba(0,0,0,0.2)';
            chatStealth.style.transform = 'scale(0.95)';
            // Add CSS class to change header styling
            chatCard.classList.add('stealth-active');
        } else {
            // Stealth mode is OFF - show slash through shield icon
            stealthIcon.className = 'bi bi-shield-slash';
            chatStealth.title = t.stealthOffTitle; // Tooltip text
            // Remove pressed effect
            chatStealth.style.boxShadow = '';
            chatStealth.style.transform = '';
            // Remove header styling
            chatCard.classList.remove('stealth-active');
        }
    }

    // Initialize stealth icon on page load to match current state
    updateStealthIcon();

    // Update speaker (auto-speak/TTS) icon and styling based on current state
    // Provides visual feedback about whether auto-speak is enabled
    function updateSpeakerIcon() {
        // Exit early if speaker feature is not enabled
        if (!chatSpeaker) return;

        // Get the icon element inside the speaker button
        const speakerIcon = chatSpeaker.querySelector('i');

        if (autoSpeakEnabled) {
            // Auto-speak is ON - show volume up icon
            speakerIcon.className = 'bi bi-volume-up-fill';
            chatSpeaker.title = t.autoSpeakOnTitle;  // Tooltip text
            // Add 3D pressed/active effect
            chatSpeaker.style.boxShadow = 'inset 2px 2px 5px rgba(0,0,0,0.2)';
            chatSpeaker.style.transform = 'scale(0.95)';
        } else {
            // Auto-speak is OFF - show muted volume icon
            speakerIcon.className = 'bi bi-volume-mute-fill';
            chatSpeaker.title = t.autoSpeakOffTitle; // Tooltip text
            // Remove pressed effect
            chatSpeaker.style.boxShadow = '';
            chatSpeaker.style.transform = '';
        }
    }

    // Function to speak text using Text-to-Speech (TTS)
    // Converts bot responses to audio and plays them automatically
    async function speakText(text) {
        if (!text || !autoSpeakEnabled) return;

        // Stop any currently playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }

        try {
            const baseUrl = config.apiUrl.replace('/chat', '');
            const response = await fetch(`${baseUrl}/api/speak`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) throw new Error('TTS request failed');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            currentAudio = new Audio(url);

            currentAudio.play();

            // Clean up when audio finishes
            currentAudio.onended = () => {
                URL.revokeObjectURL(url);
                currentAudio = null;
            };
        } catch (error) {
            console.error('Error speaking text:', error);
        }
    }

    // Conversation mode TTS - Speak text and call callback when done
    // Used in conversation mode to chain: speak response -> start listening again
    function speakTextConversation(text, onEndCallback) {
        // If no text provided, immediately call callback to continue conversation flow
        if (!text) {
            console.log('No text to speak, calling callback immediately');
            if (onEndCallback) onEndCallback();
            return;
        }

        // Stop any currently playing audio to prevent overlapping
        if (currentAudio) {
            currentAudio.pause();  // Stop current playback
            currentAudio = null;   // Clear reference
        }

        console.log('Starting TTS for conversation mode...');

        // Construct base URL for TTS API endpoint
        const baseUrl = config.apiUrl.replace('/chat', '');

        // Send text to TTS API
        fetch(`${baseUrl}/api/speak`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        })
            .then(response => {
                if (!response.ok) throw new Error('TTS request failed');
                return response.blob();
            })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                currentAudio = new Audio(url);

                // Set up event handlers before playing
                currentAudio.onended = () => {
                    console.log('Audio playback ended, triggering callback...');
                    URL.revokeObjectURL(url);
                    currentAudio = null;
                    if (onEndCallback) {
                        console.log('Calling onEndCallback...');
                        onEndCallback();
                    }
                };

                // Also handle errors
                currentAudio.onerror = (e) => {
                    console.error('Audio playback error:', e);
                    URL.revokeObjectURL(url);
                    currentAudio = null;
                    if (onEndCallback) {
                        onEndCallback();
                    }
                };

                console.log('Starting audio playback...');
                currentAudio.play().catch(e => {
                    console.error('Error playing audio:', e);
                    URL.revokeObjectURL(url);
                    currentAudio = null;
                    if (onEndCallback) {
                        onEndCallback();
                    }
                });
            })
            .catch(error => {
                console.error('Error in TTS:', error);
                if (onEndCallback) {
                    onEndCallback();
                }
            });
    }

    // Update conversation mode icon and styling based on current state
    // Provides visual feedback about whether hands-free conversation mode is active
    function updateConversationIcon() {
        // Exit early if conversation feature is not enabled
        if (!chatConversation) return;

        // Get the icon element inside the conversation button
        const conversationIcon = chatConversation.querySelector('i');

        if (conversationModeEnabled) {
            // Conversation mode is ON - show filled chat icon
            conversationIcon.className = 'bi bi-chat-left-dots-fill';
            chatConversation.title = t.conversationOnTitle;  // Tooltip text
            // Add 3D pressed/active effect
            chatConversation.style.boxShadow = 'inset 2px 2px 5px rgba(0,0,0,0.2)';
            chatConversation.style.transform = 'scale(0.95)';
            // Add CSS class to change header styling (gradient animation)
            chatCard.classList.add('conversation-active');
        } else {
            // Conversation mode is OFF - show outline chat icon
            conversationIcon.className = 'bi bi-chat-left-dots';
            chatConversation.title = t.conversationOffTitle;  // Tooltip text
            // Remove pressed effect
            chatConversation.style.boxShadow = '';
            chatConversation.style.transform = '';
            // Remove header styling
            chatCard.classList.remove('conversation-active');
        }
    }

    // Start conversation mode recording - Initiates continuous listening
    // This function sets up microphone access and voice activity detection
    async function startConversationRecording() {
        try {
            // Request microphone access from user
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Determine best supported audio format (browser compatibility)
            // Prefer mp4, fallback to mpeg, then webm
            const mimeType = MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' :
                MediaRecorder.isTypeSupported('audio/mpeg') ? 'audio/mpeg' :
                    'audio/webm';

            // Create MediaRecorder instance with the audio stream
            conversationRecorder = new MediaRecorder(stream, { mimeType });
            // Clear any previous audio chunks
            conversationChunks = [];

            // Event handler: Called repeatedly as audio data becomes available
            conversationRecorder.ondataavailable = (event) => {
                conversationChunks.push(event.data);  // Accumulate audio chunks
            };

            // Event handler: Called when recording stops
            conversationRecorder.onstop = processConversationRecording;

            // Setup Web Audio API for real-time silence detection
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);  // Create audio source from mic stream
            analyser = audioContext.createAnalyser();  // Create analyser for frequency data
            analyser.fftSize = 2048;  // FFT size (affects frequency resolution)
            source.connect(analyser);  // Connect source to analyser

            // Start recording
            conversationRecorder.start();

            // Reset speech detection state for new recording session
            hasDetectedSpeech = false;           // Haven't detected speech yet
            consecutiveSilentFrames = 0;         // Reset silence counter

            // Start monitoring audio levels to detect silence
            monitorSilence();

            // Update UI to show listening state
            chatInput.placeholder = t.listening;  // Change placeholder text
            chatInput.disabled = true;            // Disable text input
            chatSendBtn.disabled = true;          // Disable send button
            if (chatMicBtn) chatMicBtn.disabled = true;  // Disable mic button
        } catch (error) {
            // Handle errors (typically microphone permission denied)
            console.error('Error starting conversation recording:', error);
            addMessage(t.microphoneError + error.message, false);  // Show error to user
            stopConversationMode();  // Clean up and exit conversation mode
        }
    }

    // Monitor for silence with improved voice activity detection
    // This function continuously analyzes audio to detect when user stops speaking
    function monitorSilence() {
        // Exit if conversation mode was disabled or analyser not available
        if (!conversationModeEnabled || !analyser) return;

        // Get the size of the frequency data array
        const bufferLength = analyser.frequencyBinCount;
        // Create array to hold frequency data (0-255 values)
        const dataArray = new Uint8Array(bufferLength);
        // Reset speech detection flags
        hasDetectedSpeech = false;
        consecutiveSilentFrames = 0;

        // Inner function that checks audio level on each animation frame
        function checkAudioLevel() {
            // Exit if mode was disabled during monitoring
            if (!conversationModeEnabled || !analyser) return;

            analyser.getByteFrequencyData(dataArray);

            // Calculate average volume in human speech frequency range (85-255 Hz approximately)
            // Focus on lower frequency bins which contain most speech energy
            let speechSum = 0;
            const speechBins = Math.min(50, bufferLength); // Focus on first 50 bins (speech frequencies)

            for (let i = 0; i < speechBins; i++) {
                speechSum += dataArray[i];
            }
            const speechAverage = speechSum / speechBins;

            // Also calculate overall energy for comparison
            let totalSum = 0;
            for (let i = 0; i < bufferLength; i++) {
                totalSum += dataArray[i];
            }
            const totalAverage = totalSum / bufferLength;

            // Determine if this is likely speech (higher energy in speech frequencies)
            const isSpeech = speechAverage > silenceThreshold;

            if (isSpeech) {
                // Speech detected
                hasDetectedSpeech = true;
                consecutiveSilentFrames = 0;

                // Update UI to show we're hearing speech
                if (chatInput.placeholder === t.listening) {
                    chatInput.placeholder = t.listeningMic;
                }
            } else if (hasDetectedSpeech) {
                // We've heard speech before, now counting silence
                consecutiveSilentFrames++;

                // Calculate remaining seconds
                const remainingFrames = requiredSilentFrames - consecutiveSilentFrames;
                const remainingSeconds = Math.ceil(remainingFrames / 15); // ~15 frames per second

                if (remainingSeconds > 0 && remainingSeconds <= 5) {
                    chatInput.placeholder = `Finishing in ${remainingSeconds}s...`;
                }

                // If we've been silent long enough, stop recording
                if (consecutiveSilentFrames >= requiredSilentFrames) {
                    if (conversationModeEnabled && conversationRecorder && conversationRecorder.state === 'recording') {
                        console.log('Silence detected after speech, stopping recording...');
                        conversationRecorder.stop();
                        return; // Stop monitoring
                    }
                }
            }

            // Continue monitoring
            requestAnimationFrame(checkAudioLevel);
        }

        checkAudioLevel();
    }

    // Process conversation recording - Transcribe audio and send as message
    // Called automatically when recording stops (after silence detected)
    async function processConversationRecording() {
        // Prevent overlapping processing if already running
        if (isProcessingConversation) return;
        isProcessingConversation = true;  // Set lock

        // Get the MIME type that was used for recording
        const mimeType = conversationRecorder.mimeType || 'audio/webm';
        // Determine appropriate file extension based on MIME type
        const extension = mimeType.includes('mp4') ? 'mp4' :
            mimeType.includes('mpeg') ? 'mp3' : 'webm';

        // Create a Blob from all recorded audio chunks
        const audioBlob = new Blob(conversationChunks, { type: mimeType });
        // Create FormData to send audio file to server
        const formData = new FormData();
        formData.append('audio', audioBlob, `audio.${extension}`);

        try {
            // Update UI to show transcription in progress
            chatInput.placeholder = t.transcribing;

            // Construct base URL for transcription API endpoint
            const baseUrl = config.apiUrl.replace('/chat', '');
            // Send audio to transcription endpoint
            const response = await fetch(`${baseUrl}/api/transcribe`, {
                method: 'POST',
                body: formData  // FormData contains the audio file
            });

            // Parse response JSON
            const data = await response.json();

            // Check if transcription was successful and contains text
            if (data.success && data.transcript.trim()) {
                // Transcription successful - send as chat message
                chatInput.placeholder = t.sendingMessage;
                await sendMessageConversation(data.transcript);
            } else {
                // No speech detected or transcription failed - restart listening
                if (conversationModeEnabled) {
                    chatInput.placeholder = t.noSpeechDetected;
                    // Wait 1 second before restarting to give user feedback
                    setTimeout(() => {
                        // Check if still in conversation mode before restarting
                        if (conversationModeEnabled) {
                            startConversationRecording();
                        }
                    }, 1000);
                }
            }
        } catch (error) {
            // Handle transcription errors
            console.error('Error transcribing audio:', error);
            // Restart listening if still in conversation mode
            if (conversationModeEnabled) {
                chatInput.placeholder = t.errorListeningAgain;
                setTimeout(() => {
                    if (conversationModeEnabled) {
                        startConversationRecording();
                    }
                }, 1000);
            }
        } finally {
            // Release processing lock
            isProcessingConversation = false;
        }
    }

    // Send message in conversation mode - Sends transcribed text as chat message
    // Similar to sendMessage() but with conversation-specific flow (speak then listen again)
    async function sendMessageConversation(message) {
        // Exit if message is empty
        if (!message || !message.trim()) return;

        // Trim whitespace from message
        message = message.trim();

        // Add user message to chat UI
        addMessage(message, true);

        try {
            // If in stealth mode, add message to session storage
            if (config.stealthMode) {
                sessionMessages.push({
                    role: 'user',                      // Mark as user message
                    content: message,                  // The message text
                    timestamp: new Date().toISOString()  // ISO timestamp
                });
                // Persist to sessionStorage
                sessionStorage.setItem(sessionKey, JSON.stringify(sessionMessages));
            }

            // Update UI to show we're waiting for response
            chatInput.placeholder = t.gettingResponse;

            // Send message to chat API
            const response = await fetch(config.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${config.apiKey}`  // API key for authentication
                },
                body: JSON.stringify({
                    message,                           // User's message
                    userKey: config.userKey,          // User identifier
                    stealthMode: config.stealthMode,  // Whether to save to database
                    sessionMessages: config.stealthMode ? sessionMessages : undefined  // Session history
                })
            });

            // Check if request was successful
            if (!response.ok) throw new Error('API request failed');

            // Parse response JSON
            const data = await response.json();

            // Add bot response to chat UI
            addMessage(data.response, false);

            // If in stealth mode, add assistant response to session storage
            if (config.stealthMode) {
                sessionMessages.push({
                    role: 'assistant',                 // Mark as assistant message
                    content: data.response,            // Bot's response text
                    timestamp: new Date().toISOString()  // ISO timestamp
                });
                // Persist to sessionStorage
                sessionStorage.setItem(sessionKey, JSON.stringify(sessionMessages));
            }

            // In conversation mode: Speak the response, then restart listening
            // This creates the continuous conversation loop
            if (conversationModeEnabled) {
                chatInput.placeholder = t.speakingResponse;
                // Speak response with callback to restart listening after speech
                speakTextConversation(data.response, () => {
                    // Callback fires when TTS finishes speaking
                    console.log('Response finished speaking, checking if still in conversation mode...');
                    // Verify still in conversation mode before restarting
                    if (conversationModeEnabled) {
                        console.log('Still in conversation mode, restarting recording...');
                        startConversationRecording();  // Restart listening for next user input
                    } else {
                        console.log('No longer in conversation mode, not restarting');
                    }
                });
            }
        } catch (error) {
            // Handle errors in sending message or getting response
            console.error('Chat error:', error);
            addMessage(t.errorProcessing, false);  // Show error to user

            // Restart listening even after error (keep conversation going)
            if (conversationModeEnabled) {
                setTimeout(() => {
                    // Check if still in conversation mode before restarting
                    if (conversationModeEnabled) {
                        startConversationRecording();
                    }
                }, 2000);  // 2 second delay before restarting
            }
        }
    }

    // Stop conversation mode - Cleanup and restore normal chat mode
    // Called when user toggles conversation mode off or on error
    function stopConversationMode() {
        // Disable conversation mode flag
        conversationModeEnabled = false;

        // Stop active recording if running
        if (conversationRecorder && conversationRecorder.state === 'recording') {
            conversationRecorder.stop();  // Stop recording
        }
        // Stop all media stream tracks (releases microphone)
        if (conversationRecorder && conversationRecorder.stream) {
            conversationRecorder.stream.getTracks().forEach(track => track.stop());
        }
        conversationRecorder = null;  // Clear recorder reference

        // Reset speech detection state
        hasDetectedSpeech = false;       // Clear speech detected flag
        consecutiveSilentFrames = 0;     // Reset silence counter

        // Cleanup Web Audio API resources
        if (audioContext) {
            audioContext.close();  // Close audio context (releases resources)
            audioContext = null;
        }
        analyser = null;  // Clear analyser reference

        // Stop any currently playing TTS audio
        if (currentAudio) {
            currentAudio.pause();  // Stop playback
            currentAudio = null;   // Clear reference
        }

        // Restore UI to normal chat mode
        chatInput.placeholder = t.typeMessage;  // Reset placeholder text
        chatInput.disabled = false;             // Re-enable text input
        chatSendBtn.disabled = false;           // Re-enable send button
        if (chatMicBtn) chatMicBtn.disabled = false;  // Re-enable mic button

        // Update conversation button icon to show inactive state
        updateConversationIcon();
    }

    // Add message to chat UI - Creates and displays a message bubble
    // Parameters:
    //   message: Text content to display
    //   isUser: true for user messages (right-aligned, blue), false for bot (left-aligned, gray)
    //   isInitialLoad: true when loading history (skips auto-scroll for performance)
    function addMessage(message, isUser = false, isInitialLoad = false) {
        // Create message container div
        const messageDiv = document.createElement('div');
        // Apply classes for styling: alignment, padding, rounded corners, background color
        messageDiv.className = `chat-message ${isUser ? 'align-self-end' : 'align-self-start'} 
                              p-2 rounded ${isUser ? 'bg-primary text-white' : 'bg-light'}`;
        // Limit message width to 80% of container
        messageDiv.style.maxWidth = '80%';
        // Set message text content
        messageDiv.textContent = message;
        // Append to messages container
        chatMessages.appendChild(messageDiv);

        // Handle scrolling behavior
        if (isInitialLoad) {
            // On initial load, just append without scrolling
            // We'll scroll to bottom once after all messages are loaded
            return;
        }

        if (isUser) {
            // For user messages, scroll to show the full message (bottom-aligned)
            setTimeout(() => {
                messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, 50);  // Short delay to ensure DOM has rendered
        } else {
            // For assistant responses, scroll to show the start of the message (top-aligned)
            setTimeout(() => {
                messageDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100); // Slightly longer delay to ensure proper scrolling
        }
    }

    // Voice recording functions - For one-time voice input (mic button, not conversation mode)
    // Start recording audio from microphone
    async function startRecording() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Determine best supported audio format (browser compatibility)
            const mimeType = MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' :
                MediaRecorder.isTypeSupported('audio/mpeg') ? 'audio/mpeg' :
                    'audio/webm';

            // Create MediaRecorder with audio stream
            mediaRecorder = new MediaRecorder(stream, { mimeType });
            // Clear previous audio chunks
            audioChunks = [];

            // Event handler: Accumulate audio data chunks
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            // Event handler: Process recording when stopped
            mediaRecorder.onstop = processRecording;

            // Start recording
            mediaRecorder.start();
            isRecording = true;  // Set recording flag

            // Update UI - show recording state with visual feedback
            if (chatMicBtn) {
                // Add 3D pressed effect to mic button
                chatMicBtn.style.boxShadow = 'inset 2px 2px 5px rgba(0,0,0,0.2)';
                chatMicBtn.style.transform = 'scale(0.95)';
            }
            chatInput.placeholder = t.recording;  // Update placeholder text
            chatInput.disabled = true;            // Disable text input while recording
            chatSendBtn.disabled = true;          // Disable send button while recording
        } catch (error) {
            // Handle errors (typically microphone permission denied)
            console.error('Error starting recording:', error);
            addMessage(t.microphoneError + error.message, false);
        }
    }

    // Stop recording audio - Called when user clicks mic button again
    function stopRecording() {
        // Verify recorder exists and is recording
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();  // Stop recording (triggers onstop event)
            // Stop all media stream tracks (releases microphone)
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;  // Clear recording flag

            // Update UI - remove pressed effect and show processing state
            if (chatMicBtn) {
                chatMicBtn.style.boxShadow = '';      // Remove pressed shadow
                chatMicBtn.style.transform = '';       // Reset scale
            }
            chatInput.placeholder = t.processing;  // Update placeholder text
        }
    }

    // Process recorded audio - Transcribe and send as message
    // Called automatically when recording stops (mediaRecorder.onstop event)
    async function processRecording() {
        // Get the MIME type that was used for recording
        const mimeType = mediaRecorder.mimeType || 'audio/webm';
        // Determine file extension based on MIME type
        const extension = mimeType.includes('mp4') ? 'mp4' :
            mimeType.includes('mpeg') ? 'mp3' : 'webm';

        // Create a Blob from all recorded audio chunks
        const audioBlob = new Blob(audioChunks, { type: mimeType });
        // Create FormData to send file to server
        const formData = new FormData();
        formData.append('audio', audioBlob, `audio.${extension}`);

        try {
            // Update UI to show transcription in progress
            chatInput.placeholder = t.transcribing;

            // Construct base URL for transcription API endpoint
            const baseUrl = config.apiUrl.replace('/chat', '');
            // Send audio to transcription endpoint
            const response = await fetch(`${baseUrl}/api/transcribe`, {
                method: 'POST',
                body: formData  // FormData contains the audio file
            });

            // Parse response JSON
            const data = await response.json();

            // Check if transcription was successful
            if (data.success) {
                // Restore input controls to normal state
                chatInput.placeholder = t.typeMessage;
                chatInput.disabled = false;
                chatSendBtn.disabled = false;
                if (chatMicBtn) chatMicBtn.disabled = false;

                // Send the transcribed text as a chat message
                await sendMessage(data.transcript);
            } else {
                // Transcription failed - show error and restore controls
                addMessage(t.transcriptionFailed + data.error, false);
                chatInput.placeholder = t.typeMessage;
                chatInput.disabled = false;
                chatSendBtn.disabled = false;
                if (chatMicBtn) chatMicBtn.disabled = false;
            }
        } catch (error) {
            // Handle transcription errors
            console.error('Error transcribing audio:', error);
            addMessage(t.transcriptionError + error.message, false);
            // Restore controls to normal state
            chatInput.placeholder = t.typeMessage;
            chatInput.disabled = false;
            chatSendBtn.disabled = false;
            if (chatMicBtn) chatMicBtn.disabled = false;
        }
    }

    // Setup mic button click handler - Toggle recording on/off
    if (chatMicBtn) {
        chatMicBtn.addEventListener('click', () => {
            if (isRecording) {
                stopRecording();  // Stop if currently recording
            } else {
                startRecording(); // Start if not recording
            }
        });
    }

    // Function to send a message - Main message sending logic
    // Used by both form submit (typed messages) and voice input (transcribed messages)
    async function sendMessage(message) {
        // Exit if message is empty
        if (!message || !message.trim()) return;

        // Trim whitespace
        message = message.trim();

        // Add user message to chat UI
        addMessage(message, true);

        // Clear input field and update UI to show loading state
        chatInput.value = '';
        chatInput.placeholder = t.gettingResponse;  // "Getting response..."
        chatInput.disabled = true;                  // Disable during processing
        chatSendBtn.disabled = true;                // Disable send button
        if (chatMicBtn) chatMicBtn.disabled = true; // Disable mic button

        try {
            // If in stealth mode, add message to session storage
            if (config.stealthMode) {
                sessionMessages.push({
                    role: 'user',                      // Mark as user message
                    content: message,                  // Message text
                    timestamp: new Date().toISOString()  // ISO timestamp
                });
                // Persist to sessionStorage
                sessionStorage.setItem(sessionKey, JSON.stringify(sessionMessages));
            }

            // Send message to chat API
            const response = await fetch(config.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${config.apiKey}`  // API key for authentication
                },
                body: JSON.stringify({
                    message,                           // User's message
                    userKey: config.userKey,          // User identifier
                    stealthMode: config.stealthMode,  // Whether to save to database
                    sessionMessages: config.stealthMode ? sessionMessages : undefined  // Session history for stealth mode
                })
            });

            // Check if request was successful
            if (!response.ok) throw new Error('API request failed');

            // Parse response JSON
            const data = await response.json();

            // Add bot response to chat UI
            addMessage(data.response, false);

            // Speak the response if auto-speak is enabled
            if (autoSpeakEnabled) {
                chatInput.placeholder = t.speakingResponse;  // "Speaking response..."
                await speakText(data.response);
            }

            // If in stealth mode, add assistant response to session storage
            if (config.stealthMode) {
                sessionMessages.push({
                    role: 'assistant',                 // Mark as assistant message
                    content: data.response,            // Bot's response text
                    timestamp: new Date().toISOString()  // ISO timestamp
                });
                // Persist to sessionStorage
                sessionStorage.setItem(sessionKey, JSON.stringify(sessionMessages));
            }
        } catch (error) {
            // Handle errors
            console.error('Chat error:', error);
            addMessage(t.errorProcessing);  // Show error message to user
        } finally {
            // Restore UI to normal state (always runs, even after errors)
            chatInput.placeholder = t.typeMessage;  // Reset placeholder
            chatInput.disabled = false;             // Re-enable input
            chatSendBtn.disabled = false;           // Re-enable send button
            if (chatMicBtn) chatMicBtn.disabled = false;  // Re-enable mic button
            chatInput.focus();                      // Focus input for next message
        }
    }

    // EVENT HANDLERS

    // Handle form submission - When user presses Enter or clicks Send button
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();  // Prevent page reload

        // Get message text and trim whitespace
        const message = chatInput.value.trim();
        if (!message) return;  // Exit if empty

        // Clear input field immediately for better UX
        chatInput.value = '';

        // Send the message
        await sendMessage(message);
    });

    // Handle maximize/restore button - Toggle between normal and fullscreen
    chatMaximize.addEventListener('click', () => {
        // Toggle maximized state
        isMaximized = !isMaximized;
        chatWidget.classList.toggle('chat-maximized');  // Apply/remove fullscreen CSS

        // Update button icon based on state
        chatMaximize.innerHTML = isMaximized
            ? '<i class="bi bi-arrows-angle-contract"></i>'  // Show contract icon when maximized
            : '<i class="bi bi-arrows-angle-expand"></i>';   // Show expand icon when normal

        // Scroll to bottom of messages after layout change
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    // Handle expand button - Restore widget from minimized state
    chatExpand.addEventListener('click', () => {
        minimizedWidget.classList.add('d-none');     // Hide minimized button
        chatWidget.classList.remove('d-none');       // Show full widget
    });

    // Initialize Bootstrap modals - Setup modal dialogs for confirmations
    let stealthModeModal;      // Reference to stealth mode confirmation modal
    let clearChatModal;        // Reference to clear chat confirmation modal
    let pendingStealthMode = false;  // Flag for pending stealth mode change (currently unused)

    // Wait for Bootstrap JS to load before initializing modals
    // Bootstrap is loaded asynchronously, so we need to poll for it
    const initModals = () => {
        if (window.bootstrap) {
            // Bootstrap loaded - initialize modal instances
            stealthModeModal = new bootstrap.Modal(document.getElementById('stealthModeModal'));
            clearChatModal = new bootstrap.Modal(document.getElementById('clearChatModal'));
        } else {
            // Bootstrap not loaded yet - try again in 100ms
            setTimeout(initModals, 100);
        }
    };
    initModals();  // Start the initialization process

    // Handle speaker toggle - Enable/disable auto-speak (TTS) for bot responses
    if (chatSpeaker) {
        chatSpeaker.addEventListener('click', () => {
            // Toggle auto-speak state
            autoSpeakEnabled = !autoSpeakEnabled;

            // Update button icon to reflect new state
            updateSpeakerIcon();

            // Stop any currently playing audio if disabling auto-speak
            if (!autoSpeakEnabled && currentAudio) {
                currentAudio.pause();  // Stop playback
                currentAudio = null;   // Clear reference
            }

            // Provide user feedback via placeholder text
            if (autoSpeakEnabled) {
                chatInput.placeholder = t.autoSpeakEnabled;  // "Auto-speak enabled"
                // Reset placeholder after 2 seconds
                setTimeout(() => {
                    if (!isRecording && !conversationModeEnabled) {
                        chatInput.placeholder = t.typeMessage;
                    }
                }, 2000);
            } else {
                chatInput.placeholder = t.autoSpeakDisabled;  // "Auto-speak disabled"
                // Reset placeholder after 2 seconds
                setTimeout(() => {
                    if (!isRecording && !conversationModeEnabled) {
                        chatInput.placeholder = t.typeMessage;
                    }
                }, 2000);
            }
        });
    }

    // Handle conversation mode toggle - Enable/disable hands-free conversation
    if (chatConversation) {
        chatConversation.addEventListener('click', async () => {
            if (conversationModeEnabled) {
                // Conversation mode is ON - disable it
                stopConversationMode();  // Stop recording, cleanup resources

                // Provide user feedback
                chatInput.placeholder = t.conversationDisabled;  // "Conversation mode disabled"
                // Reset placeholder after 2 seconds
                setTimeout(() => {
                    if (!isRecording && !autoSpeakEnabled) {
                        chatInput.placeholder = t.typeMessage;
                    }
                }, 2000);
            } else {
                // Conversation mode is OFF - enable it
                conversationModeEnabled = true;        // Set flag
                updateConversationIcon();              // Update button appearance
                chatInput.placeholder = t.conversationEnabled;  // "Conversation mode enabled"

                // Disable manual mic button (conversation mode handles recording automatically)
                if (chatMicBtn) chatMicBtn.disabled = true;

                // Start continuous listening
                await startConversationRecording();
            }
        });
    }

    // Handle stealth mode toggle - Enable/disable database storage
    chatStealth.addEventListener('click', () => {
        // Toggle stealth mode state
        config.stealthMode = !config.stealthMode;

        // If enabling stealth mode, clear existing session storage to start fresh
        if (config.stealthMode) {
            sessionStorage.removeItem(sessionKey);  // Clear old data
            sessionMessages = [];                    // Reset in-memory array
        }

        // Update button icon and styling
        updateStealthIcon();

        // Clear the chat UI to reflect the mode change
        chatMessages.innerHTML = '';

        // Add welcome message to cleared chat
        addMessage(t.welcomeMessage, false);

        // Provide user feedback via placeholder text
        if (config.stealthMode) {
            chatInput.placeholder = t.stealthEnabled;  // "Stealth mode enabled"
            // Reset placeholder after 3 seconds
            setTimeout(() => {
                if (!isRecording && !conversationModeEnabled) {
                    chatInput.placeholder = t.typeMessage;
                }
            }, 3000);
        } else {
            chatInput.placeholder = t.stealthDisabled;  // "Stealth mode disabled"
            // Reset placeholder after 3 seconds
            setTimeout(() => {
                if (!isRecording && !conversationModeEnabled) {
                    chatInput.placeholder = t.typeMessage;
                }
            }, 3000);
        }
    });

    // Handle clear chat button - Show confirmation modal
    chatClear.addEventListener('click', () => {
        clearChatModal.show();  // Display Bootstrap modal for confirmation
    });

    // Handle features menu dropdown - Toggle three-dots menu visibility
    featuresMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();  // Prevent event from bubbling to document click handler

        // Toggle menu open/close state
        featuresMenuOpen = !featuresMenuOpen;
        featuresDropdown.style.display = featuresMenuOpen ? 'block' : 'none';

        // Add hover effects to buttons inside dropdown (only when opening)
        if (featuresMenuOpen) {
            // Get all buttons except the menu button itself
            const dropdownButtons = featuresDropdown.querySelectorAll('button:not(#features-menu-btn)');
            dropdownButtons.forEach(btn => {
                // Add hover effect - change background on mouse enter
                btn.addEventListener('mouseenter', function () {
                    this.style.background = '#f8f9fa';
                });
                // Remove hover effect - restore background on mouse leave
                btn.addEventListener('mouseleave', function () {
                    this.style.background = 'transparent';
                });
            });
        }
    });

    // Close features menu when clicking outside of it
    document.addEventListener('click', (e) => {
        // Check if menu is open and click was outside the menu container
        if (featuresMenuOpen && !featuresMenuContainer.contains(e.target)) {
            featuresMenuOpen = false;                   // Update state
            featuresDropdown.style.display = 'none';    // Hide dropdown
        }
    });

    // Close features menu when clicking a feature button inside it
    featuresDropdown.addEventListener('click', (e) => {
        // Find if a button was clicked (excluding the menu button itself)
        if (e.target.closest('button') && e.target.closest('button').id !== 'features-menu-btn') {
            featuresMenuOpen = false;                   // Update state
            featuresDropdown.style.display = 'none';    // Hide dropdown
        }
    });

    // Handle clear chat confirmation - Execute when user confirms deletion
    document.getElementById('confirmClearChat').addEventListener('click', async () => {
        try {
            if (config.stealthMode) {
                // In stealth mode: Only clear browser's session storage
                sessionStorage.removeItem(sessionKey);  // Remove from sessionStorage
                sessionMessages = [];                    // Clear in-memory array
            } else {
                // In normal mode: Call backend to delete from database
                const response = await fetch(`${config.apiUrl.replace('/chat', '/chat/clear')}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${config.apiKey}`  // Authentication
                    },
                    body: JSON.stringify({
                        userKey: config.userKey  // Identify which user's history to clear
                    })
                });

                // Check if deletion was successful
                if (!response.ok) {
                    throw new Error('Failed to clear chat history');
                }
            }

            // Clear the chat UI (remove all messages from display)
            chatMessages.innerHTML = '';

            // Provide user feedback via placeholder text
            chatInput.placeholder = t.chatCleared;  // "Chat history cleared"
            // Reset placeholder after 3 seconds
            setTimeout(() => {
                if (!isRecording && !conversationModeEnabled) {
                    chatInput.placeholder = t.typeMessage;
                }
            }, 3000);

            // Hide the confirmation modal
            clearChatModal.hide();
        } catch (error) {
            // Handle errors during deletion
            console.error('Error clearing chat:', error);

            // Show error message to user
            chatInput.placeholder = t.chatClearFailed;  // "Failed to clear chat"
            // Reset placeholder after 3 seconds
            setTimeout(() => {
                if (!isRecording && !conversationModeEnabled) {
                    chatInput.placeholder = t.typeMessage;
                }
            }, 3000);

            // Hide the modal even if there's an error
            clearChatModal.hide();
        }
    });

    // Handle close button - Minimize widget to floating icon
    chatClose.addEventListener('click', () => {
        // Stop conversation mode if currently active (cleanup resources)
        if (conversationModeEnabled) {
            stopConversationMode();
        }

        // If widget is maximized, restore to normal size first
        if (isMaximized) {
            chatMaximize.click();  // Trigger maximize button to restore size
        }

        // Minimize widget to floating icon
        chatWidget.classList.add('d-none');           // Hide full widget
        minimizedWidget.classList.remove('d-none');   // Show minimized icon
    });

    // End of IIFE - Closes the immediately invoked function expression
})();