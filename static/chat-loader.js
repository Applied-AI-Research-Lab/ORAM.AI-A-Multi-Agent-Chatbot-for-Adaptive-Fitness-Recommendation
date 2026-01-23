// Chat Widget Loader Script
// Purpose: Lightweight bootstrap that captures configuration, validates domain,
// and dynamically loads the main chat widget with appropriate language file.
// This two-step approach allows server-side security validation before code delivery.

// IIFE (Immediately Invoked Function Expression) to create isolated scope
(function () {
    // Capture reference to this loader script element
    // IMPORTANT: Must be done immediately as document.currentScript becomes null after execution
    const currentScript = document.currentScript;

    // Extract configuration from HTML data attributes
    // All configuration is passed via data-* attributes on the loader script tag
    // Example: <script src="chat-loader.js" data-api-key="abc123" data-user-key="user1"></script>

    // Extract API key for backend authentication (REQUIRED)
    const apiKey = currentScript.getAttribute('data-api-key');

    // Extract unique user identifier for session management (REQUIRED)
    const userKey = currentScript.getAttribute('data-user-key');

    // Extract theme preference: 'light' or 'dark' (OPTIONAL) NOT WORKING YET
    const theme = currentScript.getAttribute('data-theme');

    // Extract stealth mode setting: 'on' means no database storage (OPTIONAL)
    const stealthMode = currentScript.getAttribute('data-stealth-mode');

    // Extract conversation mode setting: 'off' disables hands-free mode (OPTIONAL)
    const chatConversation = currentScript.getAttribute('data-chat-conversation');

    // Extract auto-speak setting: 'off' disables TTS for responses (OPTIONAL)
    const chatSpeaker = currentScript.getAttribute('data-chat-speaker');

    // Extract mic button setting: 'off' disables voice input (OPTIONAL)
    const chatMicBtn = currentScript.getAttribute('data-chat-mic-btn');

    // Extract fullscreen setting: 'on' starts widget in fullscreen mode (OPTIONAL)
    const fullscreen = currentScript.getAttribute('data-fullscreen');

    // Extract UI language code: 'en', 'el', etc. Defaults to 'en' if not specified (OPTIONAL)
    const uiLang = currentScript.getAttribute('data-chat-ui-lang') || 'en';

    // Capture the current domain for security validation
    // This will be sent to the server for validation against allowed domains
    // Example: 'example.com', 'localhost', 'subdomain.example.com'
    const currentDomain = window.location.hostname;

    // Extract the base URL from this loader script's source path
    // This ensures the chat widget is loaded from the same location as the loader
    const scriptSrc = currentScript.src;
    // Remove the filename (chat-loader.js) to get the directory path
    // Example: 'https://example.com/static/chat-loader.js' -> 'https://example.com/static'
    const baseUrl = scriptSrc.substring(0, scriptSrc.lastIndexOf('/'));

    // Create a new <script> element that will load the actual chat widget
    const widgetScript = document.createElement('script');

    // Set the script source URL with query parameters for server-side processing
    // Query parameters allow the server to:
    //   - lang: Determine which language file to include (en.js, el.js, etc.)
    //   - domain: Validate that this domain is authorized to use the widget
    //   - apikey: Validate the API key before serving the widget code
    // encodeURIComponent ensures special characters in domain/apikey are properly encoded
    widgetScript.src = `${baseUrl}/chat.js?lang=${uiLang}&domain=${encodeURIComponent(currentDomain)}&apikey=${encodeURIComponent(apiKey)}`;

    // Copy all configuration from loader to widget script as data attributes
    // The main widget (chat-widget.js) will read these attributes via document.currentScript

    // Set API key attribute (REQUIRED - used for API authentication)
    widgetScript.setAttribute('data-api-key', apiKey);

    // Set user key attribute (REQUIRED - identifies the user/session)
    widgetScript.setAttribute('data-user-key', userKey);

    // Set theme attribute only if provided (OPTIONAL - 'light' or 'dark')
    if (theme) widgetScript.setAttribute('data-theme', theme);

    // Set stealth mode attribute only if provided (OPTIONAL - 'on' disables database storage)
    if (stealthMode) widgetScript.setAttribute('data-stealth-mode', stealthMode);

    // Set conversation mode attribute only if provided (OPTIONAL - 'off' disables hands-free mode)
    if (chatConversation) widgetScript.setAttribute('data-chat-conversation', chatConversation);

    // Set auto-speak attribute only if provided (OPTIONAL - 'off' disables TTS)
    if (chatSpeaker) widgetScript.setAttribute('data-chat-speaker', chatSpeaker);

    // Set microphone button attribute only if provided (OPTIONAL - 'off' disables voice input)
    if (chatMicBtn) widgetScript.setAttribute('data-chat-mic-btn', chatMicBtn);

    // Set fullscreen attribute only if provided (OPTIONAL - 'on' starts in fullscreen)
    if (fullscreen) widgetScript.setAttribute('data-fullscreen', fullscreen);

    // Set UI language attribute (ALWAYS SET - defaults to 'en' if not provided)
    widgetScript.setAttribute('data-chat-ui-lang', uiLang);

    // Insert the newly created script element into the DOM right after this loader script
    // Using insertBefore with nextSibling ensures the widget script loads in the correct position
    // This maintains the execution order: loader runs first, then widget
    currentScript.parentNode.insertBefore(widgetScript, currentScript.nextSibling);

    // Execution flow after this point:
    // 1. Browser requests: /static/chat.js?lang=en&domain=example.com&apikey=abc123
    // 2. Server (app.py) receives request and validates domain and API key
    // 3. If validation passes, server responds with concatenated language + widget files
    // 4. Widget initializes using data attributes set above
    // 5. Chat interface appears on the page

    // End of IIFE
})();
