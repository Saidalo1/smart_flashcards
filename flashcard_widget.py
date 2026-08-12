import random
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QRadioButton, QStyle, QStyleOption, QButtonGroup, QLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QPainter


# --- Color themes per study mode ---
MODE_THEMES = {
    'translation': {
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, '
                     'stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460)',
        'border': '#2a4a7f',
        'badge_bg': '#1a3a5c',
        'badge_color': '#00d9ff',
        'badge_text': '🌐 ПЕРЕВОД',
        'placeholder': 'Введите перевод...',
    },
    'definition': {
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, '
                     'stop:0 #1a2e1a, stop:0.5 #163e21, stop:1 #0f6034)',
        'border': '#2a7f4a',
        'badge_bg': '#1a4a2e',
        'badge_color': '#2ecc71',
        'badge_text': '📝 ОПРЕДЕЛЕНИЕ',
        'placeholder': 'Что означает это слово?...',
    },
    'synonym': {
        'gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, '
                     'stop:0 #2e1a2e, stop:0.5 #3e1640, stop:1 #600f60)',
        'border': '#7f2a7f',
        'badge_bg': '#4a1a5c',
        'badge_color': '#a855f7',
        'badge_text': '🔀 СИНОНИМ',
        'placeholder': 'Введите синоним...',
    },
}


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


class PremiumOptionWidget(QFrame):
    """A clickable option card with radio button and word-wrapped label.

    Handles long definition texts gracefully without clipping.
    """
    clicked = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName("premiumOption")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.radio = QRadioButton()
        self.radio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.radio.setStyleSheet("""
            QRadioButton {
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }
            QRadioButton::indicator {
                width: 18px; height: 18px;
                border: 2px solid #555;
                border-radius: 10px;
                background: #1e2235;
            }
            QRadioButton::indicator:checked {
                background: #00d9ff;
                border-color: #00d9ff;
            }
        """)
        layout.addWidget(self.radio)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            "font-size: 15px; color: #eee; font-weight: normal; "
            "background: transparent; padding: 0; border: none;"
        )
        layout.addWidget(self.label, 1)

        self._apply_default_style()

    def _apply_default_style(self):
        self.setStyleSheet("""
            QFrame#premiumOption {
                background: #1e2235;
                border: 2px solid #2a2e45;
                border-radius: 10px;
            }
            QFrame#premiumOption:hover {
                background: #252a40;
                border-color: #00d9ff;
            }
        """)

    def set_result_style(self, is_correct_option, was_selected_wrong=False):
        """Highlights option after answer check."""
        if is_correct_option:
            self.setStyleSheet("""
                QFrame#premiumOption {
                    background: #1a4a2e;
                    border: 2px solid #2ecc71;
                    border-radius: 10px;
                }
            """)
            self.label.setStyleSheet(
                "font-size: 15px; color: #2ecc71; font-weight: bold; "
                "background: transparent; padding: 0; border: none;"
            )
        elif was_selected_wrong:
            self.setStyleSheet("""
                QFrame#premiumOption {
                    background: #4a1a1a;
                    border: 2px solid #e74c3c;
                    border-radius: 10px;
                }
            """)
            self.label.setStyleSheet(
                "font-size: 15px; color: #e74c3c; font-weight: bold; "
                "background: transparent; padding: 0; border: none;"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.radio.setChecked(True)
            self.clicked.emit()
            event.accept()

    def text(self):
        return self.label.text()

    def isChecked(self):
        return self.radio.isChecked()

    def setChecked(self, checked):
        self.radio.setChecked(checked)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.radio.setEnabled(enabled)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if enabled
            else Qt.CursorShape.ArrowCursor
        )


class GrabOnClickLineEdit(QLineEdit):
    """QLineEdit that engages the card for typing when clicked.

    In X11 overlay (override-redirect) mode the window can't hold keyboard focus,
    so clicking the field promotes the card to a normal managed window (via the
    supplied callback) so typing works and survives win+space. Off X11 the
    callback just focuses the field.
    """

    def __init__(self, on_click, parent=None):
        super().__init__(parent)
        self._on_click = on_click

    def mousePressEvent(self, event):
        if self._on_click:
            self._on_click()
        super().mousePressEvent(event)


