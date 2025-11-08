import requests
import threading
import mistune                       # Markdown parser
import webbrowser                    # To open links
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import escape_markup # To safely display text

# 🔑 Your OpenRouter API key here
API_KEY = "api-key-here"
URL = "https://openrouter.ai/api/v1/chat/completions"

# 📝 Choose your model here
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

# --- Kivy Language String (with on_ref_press) ---
KV_STRING = """
<ChatInterface>:
    orientation: 'vertical'
    
    # --- NEW: Top Title Bar ---
    BoxLayout:
        size_hint: (1, None)
        height: '48dp'
        # Dark background for the bar
        canvas.before:
            Color:
                rgba: (0.15, 0.15, 0.15, 1) # A dark bar color
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "Aswin's Chatbot"
            font_size: '18sp'
            bold: True
            halign: 'center'
            valign: 'middle'
            
    # --- 1. The Scrollable Chat Area ---
    ScrollView:
        id: scroll_view
        size_hint: (1, 1)
        
        Label:
            id: chat_label
            text: "Chat will appear here"
            halign: "left"
            valign: "top"
            size_hint: (1, None)
            height: self.texture_size[1]
            text_size: (self.width, None)
            markup: True
            padding: (10, 10)
            # Make links clickable
            on_ref_press: app.on_ref_press(*args)

    BoxLayout:
        size_hint: (1, None)
        height: '50dp'
        padding: ('10dp', '5dp', '10dp', '5dp')
        spacing: '10dp'

        TextInput:
            id: text_input
            hint_text: "Type your message"
            multiline: False
            size_hint: (1, 1)
            on_text_validate: app.send_message()

        Button:
            id: send_button
            text: ">"
            font_size: '24sp'
            size_hint: (None, 1)
            width: self.height
            background_color: (0, 0, 0, 0)
            background_normal: ''
            background_down: ''
            canvas.before:
                Color:
                    rgba: (0.3, 0.5, 0.8, 1) if self.state == 'normal' else (0.2, 0.4, 0.7, 1)
                RoundedRectangle:
                    size: self.size
                    pos: self.pos
                    radius: [min(self.width, self.height) / 2]
"""

Builder.load_string(KV_STRING)

# --- Custom Markdown Renderer (Mistune v3 compatible) ---
class KivyMarkdownRenderer(mistune.HTMLRenderer):
    def text(self, text):
        return escape_markup(text)

    def strong(self, text):
        return f"[b]{text}[/b]"

    def emphasis(self, text):
        return f"[i]{text}[/i]"

    def link(self, text, url, title=None):
        return f"[ref={url}][color=88aaff]{text}[/color][/ref]"

    def codespan(self, text):
        return f"[color=c0c0c0]{escape_markup(text)}[/color]"

    def block_code(self, code, info=None):
        return f"\n[color=c0c0c0]{escape_markup(code.strip())}[/color]\n"

    def paragraph(self, text):
        return f"{text}\n"

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # --- THIS IS THE FIX ---
    # Updated all signatures to be compatible with mistune v3
    # by adding **attrs to catch extra arguments like 'depth'.
    
    def heading(self, text, level, **attrs):
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        sizes = {1: '24sp', 2: '20sp', 3: '18sp'}
        size = sizes.get(level, '16sp')
        return f"\n[size={size}][b]{text}[/b][/size]\n"

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def list(self, text, ordered, **attrs):
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        return f"\n{text}\n"

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def list_item(self, text, **attrs):
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        return f"  • {text}\n"

# Create a markdown parser instance
markdown_parser = mistune.create_markdown(renderer=KivyMarkdownRenderer())

class ChatInterface(BoxLayout):
    pass

class GPTApp(App):
    def build(self):
        self.layout = ChatInterface()
        self.input = self.layout.ids.text_input
        self.button = self.layout.ids.send_button
        self.label = self.layout.ids.chat_label
        self.scroll_view = self.layout.ids.scroll_view

        self.button.bind(on_press=self.send_message)
        self.label.bind(height=self.scroll_to_bottom)
        
        Window.softinput_mode = 'below_target'
        self._keyboard = Window.request_keyboard(
            self.on_keyboard_close, self.input
        )
        if self._keyboard:
            self._keyboard.bind(on_key_down=self.on_key_down)

        return self.layout
    
    def on_ref_press(self, instance, ref):
        print(f"Opening link: {ref}")
        try:
            webbrowser.open(ref)
        except Exception as e:
            print(f"Error opening link: {e}")
            self.update_label(f"[color=ff3333]Error opening link: {e}[/color]")
    
    # Renamed from _on_keyboard_close to avoid potential conflicts
    def on_keyboard_close(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self.on_key_down)
            self._keyboard = None

    # Renamed from _on_key_down
    def on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'enter' and not self.input.multiline:
            self.send_message()
            return True
        return False

    def scroll_to_bottom(self, *args):
        Clock.schedule_once(lambda dt: setattr(self.scroll_view, 'scroll_y', 0), 0.1)

    def send_message(self, instance=None):
        user_text = self.input.text.strip()
        if not user_text:
            return

        safe_user_text = escape_markup(user_text)
        self.label.text += f"\n\n[b]You:[/b] {safe_user_text}"
        self.input.text = ""
        
        threading.Thread(target=self.call_api, args=(user_text,), daemon=True).start()

    def call_api(self, user_text):
        try:
            payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are an overexcited greedy guy. You format your answers in Markdown."},
                    {"role": "user", "content": user_text},
                ],
            }
            resp = requests.post(
                URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            
            resp.raise_for_status() 
            data = resp.json()
            
            if "choices" in data:
                reply = data["choices"][0]["message"]["content"]
                
                kivy_reply = markdown_parser(reply.strip())
                text_to_add = f"\n[b]Bot:[/b] {kivy_reply}"
                
                Clock.schedule_once(lambda dt: self.update_label(text_to_add))
            else:
                text_to_add = f"\n[color=ff3333][Error: Invalid response from server: {str(data)}][/color]"
                Clock.schedule_once(lambda dt: self.update_label(text_to_add))

        except requests.exceptions.HTTPError as http_err:
            try:
                error_details = http_err.response.json()
                message = error_details.get('error', {}).get('message', str(error_details))
            except:
                message = str(http_err)
            text_to_add = f"\n[color=ff3333][b]Server Error:[/b] {message}[/color]"
            Clock.schedule_once(lambda dt: self.update_label(text_to_add))
            
        except Exception as e:
            text_to_add = f"\n[color=ff3333][b]General Error:[/b] {e}[/color]"
            Clock.schedule_once(lambda dt: self.update_label(text_to_add))

    def update_label(self, text):
        self.label.text += text


if __name__ == "__main__":
    GPTApp().run()
