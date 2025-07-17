import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
import json
import os
import sys

# Try to import optional dependencies
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Speech recognition not available. Install with: pip install speechrecognition pyaudio")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Text-to-speech not available. Install with: pip install pyttsx3")

try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("Google Translator not available. Install with: pip install googletrans==4.0.0-rc1")

# Fallback translator using basic dictionary (limited functionality)
class FallbackTranslator:
    def __init__(self):
        self.basic_translations = {
            'en': {
                'hello': {'es': 'hola', 'fr': 'bonjour', 'de': 'hallo', 'it': 'ciao'},
                'goodbye': {'es': 'adiós', 'fr': 'au revoir', 'de': 'auf wiedersehen', 'it': 'arrivederci'},
                'thank you': {'es': 'gracias', 'fr': 'merci', 'de': 'danke', 'it': 'grazie'},
                'please': {'es': 'por favor', 'fr': 's\'il vous plaît', 'de': 'bitte', 'it': 'per favore'},
                'yes': {'es': 'sí', 'fr': 'oui', 'de': 'ja', 'it': 'sì'},
                'no': {'es': 'no', 'fr': 'non', 'de': 'nein', 'it': 'no'},
                'excuse me': {'es': 'disculpe', 'fr': 'excusez-moi', 'de': 'entschuldigung', 'it': 'scusi'},
                'help': {'es': 'ayuda', 'fr': 'aide', 'de': 'hilfe', 'it': 'aiuto'},
                'water': {'es': 'agua', 'fr': 'eau', 'de': 'wasser', 'it': 'acqua'},
                'food': {'es': 'comida', 'fr': 'nourriture', 'de': 'essen', 'it': 'cibo'}
            }
        }
    
    def translate(self, text, src='en', dest='es'):
        text_lower = text.lower().strip()
        if src in self.basic_translations and text_lower in self.basic_translations[src]:
            if dest in self.basic_translations[src][text_lower]:
                class TranslationResult:
                    def __init__(self, text):
                        self.text = text
                return TranslationResult(self.basic_translations[src][text_lower][dest])
        
        # If no translation found, return original text with a note
        class TranslationResult:
            def __init__(self, text):
                self.text = text
        return TranslationResult(f"[Translation not available] {text}")