class FlashcardWidget(QFrame):
    """A widget to display a flashcard question and handle user input."""
    closed = pyqtSignal()
    card_delete_requested = pyqtSignal(dict)

    def __init__(self, card, stats_manager, vocabulary, similarity_checker,
                 is_multiple_choice=False, config_manager=None,
                 accept_focus=True, parent=None):
        super().__init__(parent)
        self.card = card
        self.vocabulary = vocabulary
        self.stats_manager = stats_manager
        self.similarity_checker = similarity_checker
        self.config_manager = config_manager
        # When False (timer-driven overlay) the window is barred from EVER taking
        # keyboard focus unsolicited — so pressing win+space (language switch) or
        # any global shortcut while you type elsewhere can't yank focus onto the
        # card. Explicit summons (hotkey) pass True to allow typing an answer.
        self._accept_focus = accept_focus
        self._drag_pos = None

        # On Linux under the xcb platform (X11 / XWayland) a PASSIVE overlay is
        # shown as an override-redirect window so the WM can't hand it focus
        # unsolicited (e.g. on win+space while you type elsewhere). The moment the
        # user engages it to type, it is promoted to a normal managed window (see
        # _promote_to_managed) so it holds focus through global shortcuts.
        self._x11_overlay = False
        try:
            import sys as _sys
            from PyQt6.QtWidgets import QApplication as _QA
            _app = _QA.instance()
            self._x11_overlay = (
                _sys.platform.startswith('linux')
                and _app is not None
                and _app.platformName() == 'xcb'
            )
        except Exception:
            self._x11_overlay = False
        # True while the window is an override-redirect (unmanaged) overlay.
        self._is_bypass = False

        # --- Determine study mode for this card ---
        self.study_mode = self._resolve_study_mode()

        # Check if it's the Transition category (preserve legacy logic)
        self.is_transition_card = (
            self.card.get('category') == 'SAT Transitions & Grammar'
        )

        # --- Set question/answer language based on study mode ---
        if self.study_mode.startswith('definition'):
            self.question_lang = 'english'
            self.answer_lang = 'definition'
        elif self.study_mode.startswith('synonym'):
            self.question_lang = 'english'
            self.answer_lang = 'synonyms'
        else:
            # Translation mode. We never quiz the grammar pattern itself — the
            # pattern is shown inline in the word title (see set_question), so the
            # learner always sees e.g. "avoid doing sth" while still being asked
            # for the meaning.
            if self.is_transition_card:
                if 'uzbek' in self.card and self.card['uzbek']:
                    self.question_lang, self.answer_lang = 'english', 'uzbek'
                else:
                    self.question_lang, self.answer_lang = 'english', 'english'
            elif random.choice([True, False]):
                self.question_lang, self.answer_lang = 'english', 'uzbek'
            else:
                self.question_lang, self.answer_lang = 'uzbek', 'english'

        # --- Smart multiple-choice decision ---
        self.is_multiple_choice = self.study_mode.endswith('_mc')

        self.init_ui()
        self.set_question()

    def _resolve_study_mode(self):
        """Determines the actual study mode for this card.

        Handles:
        - Config-based static modes (translation/definition/synonym)
        - Adaptive mode (mastery-based progression)
        - Automatic fallback if card lacks required fields
        """
        config_mode = 'adaptive'
        if self.config_manager:
            config_mode = self.config_manager.study_mode

        if config_mode == 'adaptive':
            mode = self.stats_manager.get_mastery_level(self.card)
        else:
            # Config is static: 'translation', 'definition', 'synonym'
            # Progress static mode based on its specific mc -> text progression
            mc_mode = f"{config_mode}_mc"
            text_mode = f"{config_mode}_text"

            # Check if text mode is unlocked
            word_key = self.stats_manager._get_word_key(self.card)
            self.stats_manager._ensure_mode_stats(word_key)
            mc_streak = self.stats_manager.stats[word_key].get(mc_mode, {}).get('streak', 0)
            if mc_streak >= 3:
                mode = text_mode
            else:
                mode = mc_mode

        # Fallbacks: if card doesn't have required fields, downgrade dynamically
        has_uzbek = bool((self.card.get('uzbek') or '').strip())
        has_definition = bool((self.card.get('definition') or '').strip())
        has_synonyms = bool(self.card.get('synonyms'))

        if mode.startswith('synonym') and not has_synonyms:
            mode = 'definition_text' if has_definition else 'translation_text'
        if mode.startswith('definition') and not has_definition:
            mode = 'translation_text' if has_uzbek else 'translation_mc'
        if mode.startswith('translation') and not has_uzbek:
            mode = 'definition_mc' if has_definition else 'translation_mc'

        print(f"[STUDY_MODE] {self.card['english']}: resolved mode = {mode}")
        return mode

    def _normalize_answer(self, text):
        replacements = {"'": "'", "\u2019": "'", "\u02bb": "'", "\u02bc": "'"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.strip().lower()

    def init_ui(self):
        self.setObjectName("main_widget")
        self.setWindowTitle('Smart Flashcards')

        # A pinned overlay that floats above other windows (incl. games) and is
        # NOT modal — a modal window steals ALL input from whatever you're doing.
        flags = (
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        # Passive timer overlay on X11 -> override-redirect so it never steals
        # focus. Explicitly-summoned cards (accept_focus) start as normal managed
        # windows so they can hold keyboard focus through win+space etc.
        if self._x11_overlay and not self._accept_focus:
            flags |= Qt.WindowType.X11BypassWindowManagerHint
            self._is_bypass = True
        self.setWindowFlags(flags)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Never activate on show — the card must not pull focus off the active
        # app when it appears. You answer it by mouse; keyboard is taken only on
        # an explicit click into the field (which promotes it) or via the hotkey.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        if not self._x11_overlay and not self._accept_focus:
            # Non-X11 fallback (native Wayland / other WMs): best-effort hint to
            # the WM not to focus the passive overlay.
            self.setAttribute(Qt.WidgetAttribute.WA_X11DoNotAcceptFocus)

        self.setMinimumWidth(460)
        self.setMaximumWidth(600)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.drag_bar = QLabel("⋮⋮ Перетащи меня ⋮⋮")
        self.drag_bar.setObjectName("dragBar")
        self.drag_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_bar.setFixedHeight(28)
        self.drag_bar.setCursor(Qt.CursorShape.SizeAllCursor)
        main_layout.addWidget(self.drag_bar)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 12)
        content_layout.setSpacing(10)

        # Mode badge is not added to layout as color coding is sufficient
        base_mode = self.study_mode.split('_')[0]
        theme = MODE_THEMES.get(base_mode, MODE_THEMES['translation'])

        top_layout = QHBoxLayout()
        self.question_label = QLabel()
        self.question_label.setObjectName("questionLabel")
        self.question_label.setWordWrap(True)
        top_layout.addWidget(self.question_label, 1)

        # 💡 as a real button. A QLabel <a> link needs hover/hit-test events that
        # never reach the override-redirect X11 overlay, so link clicks silently
        # did nothing. A QPushButton receives clicks reliably (like the answer
        # options do).
        self.hint_button = QPushButton("💡")
        self.hint_button.setObjectName("hintButton")
        self.hint_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hint_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.hint_button.setFixedSize(32, 32)
        self.hint_button.setToolTip("Подсказка")
        self.hint_button.clicked.connect(self.toggle_hint)
        # Styled via apply_stylesheet (#hintButton), exactly like #deleteButton.
        # A per-widget stylesheet here would miss the generic QPushButton padding
        # override and the emoji would get clipped out of the fixed-size button.
        self.hint_button.hide()
        top_layout.addWidget(self.hint_button, 0, Qt.AlignmentFlag.AlignTop)

        top_layout.addWidget(self._create_delete_button(), 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addLayout(top_layout)

        # Hint shown as a floating overlay: a child of the window that is NOT in
        # any layout, so it paints ABOVE the options without reflowing them, and
        # (being a child) it travels with the card when you drag it. It is
        # positioned under the 💡 button in toggle_hint().
        self.hint_label = QLabel(self)
        self.hint_label.setObjectName("hintOverlay")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet(
            "QLabel#hintOverlay { color: #f1c40f; font-style: italic; "
            "background: #2a2f18; border: 1px solid #f1c40f; border-radius: 8px; "
            "padding: 8px 12px; }"
        )
        self.hint_label.hide()

        main_layout.addLayout(content_layout)
        self.content_layout = content_layout

        if self.is_multiple_choice:
            self.setup_multiple_choice_ui(content_layout)
        else:
            self.setup_text_input_ui(content_layout)

        self.check_button = QPushButton("Check Answer")
        self.check_button.clicked.connect(self.check_answer)
        self.check_button.setDefault(True)
        content_layout.addWidget(self.check_button)

        # Streak progress indicator
        self._add_streak_indicator(content_layout)

        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.apply_stylesheet()
        self.setLayout(main_layout)

    def _add_streak_indicator(self, layout):
        """Adds a visual streak progress bar below the check button."""
        from stats_manager import MASTERY_STREAK_THRESHOLD

        current_streak = self.stats_manager.get_streak(self.card, self.study_mode)
        capped_streak = min(current_streak, MASTERY_STREAK_THRESHOLD)

        filled = "⬤" * capped_streak
        empty = "○" * (MASTERY_STREAK_THRESHOLD - capped_streak)
        progress_text = f"Progress: {filled}{empty}"

        self.streak_label = QLabel(progress_text)
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        base_mode = self.study_mode.split('_')[0]
        theme = MODE_THEMES.get(base_mode, MODE_THEMES['translation'])
        self.streak_label.setStyleSheet(
            f"font-size: 11px; color: {theme['badge_color']}; "
            f"background: transparent; border: none; padding: 2px;"
        )
        layout.addWidget(self.streak_label)

    def _create_delete_button(self):
        delete_button = QPushButton("🗑️")
        delete_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        delete_button.setObjectName("deleteButton")
        delete_button.setFixedSize(32, 32)
        delete_button.setToolTip("Удалить эту карточку навсегда")
        delete_button.clicked.connect(self.request_delete)
        return delete_button

    def paintEvent(self, event):
        """Crucial override: forces the custom QFrame to paint its CSS style background."""
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        super().paintEvent(event)

    def apply_stylesheet(self):
        base_mode = self.study_mode.split('_')[0]
        theme = MODE_THEMES.get(base_mode, MODE_THEMES['translation'])
        self.setStyleSheet(f"""
            QFrame#main_widget {{
                background: {theme['gradient']};
                border: 2px solid {theme['border']};
                border-radius: 20px;
                color: #ecf0f1;
            }}

            QLabel#dragBar {{
                background: #222740;
                border: none;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                color: #666;
                font-size: 12px;
                font-weight: normal;
                padding: 4px;
            }}

            QLabel#dragBar:hover {{
                background: #2a3050;
                color: #999;
            }}

            QLabel#questionLabel {{
                font-size: 20px;
                font-weight: bold;
                color: #fff;
                border: none;
                padding: 6px 12px;
                background: transparent;
            }}

            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 12px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }}

            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }}

            QLineEdit {{
                padding: 14px 18px;
                border: 2px solid #2a3050;
                border-radius: 12px;
                font-size: 18px;
                background: #1e2235;
                color: #fff;
            }}

            QLineEdit:focus {{
                border: 2px solid #00d9ff;
                background: #222740;
            }}

            QGroupBox {{
                border: 1px solid #2a2e45;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 5px;
            }}

            QPushButton#deleteButton {{
                background: transparent;
                border: none;
                font-size: 20px;
                color: #c0392b;
                padding: 4px;
            }}

            QPushButton#deleteButton:hover {{
                color: #e74c3c;
            }}

            QPushButton#hintButton {{
                background: transparent;
                border: none;
                font-size: 18px;
                padding: 4px;
            }}

            QPushButton#hintButton:hover {{
                background: rgba(241, 196, 15, 0.15);
                border-radius: 6px;
            }}
        """)

    def setup_text_input_ui(self, layout):
        base_mode = self.study_mode.split('_')[0]
        theme = MODE_THEMES.get(base_mode, MODE_THEMES['translation'])
        self.answer_input = GrabOnClickLineEdit(self._engage_for_typing)
        self.answer_input.setPlaceholderText(theme['placeholder'])
        self.answer_input.returnPressed.connect(self.check_answer)
        layout.addWidget(self.answer_input)
        # NOTE: intentionally NOT calling setFocus() here — that would grab the
        # keyboard the instant the card appears and interrupt whatever you're
        # typing. Focus is given only on an explicit summon (hotkey) via
        # focus_answer_input(), or when you click into the field yourself.

    def setup_multiple_choice_ui(self, layout):
        self.option_widgets = []
        self.button_group = QButtonGroup(self)

        # Generate options based on study mode
        if self.study_mode.startswith('definition'):
            options = self._get_definition_options()
        elif self.study_mode.startswith('synonym'):
            options = self._get_synonym_options()
        else:
            options = self.vocabulary.get_options_for_card(
                self.card, self.answer_lang
            )

        for i, option in enumerate(options):
            widget = PremiumOptionWidget(option, self)
            self.button_group.addButton(widget.radio, i)
            self.option_widgets.append(widget)
            layout.addWidget(widget)

    def _get_definition_options(self):
        """Generates multiple-choice options from definitions of same-category words."""
        correct_def = self.card.get('definition') or ''
        card_category = self.card.get('category')

        if card_category:
            pool = [
                w for w in self.vocabulary.words
                if w.get('category') == card_category
                and w.get('definition')
                and w['english'] != self.card['english']
            ]
        else:
            pool = [
                w for w in self.vocabulary.words
                if w.get('definition')
                and w['english'] != self.card['english']
            ]

        if len(pool) < 3:
            pool = [
                w for w in self.vocabulary.words
                if w.get('definition')
                and w['english'] != self.card['english']
            ]

        distractors = random.sample(pool, min(3, len(pool)))
        options = [correct_def] + [d['definition'] for d in distractors]
        random.shuffle(options)
        return options

    def _get_synonym_options(self):
        """Generates multiple-choice options from synonyms of same-category words."""
        correct_synonyms = self.card.get('synonyms', [])
        correct_answer = correct_synonyms[0] if correct_synonyms else ''
        card_category = self.card.get('category')

        if card_category:
            pool = [
                w for w in self.vocabulary.words
                if w.get('category') == card_category
                and w.get('synonyms')
                and w['english'] != self.card['english']
            ]
        else:
            pool = [
                w for w in self.vocabulary.words
                if w.get('synonyms')
                and w['english'] != self.card['english']
            ]

        if len(pool) < 3:
            pool = [
                w for w in self.vocabulary.words
                if w.get('synonyms')
                and w['english'] != self.card['english']
            ]

        distractors = random.sample(pool, min(3, len(pool)))
        options = [correct_answer] + [d['synonyms'][0] for d in distractors]
        random.shuffle(options)
        return options

    def set_question(self):
        has_hint = bool((self.card.get('hint') or '').strip())
        self.hint_button.setVisible(has_hint)
        self.hint_label.hide()  # collapse any previously opened hint on a new card
        print(f"[HINT] set_question card={self.card.get('english')!r} has_hint={has_hint} -> 💡 button {'shown' if has_hint else 'hidden'}")
        word = self.card.get('english', 'No text')
        # For verbs, show the word together with its pattern continuation
        # (e.g. "avoid doing sth", "refuse to do sth") whenever the English word
        # is the prompt. This only changes what's displayed — the answer asked
        # for is still the meaning.
        english_prompt = self.card.get('grammar_pattern') or word

        if self.study_mode.startswith('definition'):
            self.question_label.setText(
                f"Define: <b>{english_prompt}</b>"
            )
        elif self.study_mode.startswith('synonym'):
            self.question_label.setText(
                f"Synonym for: <b>{english_prompt}</b>"
            )
        elif self.is_transition_card:
            question_text = english_prompt if self.question_lang == 'english' else self.card.get(self.question_lang, word)
            self.question_label.setText(
                f"Transition: <b>{question_text}</b>"
            )
        else:
            question_text = english_prompt if self.question_lang == 'english' else self.card.get(self.question_lang, word)
            self.question_label.setText(
                f"Translate: <b>{question_text}</b>"
            )

    def check_answer(self):
        user_answer = ""

        if self.is_multiple_choice:
            for widget in self.option_widgets:
                if widget.isChecked():
                    user_answer = widget.text()
                    break
        else:
            user_answer = self.answer_input.text()

        # Disable inputs
        self.check_button.setEnabled(False)
        if not self.is_multiple_choice:
            self.answer_input.setEnabled(False)
        else:
            for widget in self.option_widgets:
                widget.setEnabled(False)

        # --- Check correctness based on study mode ---
        if self.study_mode.startswith('definition'):
            is_correct = self._check_definition_answer(user_answer)
            correct_display = self.card.get('definition') or ''
        elif self.study_mode.startswith('synonym'):
            is_correct = self._check_synonym_answer(user_answer)
            synonyms = self.card.get('synonyms', [])
            correct_display = ' / '.join(synonyms)
        else:
            # Translation / grammar — legacy behavior
            correct_answer_string = self.card[self.answer_lang]
            possible_answers = [ans.strip() for ans in correct_answer_string.split('/')]
            if self.is_multiple_choice:
                is_correct = self._normalize_answer(user_answer) in [
                    self._normalize_answer(ans) for ans in possible_answers
                ]
            else:
                is_correct = any(
                    self.similarity_checker.are_similar(user_answer, p_ans)
                    for p_ans in possible_answers
                )
            correct_display = correct_answer_string

        # Record answer with mode
        self.stats_manager.record_answer(self.card, is_correct, self.study_mode)

        # Visual feedback for multiple choice
        if self.is_multiple_choice:
            for widget in self.option_widgets:
                widget_text = self._normalize_answer(widget.text())
                if self.study_mode.startswith('definition'):
                    is_this_correct = widget_text == self._normalize_answer(
                        self.card.get('definition') or ''
                    )
                elif self.study_mode.startswith('synonym'):
                    synonyms = self.card.get('synonyms', [])
                    is_this_correct = widget_text in [
                        self._normalize_answer(s) for s in synonyms
                    ]
                else:
                    correct_answer_string = self.card[self.answer_lang]
                    possible = [ans.strip() for ans in correct_answer_string.split('/')]
                    is_this_correct = widget_text in [
                        self._normalize_answer(ans) for ans in possible
                    ]

                if is_this_correct:
                    widget.set_result_style(is_correct_option=True)
                elif widget.isChecked() and not is_correct:
                    widget.set_result_style(
                        is_correct_option=False, was_selected_wrong=True
                    )

        if is_correct:
            self.setStyleSheet(
                self.styleSheet()
                + "QFrame#main_widget { border: 2px solid #2ecc71; }"
            )
            self.check_button.setText(correct_display)
            self.check_button.setStyleSheet("background-color: #2ecc71;")
        else:
            self.setStyleSheet(
                self.styleSheet()
                + "QFrame#main_widget { border: 2px solid #e74c3c; }"
            )
            self.check_button.setText(correct_display)
            self.check_button.setStyleSheet("background-color: #e74c3c;")

        QTimer.singleShot(4000, self.close)

    def _check_definition_answer(self, user_answer):
        """Checks if user's answer matches the definition using similarity."""
        correct_def = self.card.get('definition') or ''
        if self.is_multiple_choice:
            return self._normalize_answer(user_answer) == self._normalize_answer(correct_def)
        return self.similarity_checker.are_similar(user_answer, correct_def)

    def _check_synonym_answer(self, user_answer):
        """Checks if user's answer matches any synonym (1-to-any logic)."""
        synonyms = self.card.get('synonyms', [])
        if self.is_multiple_choice:
            return self._normalize_answer(user_answer) in [
                self._normalize_answer(s) for s in synonyms
            ]
        return any(
            self.similarity_checker.are_similar(user_answer, syn)
            for syn in synonyms
        )

    def toggle_hint(self, link=None):
        hint_text = (self.card.get('hint') or '').strip()
        print(f"[HINT] toggle_hint called; card={self.card.get('english')!r} hint={hint_text!r}")
        if not hint_text:
            print("[HINT] no hint text for this card -> nothing to show")
            return

        if self.hint_label.isVisible():
            self.hint_label.hide()
            print("[HINT] hidden")
            return

        self.hint_label.setText(f"💡 {hint_text}")
        # Full-width banner pinned just under the title row, so it reads as a
        # header hint instead of a small box floating over the answer options.
        # It's not in a layout (overlays, doesn't reflow) and is a child of the
        # window (travels with the card when dragged).
        margin = 12
        self.hint_label.setFixedWidth(self.width() - 2 * margin)
        self.hint_label.adjustSize()
        # Pin to the very top, over the "drag me" bar — where the user marked it.
        y = 4
        self.hint_label.move(margin, y)
        self.hint_label.raise_()
        self.hint_label.show()
        print(f"[HINT] shown overlay at ({margin},{y}) "
              f"size={self.hint_label.width()}x{self.hint_label.height()}")

    def _promote_to_managed(self):
        """Turn a passive override-redirect overlay into a normal managed window.

        Unmanaged (override-redirect) windows can't hold keyboard focus through
        global shortcuts — win+space makes the WM push focus to another window.
        Once the user engages the card to type, drop the override-redirect flag
        so it becomes a regular focusable window that keeps focus like any app.
        """
        if not self._is_bypass:
            return
        self._is_bypass = False
        pos = self.pos()
        # NOTE: deliberately NO WindowStaysOnTopHint here. A managed always-on-top
        # window steals focus on win+space in GNOME/XWayland (the very bug we're
        # fighting). As a plain managed window it stays on top while focused (you
        # are answering it) and simply drops behind — without grabbing focus —
        # once you click away.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # setWindowFlags() unmaps the window; restore position and re-show.
        self.move(pos)
        self.show()
        self.activateWindow()
        self.raise_()

    def _engage_for_typing(self):
        """User clicked the answer field — make the card typable.

        For a passive X11 overlay this promotes it to a managed window first
        (deferred so the current click finishes), then focuses the field.
        """
        if self._is_bypass:
            QTimer.singleShot(0, self._do_engage)
        else:
            self.focus_answer_input()

    def _do_engage(self):
        self._promote_to_managed()
        self.activateWindow()
        self.focus_answer_input()

    def focus_answer_input(self):
        """Gives keyboard focus to the answer field (text modes only)."""
        if not self.is_multiple_choice and hasattr(self, 'answer_input'):
            self.answer_input.setFocus()

    def summon_focus(self):
        """Explicit trigger (hotkey / menu): bring to front and give it the keyboard.

        Promotes a passive overlay to a managed window if needed, then activates
        and focuses the answer field so you can type immediately — and, being
        managed, it holds focus through win+space.
        """
        self._promote_to_managed()
        self.activateWindow()
        self.raise_()
        self.focus_answer_input()

    def request_delete(self):
        print(f"Delete button clicked for: {self.card['english']}")
        self.card_delete_requested.emit(self.card)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.check_button.isEnabled():
                self.check_button.click()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        elif self.is_multiple_choice and event.key() in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4):
            index = event.key() - Qt.Key.Key_1
            if index < len(self.option_widgets):
                self.option_widgets[index].setChecked(True)
                self.check_answer()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._x11_overlay:
                # Override-redirect windows are unmanaged, so startSystemMove()
                # (which asks the WM to move us) has no effect. Drag manually —
                # move() works fine for unmanaged X11 windows.
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            else:
                # Elsewhere prefer the compositor-driven move: on native Wayland a
                # client may NOT reposition its own top-level, so manual move() is
                # ignored there and startSystemMove() hands the drag to the
                # compositor. Fall back to manual if unsupported.
                window_handle = self.windowHandle()
                if window_handle is not None and window_handle.startSystemMove():
                    self._drag_pos = None
                else:
                    self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        # Only used on the manual-drag fallback path; when startSystemMove()
        # succeeded, _drag_pos is None and the compositor owns the drag.
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
