import sounddevice as sd
import soundfile as sf
import os
import webbrowser
import time
import psutil
import requests
import json
import numpy as np
import urllib.parse
from gtts import gTTS
import tempfile
import tkinter as tk
from PIL import Image, ImageTk
import threading
import random
from datetime import datetime

# ===== КЛАСС ДЛЯ ГИФОК (ТОЧНО РАБОЧИЙ) =====
class GifDisplay:
    def __init__(self):
        self.root = None
        self.label = None
        self.frames = []
        self.current_frame = 0
        self.is_running = False
        self.gif_thread = None
        self.POSITION_FILE = "gif_position.json"
        
    def load_position(self):
        try:
            with open(self.POSITION_FILE, 'r') as f:
                pos = json.load(f)
                return pos.get('x', 500), pos.get('y', 300)
        except:
            return 500, 300

    def save_position(self):
        if self.root and self.is_running:
            try:
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                with open(self.POSITION_FILE, 'w') as f:
                    json.dump({'x': x, 'y': y}, f)
            except:
                pass

    def load_gif(self, gif_path):
        self.frames = []
        try:
            gif = Image.open(gif_path)
            try:
                while True:
                    self.frames.append(ImageTk.PhotoImage(gif.copy()))
                    gif.seek(len(self.frames))
            except EOFError:
                pass
            return True
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False

    def show_random_gif_from_folder(self, folder_path):
        if not os.path.exists(folder_path):
            return False
        
        gif_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.gif'):
                gif_files.append(os.path.join(folder_path, file))
        
        if not gif_files:
            return False
        
        random_gif = random.choice(gif_files)
        if self.load_gif(random_gif) and self.frames:
            if self.label:
                self.label.config(image=self.frames[0])
                x, y = self.load_position()
                self.root.geometry(f"{self.frames[0].width()}x{self.frames[0].height()}+{x}+{y}")
            return True
        return False

    def animate(self):
        if not self.is_running:
            return
        if self.frames and self.label:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.label.config(image=self.frames[self.current_frame])
        if self.is_running:
            self.root.after(50, self.animate)

    def start_move(self, event):
        self.root.x = event.x
        self.root.y = event.y

    def on_move(self, event):
        if self.root:
            x = self.root.winfo_x() + (event.x - self.root.x)
            y = self.root.winfo_y() + (event.y - self.root.y)
            self.root.geometry(f"+{x}+{y}")
            self.save_position()

    def on_closing(self):
        self.save_position()
        self.is_running = False
        if self.root:
            self.root.quit()
            self.root.destroy()

    def run_gif(self):
        self.is_running = True
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes('-topmost', True)
        self.root.wm_attributes('-transparentcolor', 'black')
        self.root.config(bg='black')
        
        self.label = tk.Label(self.root, bg='black')
        self.label.pack()
        
        self.label.bind('<Button-1>', self.start_move)
        self.label.bind('<B1-Motion>', self.on_move)
        self.root.bind('<Escape>', lambda e: self.on_closing())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.animate()
        self.root.mainloop()

    def show_gif(self, folder_path):
        if not self.is_running:
            self.gif_thread = threading.Thread(target=self.run_gif, daemon=True)
            self.gif_thread.start()
            time.sleep(1)
        
        return self.show_random_gif_from_folder(folder_path)

    def hide_gif(self):
        self.on_closing()
        self.is_running = False

