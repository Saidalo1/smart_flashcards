import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

class FlashcardWidget(QWidget):
    """A widget to display a flashcard question and handle user input."""
    closed = pyqtSignal()
    card_delete_requested = pyqtSignal(dict)

    def __init__(self, card, stats_manager, vocabulary, similarity_checker, is_multiple_choice=False, parent=None):
        """Initializes the flashcard view."""
        super().__init__(parent)
        self.card = card
        self.vocabulary = vocabulary
        self.stats_manager = stats_manager
        self.similarity_checker = similarity_checker

        # Determine language direction and question type
        if random.choice([True, False]):
            self.question_lang, self.answer_lang = 'english', 'uzbek'
        else:
            self.question_lang, self.answer_lang = 'uzbek', 'english'

        # --- Smart Mode Selection ---
        # Use text input for complex phrases (containing '/') or longer answers.
        is_complex_phrase = '/' in self.card['english'] or '/' in self.card['uzbek']
        is_short_answer = len(self.card['english'].split()) <= 3
        self.is_multiple_choice = not is_complex_phrase and is_short_answer and is_multiple_choice
        # --------------------------

        self.init_ui()
        self.set_question()

    def _normalize_answer(self, text):
        """Normalizes text for comparison by standardizing quotes and whitespace."""
        replacements = {
            "‘": "'", "’": "'", "ʻ": "'", "ʼ": "'",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.strip().lower()

    def init_ui(self):
        """Sets up the user interface of the widget."""
        self.setObjectName("main_widget")
        self.setWindowTitle('Smart Flashcards')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # --- Main Layout ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Top layout for question and delete button ---
        top_layout = QHBoxLayout()
        self.question_label = QLabel()
        top_layout.addWidget(self.question_label, 1)
        top_layout.addWidget(self._create_delete_button(), 0, Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(top_layout)

        # --- Answer Area ---
        if self.is_multiple_choice:
            self.setup_multiple_choice_ui(main_layout)
        else:
            self.setup_text_input_ui(main_layout)

        # --- Button ---
        self.check_button = QPushButton("Check Answer")
        self.check_button.clicked.connect(self.check_answer)
        self.check_button.setDefault(True)  # *** CRITICAL FIX: Prevents Enter from triggering delete ***
        main_layout.addWidget(self.check_button)

        self.apply_stylesheet()
        self.setLayout(main_layout)

    def _create_delete_button(self):
        """Creates a prominent, red, non-focusable delete button."""
        delete_button = QPushButton("🗑️")
        delete_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # --- Add a unique name to target with a specific style ---
        delete_button.setObjectName("deleteButton")
        delete_button.setFixedSize(32, 32)
        delete_button.setToolTip("Удалить эту карточку навсегда")
        delete_button.clicked.connect(self.request_delete)
        return delete_button

    def apply_stylesheet(self):
        """Applies a modern, dark-themed stylesheet to the widget."""
        self.setStyleSheet("""
            QWidget#main_widget { background-color: #2c3e50; border: 1px solid #34495e; border-radius: 15px; color: #ecf0f1; }
            QLabel { font-size: 22px; font-weight: bold; color: #ecf0f1; border: none; padding: 10px; }
            QPushButton { background-color: #3498db; color: white; border-radius: 8px; padding: 10px; font-size: 16px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #2980b9; }
            QLineEdit { padding: 10px; border: 1px solid #34495e; border-radius: 8px; font-size: 18px; background-color: #34495e; color: #ecf0f1; }
            QRadioButton { font-size: 16px; padding: 5px; border: none; }
            QGroupBox { border: 1px solid #34495e; border-radius: 8px; margin-top: 10px; }

            /* --- DEFINITIVE FIX: Style the delete button by its unique name --- */
            QPushButton#deleteButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: #e74c3c; /* Red */
                padding: 0;
            }
            QPushButton#deleteButton:hover { color: #c0392b; }
        """)

    def setup_text_input_ui(self, layout):
        """Sets up UI for manual text input."""
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Your translation...")
        self.answer_input.returnPressed.connect(self.check_answer)
        layout.addWidget(self.answer_input)
        self.answer_input.setFocus()

    def setup_multiple_choice_ui(self, layout):
        """Sets up UI for multiple choice questions."""
        self.options_group = QGroupBox()
        self.options_layout = QVBoxLayout()
        self.radio_buttons = []
        options = self.vocabulary.get_options_for_card(self.card, self.answer_lang)
        for option in options:
            radio = QRadioButton(option)
            self.radio_buttons.append(radio)
            self.options_layout.addWidget(radio)
        self.options_group.setLayout(self.options_layout)
        layout.addWidget(self.options_group)

    def set_question(self):
        """Sets the question word on the label."""
        self.question_label.setText(f"Translate: <b>{self.card[self.question_lang]}</b>")

    def check_answer(self):
        """Checks the answer and provides dynamic visual feedback."""
        correct_answer_string = self.card[self.answer_lang]
        user_answer = ""
        if self.is_multiple_choice:
            for radio in self.radio_buttons:
                if radio.isChecked():
                    user_answer = radio.text()
                    break
        else:
            user_answer = self.answer_input.text()

        self.check_button.setEnabled(False)
        if not self.is_multiple_choice:
            self.answer_input.setEnabled(False)
        else:
            for radio in self.radio_buttons:
                radio.setEnabled(False)

        possible_answers = [ans.strip() for ans in correct_answer_string.split('/')]
        if self.is_multiple_choice:
            is_correct = self._normalize_answer(user_answer) in [self._normalize_answer(ans) for ans in possible_answers]
        else:
            is_correct = any(self.similarity_checker.are_similar(user_answer, p_ans) for p_ans in possible_answers)

        self.stats_manager.record_answer(self.card, is_correct)

        if is_correct:
            self.setStyleSheet(self.styleSheet() + "QWidget#main_widget { border: 2px solid #2ecc71; }")
            self.check_button.setText("Correct! 👍")
            self.check_button.setStyleSheet("background-color: #2ecc71;")
        else:
            self.setStyleSheet(self.styleSheet() + "QWidget#main_widget { border: 2px solid #e74c3c; }")
            self.check_button.setText(f"Correct: {correct_answer_string}")
            self.check_button.setStyleSheet("background-color: #e74c3c;")

        QTimer.singleShot(2000, self.close)

    def request_delete(self):
        """Emits the signal to request card deletion and closes the widget."""
        print(f"Delete button clicked for: {self.card['english']}")
        self.card_delete_requested.emit(self.card)
        self.close()

    def keyPressEvent(self, event):
        """Handles key presses for Enter (check answer) and Escape (close)."""
        # --- CRITICAL FIX: Explicitly handle Enter/Return keys to prevent accidental deletion ---
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.check_button.isEnabled():
                self.check_button.click()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()

    def closeEvent(self, event):
        """Emits a signal when the widget is closed."""
        self.closed.emit()
        super().closeEvent(event)
