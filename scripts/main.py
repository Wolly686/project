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

class VoiceAssistant:
    def __init__(self):
        print("✅ Ассистент с голосами Google активирован")
        
        # Словарь команд
        self.commands = {
            'открыть telegram': self.open_telegram,
            'открыть браузер': self.open_browser,
            'открыть проводник': self.open_explorer,
            'открыть блокнот': self.open_notepad,
            'открыть калькулятор': self.open_calculator,
            'какое время': self.get_time,
            'который час': self.get_time,
            'покажи процессы': self.show_processes,
            'закройся': self.stop,
            'стоп': self.stop,
            'выход': self.stop,
        }
        
        self.is_listening = True
        self.activation_name = "миша"
    
    def speak(self, text):
        """Произносит текст через Google TTS"""
        print(f"Ассистент: {text}")
        
        try:
            # Создаем русскую речь
            tts = gTTS(text=text, lang='ru', slow=False)
            
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                temp_path = tmp_file.name
            
            tts.save(temp_path)
            
            # Воспроизводим через sounddevice
            audio_data, sample_rate = sf.read(temp_path)
            sd.play(audio_data, sample_rate)
            sd.wait()
            
            # Удаляем временный файл
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"❌ Ошибка воспроизведения: {e}")
    
    def speak_multiple(self, texts):
        """Произносит несколько фраз подряд"""
        for text in texts:
            self.speak(text)
            time.sleep(0.3)
    
    def play_activation_sound(self):
        """Издает звук активации"""
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
        """Записывает аудио с микрофона"""
        print("🎤 Записываю аудио...")
        audio_data = sd.rec(int(duration * sample_rate), 
                           samplerate=sample_rate, 
                           channels=1, 
                           dtype='float64')
        sd.wait()
        return audio_data.flatten(), sample_rate
    
    def recognize_speech_google(self, audio_file):
        """Распознает речь через Google API"""
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
                                transcript = data['result'][0]['alternative'][0]['transcript']
                                return transcript.lower()
                        except:
                            continue
            return ""
        except Exception as e:
            print(f"Ошибка распознавания: {e}")
            return ""
    
    def listen(self):
        """Слушает и распознает речь"""
        try:
            audio_data, sample_rate = self.record_audio(duration=5)
            audio_file = "temp_audio.wav"
            sf.write(audio_file, audio_data, sample_rate)
            
            print("🔍 Обрабатываю аудио...")
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
        """Извлекает команду из текста"""
        if not text:
            return ""
        
        words = text.split()
        if words and words[0] == self.activation_name:
            return " ".join(words[1:])
        else:
            if self.activation_name in text:
                command = text.replace(self.activation_name, "").strip()
                return command
            else:
                return ""
    
    def search_web(self, query):
        """Ищет в интернете"""
        try:
            if query:
                encoded_query = urllib.parse.quote(query)
                search_url = f"https://www.google.com/search?q={encoded_query}"
                webbrowser.open(search_url)
                self.speak(f"Ищу {query}")
                return True
            else:
                self.speak("Что искать?")
                return False
        except Exception as e:
            self.speak("Не удалось выполнить поиск")
            return False
    
    def process_command(self, command):
        """Обрабатывает команду"""
        if not command:
            return
        
        self.speak("Да, сэр")
        time.sleep(1)
        
        if command.startswith('найди '):
            search_query = command[6:]
            self.search_web(search_query)
            return
        
        for cmd, action in self.commands.items():
            if cmd in command:
                action()
                return
        
        self.speak("Не понял команду, сэр")
    
    def open_telegram(self):
        try:
            webbrowser.open("https://web.telegram.org")
            self.speak("Открываю Telegram")
            return True
        except:
            self.speak("Не удалось открыть Telegram")
            return False
    
    def open_browser(self):
        try:
            webbrowser.open("https://www.google.com")
            self.speak("Открываю браузер")
            return True
        except:
            self.speak("Не удалось открыть браузер")
            return False
    
    def open_explorer(self):
        try:
            os.system("explorer")
            self.speak("Открываю проводник")
            return True
        except:
            self.speak("Не удалось открыть проводник")
            return False
    
    def open_notepad(self):
        try:
            os.system("notepad")
            self.speak("Открываю блокнот")
            return True
        except:
            self.speak("Не удалось открыть блокнот")
            return False
    
    def open_calculator(self):
        try:
            os.system("calc")
            self.speak("Открываю калькулятор")
            return True
        except:
            self.speak("Не удалось открыть калькулятор")
            return False
    
    def get_time(self):
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        self.speak(f"Сейчас {current_time}")
        return True
    
    def show_processes(self):
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
            top_processes = processes[:2]
            
            if top_processes:
                self.speak("Топ процессов по памяти:")
                for name, memory in top_processes:
                    self.speak(f"{name}: {memory:.1f}% памяти")
            else:
                self.speak("Не удалось получить список процессов")
                
            return True
        except Exception as e:
            self.speak("Не удалось получить список процессов")
            return False
    
    def stop(self):
        self.speak("До свидания")
        self.is_listening = False
        return True
    
    def run(self):
        self.speak("Ассистент Миша активирован. Говорите команды начиная с моего имени")
        
        while self.is_listening:
            print("\n" + "="*50)
            print("🔍 Слушаю... Скажите 'Миша' и команду")
            
            text = self.listen()
            
            if text:
                print(f"Распознано: {text}")
                
                if self.activation_name in text:
                    print("✅ Обнаружено имя 'Миша'")
                    self.play_activation_sound()
                    time.sleep(0.5)
                    
                    command = self.extract_command(text)
                    print(f"Команда: {command}")
                    
                    if command:
                        self.process_command(command)
                    else:
                        self.speak("Слушаю вас")
                else:
                    print("❌ Имя 'Миша' не обнаружено, игнорирую")
            
            time.sleep(1)

if __name__ == "__main__":
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        assistant.speak("Программа прервана")
    except Exception as e:
        print(f"Ошибка: {e}")