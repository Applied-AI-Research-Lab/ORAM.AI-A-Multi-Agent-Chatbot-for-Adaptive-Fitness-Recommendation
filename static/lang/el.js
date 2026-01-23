// Greek translations
const el = {
    // Header
    headerTitle: 'ORAM.AI Chatbot',
    
    // Buttons
    clearHistory: 'Εκκαθάριση ιστορικού',
    minimize: 'Ελαχιστοποίηση',
    maximize: 'Μεγιστοποίηση',
    close: 'Κλείσιμο',
    
    // Features Menu
    conversation: 'Συνομιλία',
    voiceInput: 'Φωνητική Εισαγωγή',
    autoSpeak: 'Αυτόματη Ομιλία',
    stealthMode: 'Λειτουργία Stealth',
    
    // Input
    inputPlaceholder: 'Πληκτρολόγησε το μήνυμά σου...',
    
    // Status Messages
    recording: 'Ηχογράφηση...',
    processing: 'Επεξεργασία...',
    transcribing: 'Μεταγραφή...',
    gettingResponse: 'Λήψη απάντησης...',
    speakingResponse: 'Ομιλία απάντησης...',
    
    // Feature Status
    autoSpeakEnabled: 'Αυτόματη ομιλία ενεργοποιήθηκε',
    autoSpeakDisabled: 'Αυτόματη ομιλία απενεργοποιήθηκε',
    conversationEnabled: 'Λειτουργία συνομιλίας ενεργοποιήθηκε. Μίλα τώρα!',
    conversationDisabled: 'Λειτουργία συνομιλίας απενεργοποιήθηκε',
    stealthEnabled: 'Λειτουργία Stealth ενεργοποιήθηκε',
    stealthDisabled: 'Λειτουργία Stealth απενεργοποιήθηκε',
    
    // Chat Messages
    welcomeMessage: 'Είμαι ο προσωπικός σου γυμναστής. Πως μπορώ να σε βοηθήσω σήμερα;',
    chatCleared: 'Το ιστορικό συνομιλίας διαγράφηκε',
    chatClearFailed: 'Αποτυχία διαγραφής ιστορικού. Παρακαλώ δοκίμασε ξανά.',
    loadHistoryFailed: 'Αποτυχία φόρτωσης ιστορικού συνομιλίας',
    errorProcessing: 'Συγγνώμη, υπήρξε σφάλμα κατά την επεξεργασία του μηνύματός σου.',
    microphoneError: '❌ Σφάλμα πρόσβασης στο μικρόφωνο: ',
    transcriptionFailed: '❌ Η μεταγραφή απέτυχε: ',
    transcriptionError: '❌ Σφάλμα μεταγραφής ήχου: ',
    
    // Modal - Clear Chat
    clearChatTitle: 'Εκκαθάριση Ιστορικού Συνομιλίας',
    clearChatMessage: 'Είσαι σίγουρος ότι θέλεις να διαγράψεις όλο το ιστορικό συνομιλίας;',
    clearChatConfirm: 'Διαγραφή',
    clearChatCancel: 'Ακύρωση',
    
    // Tooltips
    stealthOnTitle: 'Λειτουργία Stealth ΕΝΕΡΓΗ (τα μηνύματα δεν αποθηκεύονται)',
    stealthOffTitle: 'Λειτουργία Stealth ΑΝΕΝΕΡΓΗ',
    autoSpeakOnTitle: 'Αυτόματη ομιλία απαντήσεων ΕΝΕΡΓΗ',
    autoSpeakOffTitle: 'Αυτόματη ομιλία απαντήσεων ΑΝΕΝΕΡΓΗ',
    conversationOnTitle: 'Λειτουργία συνομιλίας ΕΝΕΡΓΗ (μίλα ελεύθερα)',
    conversationOffTitle: 'Λειτουργία συνομιλίας ΑΝΕΝΕΡΓΗ',
    
    // Conversation mode specific
    listening: 'Ακούγοντας... Μίλα τώρα',
    listeningMic: 'Ακούγοντας... 🎤',
    sendingMessage: 'Αποστολή μηνύματος...',
    noSpeechDetected: 'Δεν ανιχνεύθηκε ομιλία. Ακούγοντας ξανά...',
    errorListeningAgain: 'Σφάλμα. Ακούγοντας ξανά...',
    typeMessage: 'Πληκτρολόγησε το μήνυμά σου...'
};

// Make available globally for chat-widget.js
window.el = el;