class LanguageTranslator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Universal Language Translator")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Set instance variables for availability
        self.speech_available = SPEECH_RECOGNITION_AVAILABLE
        self.tts_available = TTS_AVAILABLE
        self.translator_available = TRANSLATOR_AVAILABLE
        
        # Check for missing dependencies and show warnings
        self.check_dependencies()
        
        # Initialize speech recognition and text-to-speech
        if self.speech_available:
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
            except:
                self.microphone = None
                self.speech_available = False
        else:
            self.recognizer = None
            self.microphone = None
            
        if self.tts_available:
            try:
                self.tts_engine = pyttsx3.init()
            except:
                self.tts_engine = None
                self.tts_available = False
        else:
            self.tts_engine = None
            
        if self.translator_available:
            self.translator = Translator()
        else:
            self.translator = FallbackTranslator()
        
        # Language mappings
        self.languages = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Italian': 'it',
            'Portuguese': 'pt',
            'Russian': 'ru',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Chinese (Simplified)': 'zh-cn',
            'Chinese (Traditional)': 'zh-tw',
            'Arabic': 'ar',
            'Hindi': 'hi',
            'Dutch': 'nl',
            'Swedish': 'sv',
            'Norwegian': 'no',
            'Danish': 'da',
            'Finnish': 'fi',
            'Polish': 'pl',
            'Czech': 'cs',
            'Hungarian': 'hu',
            'Turkish': 'tr',
            'Greek': 'el',
            'Hebrew': 'he',
            'Thai': 'th',
            'Vietnamese': 'vi',
            'Indonesian': 'id',
            'Malay': 'ms',
            'Filipino': 'tl',
            'Swahili': 'sw',
            'Bengali': 'bn',
            'Tamil': 'ta',
            'Telugu': 'te',
            'Marathi': 'mr',
            'Gujarati': 'gu',
            'Punjabi': 'pa',
            'Urdu': 'ur',
            'Persian': 'fa',
            'Romanian': 'ro',
            'Bulgarian': 'bg',
            'Croatian': 'hr',
            'Serbian': 'sr',
            'Slovak': 'sk',
            'Slovenian': 'sl',
            'Lithuanian': 'lt',
            'Latvian': 'lv',
            'Estonian': 'et',
            'Ukrainian': 'uk',
            'Catalan': 'ca',
            'Basque': 'eu',
            'Galician': 'gl',
            'Welsh': 'cy',
            'Irish': 'ga',
            'Scottish Gaelic': 'gd',
            'Maltese': 'mt',
            'Icelandic': 'is',
            'Albanian': 'sq',
            'Macedonian': 'mk',
            'Bosnian': 'bs',
            'Montenegrin': 'me',
            'Afrikaans': 'af',
            'Zulu': 'zu',
            'Xhosa': 'xh',
            'Yoruba': 'yo',
            'Hausa': 'ha',
            'Amharic': 'am',
            'Somali': 'so',
            'Malagasy': 'mg',
            'Esperanto': 'eo',
            'Latin': 'la'
        }
        
        # Variables for recording state
        self.is_recording = False
        self.recording_thread = None
        
        # Translation history
        self.translation_history = []
        
        # Setup GUI
        self.setup_gui()
        
        # Configure TTS engine
        if self.tts_available and self.tts_engine:
            self.configure_tts()
        
        # Load saved settings
        self.load_settings()
        
    def check_dependencies(self):
        """Check for missing dependencies and show installation instructions"""
        missing_deps = []
        
        if not self.speech_available:
            missing_deps.append("Speech Recognition (pip install speechrecognition pyaudio)")
        
        if not self.tts_available:
            missing_deps.append("Text-to-Speech (pip install pyttsx3)")
            
        if not self.translator_available:
            missing_deps.append("Google Translator (pip install googletrans==4.0.0-rc1)")
            
        if missing_deps:
            deps_text = "\n".join(f"• {dep}" for dep in missing_deps)
            messagebox.showwarning(
                "Missing Dependencies", 
                f"Some features may not work properly. Please install:\n\n{deps_text}\n\n"
                "The application will continue with limited functionality."
            )
        
    def setup_gui(self):
        # Main title
        title_label = tk.Label(self.root, text="Universal Language Translator", 
                              font=('Arial', 20, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=10)
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Language selection frame
        lang_frame = ttk.LabelFrame(main_frame, text="Language Selection", padding=10)
        lang_frame.pack(fill='x', pady=(0, 10))
        
        # Source language selection
        ttk.Label(lang_frame, text="From:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.source_lang_var = tk.StringVar(value='English')
        self.source_lang_combo = ttk.Combobox(lang_frame, textvariable=self.source_lang_var, 
                                             values=list(self.languages.keys()), state='readonly', width=20)
        self.source_lang_combo.grid(row=0, column=1, padx=(0, 20))
        
        # Target language selection
        ttk.Label(lang_frame, text="To:").grid(row=0, column=2, sticky='w', padx=(0, 5))
        self.target_lang_var = tk.StringVar(value='Spanish')
        self.target_lang_combo = ttk.Combobox(lang_frame, textvariable=self.target_lang_var, 
                                             values=list(self.languages.keys()), state='readonly', width=20)
        self.target_lang_combo.grid(row=0, column=3, padx=(0, 20))
        
        # Swap languages button
        swap_btn = ttk.Button(lang_frame, text="⇄", command=self.swap_languages, width=3)
        swap_btn.grid(row=0, column=4)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding=10)
        input_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Text input area
        self.input_text = scrolledtext.ScrolledText(input_frame, height=6, font=('Arial', 12))
        self.input_text.pack(fill='both', expand=True, pady=(0, 10))
        
        # Control buttons frame
        control_frame = ttk.Frame(input_frame)
        control_frame.pack(fill='x')
        
        # Record button
        self.record_btn = ttk.Button(control_frame, text="🎤 Start Recording", 
                                    command=self.toggle_recording, style='Accent.TButton')
        if not self.speech_available:
            self.record_btn.config(state='disabled', text="🎤 Recording Unavailable")
        self.record_btn.pack(side='left', padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(control_frame, text="Clear", command=self.clear_input)
        clear_btn.pack(side='left', padx=(0, 10))
        
        # Translate button
        translate_btn = ttk.Button(control_frame, text="Translate", command=self.translate_text)
        translate_btn.pack(side='left', padx=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground='green')
        self.status_label.pack(side='right')
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Translation", padding=10)
        output_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Translation output area
        self.output_text = scrolledtext.ScrolledText(output_frame, height=6, font=('Arial', 12), 
                                                    state='disabled')
        self.output_text.pack(fill='both', expand=True, pady=(0, 10))
        
        # Output control buttons
        output_control_frame = ttk.Frame(output_frame)
        output_control_frame.pack(fill='x')
        
        # Speak translation button
        self.speak_btn = ttk.Button(output_control_frame, text="🔊 Speak", command=self.speak_translation)
        if not self.tts_available:
            self.speak_btn.config(state='disabled', text="🔊 Speech Unavailable")
        self.speak_btn.pack(side='left', padx=(0, 10))
        
        # Copy translation button
        copy_btn = ttk.Button(output_control_frame, text="📋 Copy", command=self.copy_translation)
        copy_btn.pack(side='left', padx=(0, 10))
        
        # Save translation button
        save_btn = ttk.Button(output_control_frame, text="💾 Save", command=self.save_translation)
        save_btn.pack(side='left', padx=(0, 10))
        
        # History frame
        history_frame = ttk.LabelFrame(main_frame, text="Translation History", padding=10)
        history_frame.pack(fill='both', expand=True)
        
        # History listbox with scrollbar
        history_list_frame = ttk.Frame(history_frame)
        history_list_frame.pack(fill='both', expand=True)
        
        self.history_listbox = tk.Listbox(history_list_frame, font=('Arial', 10))
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient='vertical', command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_listbox.pack(side='left', fill='both', expand=True)
        history_scrollbar.pack(side='right', fill='y')
        
        # History controls
        history_control_frame = ttk.Frame(history_frame)
        history_control_frame.pack(fill='x', pady=(10, 0))
        
        clear_history_btn = ttk.Button(history_control_frame, text="Clear History", 
                                      command=self.clear_history)
        clear_history_btn.pack(side='left')
        
        # Bind double-click to load from history
        self.history_listbox.bind('<Double-1>', self.load_from_history)
        
    def configure_tts(self):
        """Configure text-to-speech engine settings"""
        if not self.tts_engine:
            return
            
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"TTS configuration error: {e}")
            self.tts_available = False
        
    def swap_languages(self):
        """Swap source and target languages"""
        source = self.source_lang_var.get()
        target = self.target_lang_var.get()
        self.source_lang_var.set(target)
        self.target_lang_var.set(source)
        
    def clear_input(self):
        """Clear the input text area"""
        self.input_text.delete(1.0, tk.END)
        
    def toggle_recording(self):
        """Toggle speech recording"""
        if not self.speech_available:
            messagebox.showerror("Error", "Speech recognition is not available. Please install required packages.")
            return
            
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Start speech recording in a separate thread"""
        if not self.speech_available or not self.microphone:
            messagebox.showerror("Error", "Microphone not available.")
            return
            
        self.is_recording = True
        self.record_btn.config(text="🛑 Stop Recording")
        self.status_var.set("Listening...")
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
        
    def stop_recording(self):
        """Stop speech recording"""
        self.is_recording = False
        self.record_btn.config(text="🎤 Start Recording")
        
    def record_audio(self):
        """Record audio and convert to text"""
        if not self.speech_available:
            return
            
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
            while self.is_recording:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    # Get source language code
                    source_lang = self.languages[self.source_lang_var.get()]
                    
                    # Recognize speech
                    text = self.recognizer.recognize_google(audio, language=source_lang)
                    
                    # Update input text
                    self.root.after(0, self.update_input_text, text)
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    self.root.after(0, self.show_error, f"Speech recognition error: {e}")
                    break
                    
        except Exception as e:
            self.root.after(0, self.show_error, f"Recording error: {e}")
        finally:
            self.root.after(0, self.recording_finished)
            
    def update_input_text(self, text):
        """Update input text area with recognized speech"""
        current_text = self.input_text.get(1.0, tk.END).strip()
        if current_text:
            self.input_text.insert(tk.END, " " + text)
        else:
            self.input_text.insert(1.0, text)
            
    def recording_finished(self):
        """Handle recording completion"""
        self.is_recording = False
        self.record_btn.config(text="🎤 Start Recording")
        self.status_var.set("Ready")
        
    def translate_text(self):
        """Translate the input text"""
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter text to translate or use speech recognition.")
            return
            
        try:
            self.status_var.set("Translating...")
            
            # Get language codes
            source_lang = self.languages[self.source_lang_var.get()]
            target_lang = self.languages[self.target_lang_var.get()]
            
            # Perform translation
            if self.translator_available:
                translation = self.translator.translate(text, src=source_lang, dest=target_lang)
            else:
                # Use fallback translator
                translation = self.translator.translate(text, src=source_lang, dest=target_lang)
            
            # Display translation
            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, translation.text)
            self.output_text.config(state='disabled')
            
            # Add to history
            self.add_to_history(text, translation.text, 
                              self.source_lang_var.get(), self.target_lang_var.get())
            
            if self.translator_available:
                self.status_var.set("Translation complete")
            else:
                self.status_var.set("Translation complete (limited functionality)")
            
        except Exception as e:
            self.show_error(f"Translation error: {e}")
            
    def speak_translation(self):
        """Speak the translated text"""
        if not self.tts_available:
            messagebox.showerror("Error", "Text-to-speech is not available. Please install pyttsx3.")
            return
            
        text = self.output_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No translation to speak.")
            return
            
        try:
            self.status_var.set("Speaking...")
            threading.Thread(target=self.speak_text, args=(text,)).start()
        except Exception as e:
            self.show_error(f"Speech error: {e}")
            
    def speak_text(self, text):
        """Speak text using TTS engine"""
        if not self.tts_available or not self.tts_engine:
            return
            
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            self.root.after(0, lambda: self.status_var.set("Ready"))
        except Exception as e:
            self.root.after(0, self.show_error, f"TTS error: {e}")
            
    def copy_translation(self):
        """Copy translation to clipboard"""
        text = self.output_text.get(1.0, tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("Copied to clipboard")
        else:
            messagebox.showwarning("Warning", "No translation to copy.")
            
    def save_translation(self):
        """Save translation to file"""
        text = self.output_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No translation to save.")
            return
            
        try:
            filename = f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Original ({self.source_lang_var.get()}):\n")
                f.write(self.input_text.get(1.0, tk.END).strip() + "\n\n")
                f.write(f"Translation ({self.target_lang_var.get()}):\n")
                f.write(text + "\n")
            
            self.status_var.set(f"Saved as {filename}")
            messagebox.showinfo("Success", f"Translation saved as {filename}")
            
        except Exception as e:
            self.show_error(f"Save error: {e}")
            
    def add_to_history(self, original, translation, source_lang, target_lang):
        """Add translation to history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            'timestamp': timestamp,
            'original': original,
            'translation': translation,
            'source_lang': source_lang,
            'target_lang': target_lang
        }
        
        self.translation_history.append(entry)
        
        # Update history listbox
        display_text = f"[{timestamp}] {source_lang} → {target_lang}: {original[:30]}..."
        self.history_listbox.insert(tk.END, display_text)
        self.history_listbox.see(tk.END)
        
    def load_from_history(self, event):
        """Load translation from history"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            entry = self.translation_history[index]
            
            # Set languages
            self.source_lang_var.set(entry['source_lang'])
            self.target_lang_var.set(entry['target_lang'])
            
            # Set text
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(1.0, entry['original'])
            
            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, entry['translation'])
            self.output_text.config(state='disabled')
            
    def clear_history(self):
        """Clear translation history"""
        self.translation_history.clear()
        self.history_listbox.delete(0, tk.END)
        self.status_var.set("History cleared")
        
    def show_error(self, message):
        """Show error message"""
        self.status_var.set("Error occurred")
        messagebox.showerror("Error", message)
        
    def load_settings(self):
        """Load saved settings"""
        try:
            if os.path.exists('translator_settings.json'):
                with open('translator_settings.json', 'r') as f:
                    settings = json.load(f)
                    self.source_lang_var.set(settings.get('source_lang', 'English'))
                    self.target_lang_var.set(settings.get('target_lang', 'Spanish'))
        except Exception:
            pass
            
    def save_settings(self):
        """Save current settings"""
        try:
            settings = {
                'source_lang': self.source_lang_var.get(),
                'target_lang': self.target_lang_var.get()
            }
            with open('translator_settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception:
            pass
            
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Handle application closing"""
        self.save_settings()
        if self.is_recording:
            self.stop_recording()
        self.root.destroy()

# Create and run the application
if __name__ == "__main__":
    app = LanguageTranslator()
    app.run()