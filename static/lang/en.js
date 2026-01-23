// English translations
const en = {
    // Header
    headerTitle: 'ORAM.AI Chatbot',
    
    // Buttons
    clearHistory: 'Clear history',
    minimize: 'Minimize',
    maximize: 'Maximize',
    close: 'Close',
    
    // Features Menu
    conversation: 'Conversation',
    voiceInput: 'Voice Input',
    autoSpeak: 'Auto-speak',
    stealthMode: 'Stealth Mode',
    
    // Input
    inputPlaceholder: 'Type your message...',
    
    // Status Messages
    recording: 'Recording...',
    processing: 'Processing...',
    transcribing: 'Transcribing...',
    gettingResponse: 'Getting response...',
    speakingResponse: 'Speaking response...',
    
    // Feature Status
    autoSpeakEnabled: 'Auto-speak enabled',
    autoSpeakDisabled: 'Auto-speak disabled',
    conversationEnabled: 'Conversation mode enabled. Speak now!',
    conversationDisabled: 'Conversation mode disabled',
    stealthEnabled: 'Stealth mode enabled',
    stealthDisabled: 'Stealth mode disabled',
    
    // Chat Messages
    welcomeMessage: 'I am your personal trainer. How can I help you today?',
    chatCleared: 'Chat history has been cleared',
    chatClearFailed: 'Failed to clear chat history. Please try again.',
    loadHistoryFailed: 'Failed to load chat history',
    errorProcessing: 'Sorry, there was an error processing your message.',
    microphoneError: '❌ Error accessing microphone: ',
    transcriptionFailed: '❌ Transcription failed: ',
    transcriptionError: '❌ Error transcribing audio: ',
    
    // Modal - Clear Chat
    clearChatTitle: 'Clear Chat History',
    clearChatMessage: 'Are you sure you want to clear all chat history?',
    clearChatConfirm: 'Clear',
    clearChatCancel: 'Cancel',
    
    // Tooltips
    stealthOnTitle: 'Stealth mode ON (messages are not stored)',
    stealthOffTitle: 'Stealth mode OFF',
    autoSpeakOnTitle: 'Auto-speak responses ON',
    autoSpeakOffTitle: 'Auto-speak responses OFF',
    conversationOnTitle: 'Conversation mode ON (speak freely)',
    conversationOffTitle: 'Conversation mode OFF',
    
    // Conversation mode specific
    listening: 'Listening... Speak now',
    listeningMic: 'Listening... 🎤',
    sendingMessage: 'Sending message...',
    noSpeechDetected: 'No speech detected. Listening again...',
    errorListeningAgain: 'Error. Listening again...',
    typeMessage: 'Type your message...'
};

// Make available globally for chat-widget.js
window.en = en;
