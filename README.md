# Aswin's Chatbot

This is a custom chatbot application built in Python using the Kivy framework. It provides a clean, responsive user interface to connect with and chat with powerful AI language models through the OpenRouter API.

The app features a personalized title bar, a scrollable chat history, and a modern input area at the bottom.

## Key Features

* **Live AI Connection:** Connects directly to the OpenRouter API to chat with state-of-the-art models like Llama 3.
* **Rich Text Rendering:** The chat display fully supports Markdown, correctly formatting:
    * **Bold** and *italic* text
    * Headings
    * Bulleted and numbered lists
    * Colored code blocks
* **Clickable Links:** Any URLs shared by the bot are automatically converted into clickable links that open in your default browser.
* **Responsive UI:**
    * A clean, scrollable view for chat history.
    * A bottom-anchored input bar with a round send button.
    * Auto-scrolling to the latest message as it arrives.
* **User-Friendly:**
    * Send messages by clicking the button or simply pressing the "Enter" key.
    * The app's UI remains perfectly smooth during API calls by using multithreading.
* **Robust Error Handling:** Clearly displays any network or API errors without crashing the application.