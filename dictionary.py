from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock
import random
import os
import datetime

class DictionaryApp(App):
    def build(self):
        self.words = {}
        self.used_questions = set()  # Barcha savollar uchun
        self.correct_answers = 0
        self.wrong_answers = 0
        self.skipped_questions = 0
        self.current_question = None
        self.remaining_time = 30  
        self.selected_file = None
        self.ask_value_instead_of_key = False  # Key yoki value orqali savolni tanlash

        layout = BoxLayout(orientation="vertical")

        # Savol raqami va vaqtni ko‘rsatuvchi qator
        header_layout = BoxLayout(size_hint_y=0.1, spacing=10)

        self.counter_label = Label(text="Test: [0/0]", font_size="18sp", size_hint_x=0.5)
        self.time_label = Label(text="Vaqt: 30s", font_size="18sp", size_hint_x=0.5, halign="right")

        header_layout.add_widget(self.counter_label)
        header_layout.add_widget(self.time_label)

        layout.add_widget(header_layout)

        # Savol chiqadigan label
        self.label = Label(text="Test tanlang yoki boshlang", size_hint_y=0.2, font_size="20sp")
        layout.add_widget(self.label)

        # Javob kiritish uchun input
        self.input = TextInput(size_hint_y=0.2, font_size="18sp", multiline=False)
        layout.add_widget(self.input)

        # Tugmalar (3x2 Grid)
        button_grid = GridLayout(size_hint_y=0.5, cols=2, spacing=5, padding=10)
        
        self.check_button = Button(text="Check", font_size="22sp", on_press=self.check_answer)
        self.next_button = Button(text="Next", font_size="22sp", on_press=self.next_question)
        self.restart_button = Button(text="Restart", font_size="22sp", on_press=self.restart_quiz)
        self.finish_button = Button(text="Finish", font_size="22sp", on_press=self.finish_quiz)
        self.select_test_button = Button(text="Select Test", font_size="22sp", on_press=self.open_filechooser)
        self.exit_button = Button(text="Exit", font_size="22sp", on_press=self.stop)

        button_grid.add_widget(self.check_button)
        button_grid.add_widget(self.next_button)
        button_grid.add_widget(self.restart_button)
        button_grid.add_widget(self.finish_button)
        button_grid.add_widget(self.select_test_button)
        button_grid.add_widget(self.exit_button)

        layout.add_widget(button_grid)

        return layout

    def update_display(self):
        """ Savol va hisoblagichni yangilash """
        self.counter_label.text = f"Test: [{len(self.used_questions)}/{len(self.words)*2}]"
        self.time_label.text = f"Vaqt: {self.remaining_time}s"

    def open_filechooser(self, *args):
        """ Fayl tanlash oynasini ochish """
        content = BoxLayout(orientation="vertical")
        filechooser = FileChooserListView(filters=["*.txt"])

        btn_layout = BoxLayout(size_hint_y=0.2)
        select_btn = Button(text="Tanlash", on_press=lambda x: (self.load_selected_file(filechooser.selection), popup.dismiss()))
        cancel_btn = Button(text="Bekor qilish", on_press=lambda x: popup.dismiss())

        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)

        content.add_widget(filechooser)
        content.add_widget(btn_layout)

        popup = Popup(title="Fayl tanlash", content=content, size_hint=(0.9, 0.9))
        popup.open()

    def load_selected_file(self, selection):
        """ Tanlangan fayldan testni yuklash """
        if not selection:
            return

        file_path = selection[0]
        if not os.path.exists(file_path):
            self.label.text = " Fayl topilmadi!"
            return

        self.selected_file = file_path
        self.words = self.load_words(file_path)

        if not self.words:
            self.label.text = "Xato: Fayl noto‘g‘ri formatda!"
        else:
            self.label.text = "Test yuklandi! Boshlash uchun 'Next' bosing."
            self.used_questions.clear()
            self.input.disabled = False
            self.update_display()

    def load_words(self, file_path):
        """ Fayldan lug‘atni yuklash """
        words = {}

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    parts = line.strip().split(" - ")
                    if len(parts) == 2:
                        key, value = parts
                        words[key] = value
                    else:
                        return {}  # Noto'g'ri format
        except FileNotFoundError:
            print("ERROR: Fayl topilmadi!")

        return words

    def get_random_question(self):
        """ Key yoki Value bo‘yicha tasodifiy savol tanlash """
        remaining_questions = set(self.words.keys()).union(set(self.words.values())) - self.used_questions

        if remaining_questions:
            self.ask_value_instead_of_key = random.choice([True, False])  # Tasodifiy value yoki key

            if self.ask_value_instead_of_key:
                question = random.choice(list(set(self.words.values()) - self.used_questions))  # Value dan tanlash
            else:
                question = random.choice(list(set(self.words.keys()) - self.used_questions))  # Key dan tanlash

            self.used_questions.add(question)
            return question
        return None

    def next_question(self, *args):
        """ Keyingi savolni chiqarish """
        if len(self.used_questions) == len(self.words) * 2:  # Barcha savollarni tugatish
            self.finish_quiz()
            return

        self.current_question = self.get_random_question()

        if self.current_question:
            if self.ask_value_instead_of_key:
                # Value bo‘yicha savol berish
                self.label.text = f"{self.current_question}"
            else:
                # Key bo‘yicha savol berish
                self.label.text = self.current_question
            self.input.text = ""
            self.remaining_time = 30  
            self.update_display()
            Clock.unschedule(self.update_time)  
            Clock.schedule_interval(self.update_time, 1)  

    def check_answer(self, *args):
        """ Javobni tekshirish """
        user_input = self.input.text.strip().lower()

        # Javobni tekshirish
        if self.ask_value_instead_of_key:
            # Value bo‘yicha javob tekshirish
            correct_answer = next((k for k, v in self.words.items() if v.lower() == self.current_question.lower()), "")
        else:
            # Key bo‘yicha javob tekshirish
            correct_answer = self.words.get(self.current_question, "").lower()

        if user_input == correct_answer:
            self.show_popup("To‘g‘ri!", True)
            self.correct_answers += 1
            Clock.schedule_once(self.next_question, 1.5)
        else:
            self.show_popup("Xato, qaytadan urinib ko‘ring!", False)
            self.wrong_answers += 1

    def show_popup(self, message, is_correct):
        """ Javob natijasi haqida popup ko'rsatish """
        popup_content = Label(text=message)
        popup = Popup(title="Natija", content=popup_content, size_hint=(0.8, 0.4))
        popup.open()

        # Popupni 1 soniya o'tgach yopish
        Clock.schedule_once(lambda dt: popup.dismiss(), 0.5)

    def update_time(self, *args):
        """ Vaqtni 1 soniyaga kamaytirish """
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.time_label.text = f"Vaqt: {self.remaining_time}s"
        else:
            Clock.unschedule(self.update_time)
            self.label.text = "Vaqt tugadi!"
            self.skipped_questions += 1
            Clock.schedule_once(self.next_question, 2)

    def finish_quiz(self, *args):
        """ O'yinni tugatish va natijani ko'rsatish """
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_text = (
            f"O'yin tugadi!\n"
            f"To‘g‘ri javoblar: {self.correct_answers}\n"
            f"Xato javoblar: {self.wrong_answers}\n"
            f"Tashlab ketilgan savollar: {self.skipped_questions}\n"
        )

        # Natijalarni faylga yozish
        result_file = f"result_{date}.txt"
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(result_text)

        # Natijani ekranda ko'rsatish
        self.label.text = result_text
        self.input.disabled = True  # Inputni o'chirish
        Clock.unschedule(self.update_time)  # Vaqtni yangilanishini to'xtatish

    def restart_quiz(self, *args):
        """ Testni qayta boshlash """
        self.used_questions.clear()
        self.correct_answers = 0
        self.wrong_answers = 0
        self.skipped_questions = 0
        self.remaining_time = 30
        self.label.text = "O‘yin qayta boshlandi! 'Next' tugmasini bosing."
        self.input.text = ""
        self.update_display()

if __name__ == "__main__":
    DictionaryApp().run()