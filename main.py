import json
import os
import random
import sys

import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.popup import Popup

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

QUIZ_FILE = resource_path("quiz.json")
# Już nie potrzebujemy tej zmiennej, ale zostawienie jej nie szkodzi
QUIZ_KV_FILE = resource_path("quiz.kv")


class MainMenuScreen(Screen):
    pass
class QuizScreen(Screen):
    pass
class ResultScreen(Screen):
    pass
class WindowManager(ScreenManager):
    pass


class QuizApp(App):
    def build(self):
        self.title = 'Egzaminator KPP'
        # --- ZMIANA: Usunęliśmy blok try/except z Builder.load_file() ---
        # Kivy załaduje plik quiz.kv automatycznie dzięki poprawnej nazwie klasy.
        return WindowManager()

    def on_start(self):
        self.all_questions = []
        self.load_questions()

    def load_questions(self):
        if not os.path.exists(QUIZ_FILE):
            self.show_error_popup("Błąd krytyczny", f"Nie znaleziono bazy pytań!\nPlik '{os.path.basename(QUIZ_FILE)}' musi być w tym samym folderze co aplikacja.")
            return
        try:
            with open(QUIZ_FILE, "r", encoding="utf-8") as f:
                self.all_questions = json.load(f)
        except Exception as e:
            self.show_error_popup("Błąd krytyczny", f"Plik z pytaniami '{os.path.basename(QUIZ_FILE)}' jest uszkodzony.\nBłąd: {e}")

    def start_exam(self):
        if not self.all_questions:
            self.show_error_popup("Błąd", "Baza pytań jest pusta lub nie została załadowana.")
            return

        self.quiz_questions = random.sample(self.all_questions, min(30, len(self.all_questions)))
        self.mistake_counter = 0
        self.correct_counter = 0
        self.current_index = 0
        self.quiz_answers_history = []
        self.current_user_selection = None
        
        self.root.current = 'quiz'
        self.show_next_question()

    def show_next_question(self):
        if self.current_index >= len(self.quiz_questions):
            self.go_to_results()
            return
            
        q = self.quiz_questions[self.current_index]
        quiz_screen = self.root.get_screen('quiz')

        quiz_screen.ids.question_label.text = f"Pytanie {self.current_index + 1}/{len(self.quiz_questions)}:\n\n{q['question']}"
        quiz_screen.ids.correct_counter_label.text = f"Poprawne: {self.correct_counter}"
        quiz_screen.ids.mistake_counter_label.text = f"Błędy: {self.mistake_counter}/3"
        
        answers_box = quiz_screen.ids.answers_box
        answers_box.clear_widgets()
        self.current_user_selection = None

        for key, value in sorted(q["answers"].items()):
            btn = ToggleButton(
                text=f"{key}. {value}",
                group='answers',
                size_hint_y=None,
                height='60dp',
                text_size=(answers_box.width - 40, None),
                halign='left',
                valign='middle',
                padding=(10, 10)
            )
            btn.bind(on_press=self.select_answer)
            answers_box.add_widget(btn)

    def select_answer(self, button_instance):
        self.current_user_selection = button_instance.text.split('.')[0]

    def submit_answer(self):
        if self.current_user_selection is None:
            self.show_error_popup("Brak odpowiedzi", "Proszę wybrać jedną z odpowiedzi.")
            return

        current_question = self.quiz_questions[self.current_index]
        correct_answer = current_question.get("correct")

        self.quiz_answers_history.append({
            "user": self.current_user_selection, 
            "correct": correct_answer,
            "question_index": self.current_index
        })

        if self.current_user_selection == correct_answer:
            self.correct_counter += 1
        else:
            self.mistake_counter += 1

        if self.mistake_counter >= 3:
            self.go_to_results()
            return

        self.current_index += 1
        self.show_next_question()

    def go_to_results(self):
        result_screen = self.root.get_screen('result')
        
        if self.mistake_counter < 3:
            result_screen.ids.result_title.text = "Egzamin ZDANY"
            result_screen.ids.result_title.color = (0.2, 0.8, 0.2, 1)
        else:
            result_screen.ids.result_title.text = "Egzamin NIEZDANY"
            result_screen.ids.result_title.color = (0.9, 0.2, 0.2, 1)

        total_attempted = len(self.quiz_answers_history)
        result_screen.ids.summary_label.text = (
            f"Odpowiedziano na: {total_attempted} pytań\n"
            f"Poprawne odpowiedzi: {self.correct_counter}\n"
            f"Błędne odpowiedzi: {self.mistake_counter}"
        )

        incorrect_info_text = ""
        for answer_info in self.quiz_answers_history:
            if answer_info['user'] != answer_info['correct']:
                q = self.quiz_questions[answer_info["question_index"]]
                
                incorrect_info_text += f"[b]PYTANIE:[/b]\n{q['question']}\n\n"
                your_ans_text = q['answers'].get(answer_info['user'], "Brak odpowiedzi")
                correct_ans_text = q['answers'].get(answer_info['correct'], "N/A")

                incorrect_info_text += f"Twoja odpowiedź: [color=ff3333]{answer_info['user']}. {your_ans_text}[/color]\n"
                incorrect_info_text += f"Poprawna odpowiedź: [color=33ff33]{answer_info['correct']}. {correct_ans_text}[/color]\n"
                incorrect_info_text += "-"*50 + "\n"
        
        result_screen.ids.errors_details.text = incorrect_info_text
        self.root.current = 'result'

    def go_to_menu(self):
        self.root.current = 'main_menu'

    def show_error_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()


if __name__ == '__main__':
    QuizApp().run()