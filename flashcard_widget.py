import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QRadioButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QCursor

class HintPopupWindow(QFrame):
    """A floating popover window that displays the word's hint/meaning."""
    def __init__(self, text, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("hintPopup")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        self.label = QLabel(f"💡 <i>{text}</i>")
        self.label.setObjectName("hintPopupLabel")
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 14px; color: #f1c40f; background: transparent; border: none; padding: 0;")
        layout.addWidget(self.label)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("hintPopupClose")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton#hintPopupClose {
                background: transparent;
                border: none;
                color: #888;
                font-size: 14px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton#hintPopupClose:hover {
                color: #e74c3c;
            }
        """)
        layout.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignTop)
        
        self.setStyleSheet("""
            QFrame#hintPopup {
                background: rgba(26, 26, 46, 0.95);
                border: 1px solid #f1c40f;
                border-radius: 8px;
            }
        """)
        self.adjustSize()

class FlashcardWidget(QWidget):
    """A widget to display a flashcard question and handle user input."""
    closed = pyqtSignal()
    card_delete_requested = pyqtSignal(dict)

    def __init__(self, card, stats_manager, vocabulary, similarity_checker, is_multiple_choice=False, parent=None):
        super().__init__(parent)
        self.card = card
        self.vocabulary = vocabulary
        self.stats_manager = stats_manager
        self.similarity_checker = similarity_checker
        self._drag_pos = None
        
        # Question type: 'translation' or 'grammar'
        has_grammar = card.get('grammar_pattern') is not None
        self.question_type = 'grammar' if has_grammar and random.random() < 0.4 else 'translation'
        
        # Check if it's the new Transition category
        self.is_transition_card = (self.card.get('category') == 'SAT Transitions & Grammar')

        # For translation questions - determine language direction
        if self.is_transition_card:
            self.question_lang, self.answer_lang = 'english', 'uzbek'
        elif self.question_type == 'translation':
            if random.choice([True, False]):
                self.question_lang, self.answer_lang = 'english', 'uzbek'
            else:
                self.question_lang, self.answer_lang = 'uzbek', 'english'
        else:
            # Grammar questions: show english verb, ask for pattern
            self.question_lang, self.answer_lang = 'english', 'grammar_pattern'

        # Smart mode selection
        is_complex_phrase = '/' in self.card['english'] or '/' in self.card.get('uzbek', '')
        is_short_answer = len(self.card['english'].split()) <= 3
        
        word_stats = self.stats_manager.get_stats_for_word(self.card)
        correct_count = word_stats.get('correct', 0)
        is_learning_phase = correct_count < 2
        
        # Grammar questions always use multiple choice (only 2 options: V-ing or to+V)
        if self.question_type == 'grammar':
            self.is_multiple_choice = True
        else:
            self.is_multiple_choice = is_learning_phase or (not is_complex_phrase and is_short_answer and is_multiple_choice)

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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Drag Bar (for moving the widget) ---
        self.drag_bar = QLabel("⋮⋮ Перетащи меня ⋮⋮")
        self.drag_bar.setObjectName("dragBar")
        self.drag_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_bar.setFixedHeight(28)
        self.drag_bar.setCursor(Qt.CursorShape.SizeAllCursor)
        main_layout.addWidget(self.drag_bar)
        
        # --- Content Layout ---
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)

        # --- Top layout for question and delete button ---
        top_layout = QHBoxLayout()
        self.question_label = QLabel()
        self.question_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.question_label.linkActivated.connect(self.toggle_hint)
        top_layout.addWidget(self.question_label, 1)
        
        top_layout.addWidget(self._create_delete_button(), 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addLayout(top_layout)
        
        main_layout.addLayout(content_layout)
        self.content_layout = content_layout  # Save reference

        # --- Answer Area ---
        if self.is_multiple_choice:
            self.setup_multiple_choice_ui(content_layout)
        else:
            self.setup_text_input_ui(content_layout)

        # --- Button ---
        self.check_button = QPushButton("Check Answer")
        self.check_button.clicked.connect(self.check_answer)
        self.check_button.setDefault(True)
        content_layout.addWidget(self.check_button)

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
        """Applies a modern glassmorphism-themed stylesheet."""
        self.setStyleSheet("""
            QWidget#main_widget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border: 1px solid #2a2e45;
                border-radius: 20px;
                color: #ecf0f1;
            }
            
            QLabel#dragBar {
                background: #222740;
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                color: #666;
                font-size: 12px;
                font-weight: normal;
                padding: 4px;
            }
            
            QLabel#dragBar:hover {
                background: #2a3050;
                color: #999;
            }
            
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #fff;
                border: none;
                padding: 12px;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 12px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
            
            QLineEdit {
                padding: 14px 18px;
                border: 2px solid #2a3050;
                border-radius: 12px;
                font-size: 18px;
                background: #1e2235;
                color: #fff;
            }
            
            QLineEdit:focus {
                border: 2px solid #00d9ff;
                background: #222740;
            }
            
            QRadioButton {
                font-size: 16px;
                padding: 10px 16px;
                border: none;
                color: #ddd;
                background: #1e2235;
                border-radius: 8px;
                margin: 4px 0;
            }
            
            QRadioButton:hover {
                background: #252a40;
                color: #fff;
            }
            
            QRadioButton:checked {
                background: #1a3a4a;
                color: #00d9ff;
            }
            
            QGroupBox {
                border: 1px solid #2a2e45;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 5px;
            }
            
            QPushButton#deleteButton {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #c0392b;
                padding: 4px;
            }
            
            QPushButton#deleteButton:hover {
                color: #e74c3c;
            }
            
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
        
        if self.question_type == 'grammar':
            # Grammar questions: only 2 options
            options = ['V-ing', 'to + V']
            random.shuffle(options)
        else:
            options = self.vocabulary.get_options_for_card(self.card, self.answer_lang)
        
        for option in options:
            radio = QRadioButton(option)
            self.radio_buttons.append(radio)
            self.options_layout.addWidget(radio)
        self.options_group.setLayout(self.options_layout)
        layout.addWidget(self.options_group)

    def set_question(self):
        """Sets the question word on the label."""
        hint_html = " <a href='hint' style='text-decoration:none; color:#f1c40f;'><sup>💡</sup></a>"
        
        if self.question_type == 'grammar':
            self.question_label.setText(f"Grammar pattern for: <b>{self.card['english']}</b>{hint_html}")
        elif getattr(self, 'is_transition_card', False):
            self.question_label.setText(f"Transition: <b>{self.card[self.question_lang]}</b>{hint_html}")
        else:
            self.question_label.setText(f"Translate: <b>{self.card[self.question_lang]}</b>{hint_html}")

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

        # Highlight correct and wrong answers in multiple choice
        if self.is_multiple_choice:
            for radio in self.radio_buttons:
                radio_text = self._normalize_answer(radio.text())
                is_this_correct = radio_text in [self._normalize_answer(ans) for ans in possible_answers]
                if is_this_correct:
                    radio.setStyleSheet("background: #2ecc71; color: white; font-weight: bold;")
                elif radio.isChecked() and not is_correct:
                    radio.setStyleSheet("background: #e74c3c; color: white;")

        if is_correct:
            self.setStyleSheet(self.styleSheet() + "QWidget#main_widget { border: 2px solid #2ecc71; }")
            self.check_button.setText("Correct! 👍")
            self.check_button.setStyleSheet("background-color: #2ecc71;")
        else:
            self.setStyleSheet(self.styleSheet() + "QWidget#main_widget { border: 2px solid #e74c3c; }")
            self.check_button.setText(f"Correct: {correct_answer_string}")
            self.check_button.setStyleSheet("background-color: #e74c3c;")

        QTimer.singleShot(4000, self.close)  # 4 seconds to see the answer

    def toggle_hint(self, link=None):
        """Toggles the visibility of the custom hint/meaning popover."""
        if hasattr(self, 'hint_popup') and self.hint_popup and self.hint_popup.isVisible():
            self.hint_popup.close()
            self.hint_popup = None
            return
            
        hint_text = self.card.get('hint', '').strip()
        if hint_text:
            self.hint_popup = HintPopupWindow(hint_text, self)
            
            # Position at top-right of the mouse click position (near the lamp icon)
            cursor_pos = QCursor.pos()
            popup_size = self.hint_popup.sizeHint()
            
            x = cursor_pos.x() + 10
            y = cursor_pos.y() - popup_size.height() - 10
            
            self.hint_popup.move(x, y)
            self.hint_popup.show()

    def request_delete(self):
        """Emits the signal to request card deletion and closes the widget."""
        print(f"Delete button clicked for: {self.card['english']}")
        self.card_delete_requested.emit(self.card)
        self.close()

    def keyPressEvent(self, event):
        """Handles key presses for Enter (check answer), Escape (close), and 1-4 (MC options)."""
        # --- CRITICAL FIX: Explicitly handle Enter/Return keys to prevent accidental deletion ---
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.check_button.isEnabled():
                self.check_button.click()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        # --- Hotkeys for multiple choice (1-4) ---
        elif self.is_multiple_choice and event.key() in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4):
            index = event.key() - Qt.Key.Key_1  # 0, 1, 2, or 3
            if index < len(self.radio_buttons):
                self.radio_buttons[index].setChecked(True)
                self.check_answer()

    def mousePressEvent(self, event):
        """Start drag when mouse pressed."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Move widget while dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """End drag when mouse released."""
        self._drag_pos = None
        event.accept()

    def closeEvent(self, event):
        """Emits a signal when the widget is closed."""
        self.closed.emit()
        super().closeEvent(event)