# ===== ТВОЙ АССИСТЕНТ =====
class VoiceAssistant:
    def __init__(self):
        print("✅ Ассистент активирован")
        
        self.gif = GifDisplay()
        self.base_gif_folder = r"C:\Users\Wolly\Desktop\deekpeekyukinoy\gifs"
        
        self.gif_folders = {
            'idle': os.path.join(self.base_gif_folder, 'idle'),
            'no_reco': os.path.join(self.base_gif_folder, 'no_reco'),
            'search': os.path.join(self.base_gif_folder, 'search'),
            'find': os.path.join(self.base_gif_folder, 'find')
        }
        
        for folder in self.gif_folders.values():
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                except:
                    pass
        
        self.is_listening = True
        self.activation_name = "миша"
    
    def show_gif_by_type(self, gif_type):
        folder = self.gif_folders.get(gif_type, self.gif_folders['idle'])
        self.gif.show_gif(folder)
    
    def speak(self, text):
        print(f"Ассистент: {text}")
        try:
            tts = gTTS(text=text, lang='ru', slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                temp_path = tmp_file.name
            tts.save(temp_path)
            audio_data, sample_rate = sf.read(temp_path)
            sd.play(audio_data, sample_rate)
            sd.wait()
            os.unlink(temp_path)
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def play_activation_sound(self):
        try:
            duration = 0.2
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = 0.3 * np.sin(2 * np.pi * 1000 * t)
            sd.play(audio, sample_rate)
            sd.wait()
        except:
            pass
    
    def record_audio(self, duration=5, sample_rate=16000):
        print("🎤 Слушаю...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float64')
        sd.wait()
        return audio_data.flatten(), sample_rate
    
    def recognize_speech_google(self, audio_file):
        try:
            with open(audio_file, 'rb') as f:
                audio_content = f.read()
            
            url = "http://www.google.com/speech-api/v2/recognize?output=json&lang=ru-RU&key=AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
            headers = {'Content-Type': 'audio/l16; rate=16000'}
            response = requests.post(url, data=audio_content, headers=headers)
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if 'result' in data and len(data['result']) > 0:
                                return data['result'][0]['alternative'][0]['transcript'].lower()
                        except:
                            continue
            return ""
        except Exception as e:
            print(f"Ошибка: {e}")
            return ""
    
    def listen(self):
        try:
            audio_data, sample_rate = self.record_audio(duration=5)
            audio_file = "temp_audio.wav"
            sf.write(audio_file, audio_data, sample_rate)
            
            text = self.recognize_speech_google(audio_file)
            
            try:
                os.remove(audio_file)
            except:
                pass
                
            return text
        except Exception as e:
            print(f"Ошибка: {e}")
            return ""
    
    def extract_command(self, text):
        if not text:
            return ""
        
        words = text.split()
        if words and words[0] == self.activation_name:
            return " ".join(words[1:])
        else:
            if self.activation_name in text:
                return text.replace(self.activation_name, "").strip()
            else:
                return ""
    
    def search_web(self, query=None):
        try:
            if query:
                self.show_gif_by_type('find')
                encoded_query = urllib.parse.quote(query)
                search_url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(search_url)
                self.speak(f"Ищу {query}")
                return True
            else:
                self.speak("Что искать?")
                return False
        except:
            self.speak("Не удалось выполнить поиск")
            return False
    
    def process_command(self, command):
        if not command:
            return
        
        print(f"Команда: {command}")
        
        if command.startswith('найди '):
            self.show_gif_by_type('find')
            search_query = command[6:]
            self.search_web(search_query)
        
        elif 'открыть' in command or 'запусти' in command:
            self.show_gif_by_type('search')
            
            if 'telegram' in command or 'телеграм' in command:
                webbrowser.open("https://web.telegram.org")
                self.speak("Открываю Telegram")
            elif 'браузер' in command or 'browser' in command:
                webbrowser.open("https://google.com")
                self.speak("Открываю браузер")
            elif 'проводник' in command or 'explorer' in command:
                os.system("explorer")
                self.speak("Открываю проводник")
            elif 'блокнот' in command or 'notepad' in command:
                os.system("notepad")
                self.speak("Открываю блокнот")
            elif 'калькулятор' in command or 'calculator' in command:
                os.system("calc")
                self.speak("Открываю калькулятор")
            else:
                self.speak("Не знаю как открыть")
        
        elif 'время' in command or 'час' in command:
            self.show_gif_by_type('search')
            current_time = datetime.now().strftime("%H:%M")
            self.speak(f"Сейчас {current_time}")
        
        elif 'процессы' in command or 'процесс' in command:
            self.show_gif_by_type('search')
            try:
                processes = []
                for proc in psutil.process_iter(['name', 'memory_percent']):
                    try:
                        memory = proc.info['memory_percent']
                        if memory is not None:
                            processes.append((proc.info['name'], memory))
                    except:
                        pass
                
                processes.sort(key=lambda x: x[1], reverse=True)
                top = processes[:3]
                
                if top:
                    self.speak("Топ процессов:")
                    for name, mem in top:
                        self.speak(f"{name}: {mem:.1f}%")
            except:
                self.speak("Не удалось получить процессы")
        
        elif 'стоп' in command or 'выход' in command or 'закройся' in command:
            self.show_gif_by_type('search')
            self.speak("До свидания")
            self.is_listening = False
            self.gif.hide_gif()
        
        else:
            self.show_gif_by_type('no_reco')
            self.speak("Не понял команду")
    
    def run(self):
        self.show_gif_by_type('idle')
        self.speak("Ассистент Миша активирован. Говорите команды")
        
        while self.is_listening:
            print("\n" + "="*50)
            self.show_gif_by_type('idle')
            
            text = self.listen()
            
            if text:
                print(f"Распознано: {text}")
                
                if self.activation_name in text:
                    print("✅ Обнаружен Миша")
                    self.play_activation_sound()
                    time.sleep(0.5)
                    
                    command = self.extract_command(text)
                    
                    if command:
                        self.process_command(command)
                    else:
                        self.show_gif_by_type('idle')
                        self.speak("Слушаю")
                else:
                    print("❌ Миша не обнаружен")
                    self.show_gif_by_type('no_reco')
                    time.sleep(1)
            
            time.sleep(0.5)

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("="*50)
    print("ГОЛОСОВОЙ АССИСТЕНТ")
    print("="*50)
    print("Папки:")
    print("- idle: ожидание")
    print("- no_reco: не понял")
    print("- search: открыть")
    print("- find: найти")
    print("="*50)
    
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nВыход")
        assistant.gif.hide_gif()
    except Exception as e:
        print(f"Ошибка: {e}")
        assistant.gif.hide_gif()