import random
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QRadioButton, QStyle, QStyleOption, QButtonGroup, QLayout,
    QSizePolicy, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QRectF, QSize
from PySide6.QtGui import QPainter, QPixmap, QPen, QColor, QPainterPath, QIcon

from .i18n import tr


def make_speaker_icon(color="#00d9ff", size=22):
    """Draw a crisp speaker (🔊) icon with QPainter.

    Emoji glyphs don't render reliably inside styled QPushButtons on every
    system (the 🔊 came out invisible), so we draw a real vector icon that is
    font-independent and always shows.
    """
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    c = QColor(color)
    s = float(size)
    # Speaker body: a small box + cone (one filled shape).
    p.setPen(QPen(c, 1.6))
    p.setBrush(c)
    path = QPainterPath()
    path.addRect(QRectF(s * 0.14, s * 0.40, s * 0.12, s * 0.20))
    path.moveTo(s * 0.26, s * 0.40)
    path.lineTo(s * 0.46, s * 0.24)
    path.lineTo(s * 0.46, s * 0.76)
    path.lineTo(s * 0.26, s * 0.60)
    path.closeSubpath()
    p.drawPath(path)
    # Two sound-wave arcs (outlined only).
    p.setBrush(Qt.GlobalColor.transparent)
    p.setPen(QPen(c, 1.8))
    p.drawArc(QRectF(s * 0.50, s * 0.32, s * 0.20, s * 0.36), -55 * 16, 110 * 16)
    p.drawArc(QRectF(s * 0.56, s * 0.22, s * 0.30, s * 0.56), -55 * 16, 110 * 16)
    p.end()
    return QIcon(pm)


# Key codes captured ONCE at import as plain ints. Accessing ``Qt.Key.*`` inside
# the keyPressEvent override crashed for some users with
# "type object 'PySide6.QtCore.Qt' has no attribute 'Key'"; plain ints compared
# against event.key() are immune to that runtime quirk.
try:
    _KEY_RETURN = int(Qt.Key.Key_Return)
    _KEY_ENTER = int(Qt.Key.Key_Enter)
    _KEY_ESCAPE = int(Qt.Key.Key_Escape)
    _KEY_1 = int(Qt.Key.Key_1)
    _KEY_4 = int(Qt.Key.Key_4)
    _KEY_M = int(Qt.Key.Key_M)
    _KEY_L = int(Qt.Key.Key_L)
    _KEY_D = int(Qt.Key.Key_D)
    _KEY_S = int(Qt.Key.Key_S)
    _KEY_DELETE = int(Qt.Key.Key_Delete)
except Exception:  # extremely defensive — hard-coded Qt key codes
    _KEY_RETURN, _KEY_ENTER, _KEY_ESCAPE = 0x01000004, 0x01000005, 0x01000000
    _KEY_1, _KEY_4 = 0x31, 0x34
    _KEY_M, _KEY_L, _KEY_D, _KEY_S = 0x4D, 0x4C, 0x44, 0x53
    _KEY_DELETE = 0x01000007


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

# Key-cap ("kbd") badge — styled like a raised physical key so a keyboard shortcut
# reads as discoverable secondary metadata next to the control it triggers.
KBD_CAP_QSS = (
    "QLabel#kbdCap {"
    " background: rgba(42,46,69,0.6); color: #7f8aa3;"
    " border: 1px solid #343954; border-radius: 4px;"
    " font-size: 10px; font-weight: 600; }"
)

# Tiny corner variant, overlaid on the top-right edge of a 30px icon button.
KBD_CORNER_QSS = (
    "QLabel#kbdCorner {"
    " background: rgba(58,63,90,0.75); color: #aab3cc;"
    " border: 1px solid #454b6b; border-radius: 3px;"
    " font-size: 8px; font-weight: 600; }"
)


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
    clicked = Signal()

    def __init__(self, text, parent=None, key_hint=None):
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
        # Reserve the RIGHT height for a wrapped (multi-line) answer. By default a
        # word-wrapped QLabel's size policy does NOT advertise height-for-width, so
        # the row is sized for a single line and a long answer gets clipped at the
        # top (the bug on long options like "Boshqa mamlakatga ko'chib ketmoq").
        # Enabling it — on the label AND this frame, so it propagates through the
        # nested layouts up to the card's SetFixedSize pass — makes the row grow to
        # fit every line.
        _lp = self.label.sizePolicy()
        _lp.setHeightForWidth(True)
        self.label.setSizePolicy(_lp)
        layout.addWidget(self.label, 1)

        # Trailing key-cap badge (1-4) so the keyboard shortcut is discoverable
        # right on the option — reads as secondary metadata after the answer text.
        self.key_cap = None
        if key_hint:
            self.key_cap = QLabel(str(key_hint))
            self.key_cap.setObjectName("kbdCap")
            self.key_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.key_cap.setFixedSize(18, 18)
            self.key_cap.setStyleSheet(KBD_CAP_QSS)
            layout.addWidget(self.key_cap)

        _fp = self.sizePolicy()
        _fp.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        _fp.setHeightForWidth(True)
        self.setSizePolicy(_fp)

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


# Presentation rules per category. To change how a category is asked — its
# question direction or its prompt label — edit this table; the widget below
# stays generic and never branches on a category name.
#   mode:            'exact' or 'prefix' match against the card's category
#   fixed_direction: always ask prompt-language -> answer-language (never reversed)
#   prompt:          i18n key for the question label
CATEGORY_RULES = (
    {'match': 'SAT Transitions & Grammar', 'mode': 'exact',  'fixed_direction': True, 'prompt': 'prompt_transition'},
    {'match': 'Irregular Verbs',           'mode': 'prefix', 'fixed_direction': True, 'prompt': 'prompt_verb_forms'},
)


def category_rule(category):
    """Return the presentation rule for a card's category, or None for default behaviour."""
    category = category or ''
    for rule in CATEGORY_RULES:
        if rule['mode'] == 'exact' and category == rule['match']:
            return rule
        if rule['mode'] == 'prefix' and category.startswith(rule['match']):
            return rule
    return None


class FlashcardWidget(QFrame):
    """A widget to display a flashcard question and handle user input."""
    closed = Signal()
    card_delete_requested = Signal(dict)
    menu_requested = Signal()  # ⚙ on the card → app pops up the menu (Manage, etc.)
    home_requested = Signal()  # 🏠 on the card → app returns straight to the main menu

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
            from PySide6.QtWidgets import QApplication as _QA
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

        # Presentation rule for this card's category (fixed direction + custom
        # prompt label). None => default translation behaviour.
        self.card_rule = category_rule(self.card.get('category'))

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
            if self.card_rule and self.card_rule['fixed_direction']:
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

        # Top bar as ONE row: 🏠 home (left) · draggable title (centre, stretches)
        # · 💡/🗑 card actions pinned to the right — all on the same line. The 🏠
        # button returns to the main menu in one click (the old ⚙ menu's other
        # actions — Manage, shuffle, etc. — remain in the system-tray menu).
        self.menu_button = QPushButton("🏠")
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.menu_button.setFixedSize(30, 30)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_button.setToolTip(tr('home_tooltip'))
        self.menu_button.clicked.connect(self.home_requested.emit)

        self.hint_button = QPushButton("💡", self)
        self.hint_button.setObjectName("hintButton")
        self.hint_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.hint_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hint_button.setFixedSize(30, 30)
        self.hint_button.setToolTip(tr('hint_tooltip'))
        self.hint_button.clicked.connect(self.toggle_hint)
        self.hint_button.hide()

        self.delete_button = QPushButton("🗑️", self)
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.delete_button.setFixedSize(30, 30)
        self.delete_button.setToolTip(tr('delete_card_tooltip'))
        self.delete_button.clicked.connect(self.request_delete)

        # 🔊 Pronounce the English word (cached Google TTS, offline fallback).
        # Uses a hand-drawn vector icon, not an emoji glyph (the 🔊 emoji rendered
        # invisible inside the styled button on the user's system).
        self.speak_button = QPushButton(self)
        self.speak_button.setObjectName("speakButton")
        self.speak_button.setIcon(make_speaker_icon("#00d9ff", 22))
        self.speak_button.setIconSize(QSize(22, 22))
        self.speak_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.speak_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speak_button.setFixedSize(30, 30)
        self.speak_button.setToolTip("Произношение / Pronounce (S)")
        self.speak_button.setStyleSheet(
            "QPushButton#speakButton { background: transparent; border: none; }"
            "QPushButton#speakButton:hover { background: rgba(0,217,255,0.22); border-radius: 6px; }"
        )
        self.speak_button.clicked.connect(self._pronounce_word)

        # Tiny corner key-cap badges sitting on the top-right edge of each icon, so
        # the shortcut reads as attached without covering the glyph. Parented to the
        # button, so they move/appear/hide with it automatically.
        self._corner_badge(self.menu_button, "M")    # 🏠 → main menu
        self._corner_badge(self.hint_button, "L")    # 💡 → hint (L = lampa)
        self._corner_badge(self.delete_button, "D")  # 🗑 → delete
        self._corner_badge(self.speak_button, "S")   # 🔊 → pronounce

        self.drag_bar = QLabel(tr('drag_me'))
        self.drag_bar.setObjectName("dragBar")
        self.drag_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_bar.setCursor(Qt.CursorShape.SizeAllCursor)

        # Top bar strip: ONLY the ⚙ app menu (left) + the draggable title (centre).
        # The card-action icons 💡/🗑 live below, in the card body (see actions_row).
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(34)
        drag_row = QHBoxLayout(top_bar)
        drag_row.setContentsMargins(8, 0, 8, 0)
        drag_row.setSpacing(4)
        drag_row.addWidget(self.menu_button)
        drag_row.addWidget(self.drag_bar, 1)
        # Right-side spacer the same width as ⚙ so the title stays optically centred.
        drag_row.addSpacing(30)
        main_layout.addWidget(top_bar)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 12)
        content_layout.setSpacing(10)

        # Mode badge is not added to layout as color coding is sufficient
        base_mode = self.study_mode.split('_')[0]
        theme = MODE_THEMES.get(base_mode, MODE_THEMES['translation'])

        # Question — centred and full width. 💡/🗑 float in the top-right corner of
        # the card body (positioned in resizeEvent), so they take NO layout row and
        # never push the question down or shove it aside.
        self.question_label = QLabel()
        self.question_label.setObjectName("questionLabel")
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.question_label)

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

        self.check_button = QPushButton(tr('check_answer'))
        self.check_button.clicked.connect(self.check_answer)
        self.check_button.setDefault(True)
        content_layout.addWidget(self.check_button)
        # "Enter" key-cap on the right edge of the check button (child → moves with it,
        # clicks pass through); positioned in resizeEvent, hidden once answered.
        self.enter_badge = QLabel("Enter", self.check_button)
        self.enter_badge.setObjectName("kbdCap")
        self.enter_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enter_badge.setStyleSheet(KBD_CAP_QSS)
        self.enter_badge.setFixedSize(38, 16)
        self.enter_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Streak progress indicator
        self._add_streak_indicator(content_layout)

        # Width strut — ONLY for multiple-choice cards. SetFixedSize shrinks the
        # card to its word-wrapped content (as narrow as ~220px), which made long
        # ANSWER OPTIONS (e.g. "Boshqa mamlakatga ko'chib ketmoq") wrap and clip,
        # while setMinimumWidth() is ignored under SetFixedSize. A zero-height,
        # fixed-width invisible strut pins MC cards to a readable width so options
        # fit on one line. Text-input cards have no such content and stay compact.
        if self.is_multiple_choice:
            width_strut = QWidget()
            width_strut.setFixedHeight(0)
            width_strut.setMinimumWidth(420)
            content_layout.addWidget(width_strut)

        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.apply_stylesheet()
        self.setLayout(main_layout)

    def _add_streak_indicator(self, layout):
        """Adds a visual streak progress bar below the check button."""
        from .stats_manager import MASTERY_STREAK_THRESHOLD

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
        delete_button.setToolTip(tr('delete_card_tooltip'))
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

            QFrame#topBar {{
                background: #222740;
                border: none;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }}
            QLabel#dragBar {{
                background: transparent;
                border: none;
                color: #666;
                font-size: 12px;
                font-weight: normal;
                padding: 0;
            }}
            QLabel#dragBar:hover {{
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
                padding: 0;
            }}

            QPushButton#deleteButton:hover {{
                color: #e74c3c;
            }}

            QPushButton#hintButton {{
                background: transparent;
                border: none;
                font-size: 20px;
                padding: 0;
            }}

            QPushButton#hintButton:hover {{
                background: rgba(241, 196, 15, 0.15);
                border-radius: 6px;
            }}

            QPushButton#menuButton {{
                background: transparent;
                border: none;
                font-size: 14px;
                color: #8a97ac;
                padding: 0;
            }}

            QPushButton#menuButton:hover {{
                background: rgba(159, 176, 195, 0.18);
                border-radius: 6px;
                color: #cfd6e6;
            }}
        """)

    def setup_text_input_ui(self, layout):
        base_mode = self.study_mode.split('_')[0]
        theme = MODE_THEMES.get(base_mode, MODE_THEMES['translation'])
        self.answer_input = GrabOnClickLineEdit(self._engage_for_typing)
        _ph = {'translation': tr('ph_translation'),
               'definition': tr('ph_definition'),
               'synonym': tr('ph_synonym')}.get(base_mode, tr('ph_translation'))
        self.answer_input.setPlaceholderText(_ph)
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
            # Show a 1-9 key-cap on the first nine options (keys 1-4 are wired).
            key_hint = str(i + 1) if i < 9 else None
            widget = PremiumOptionWidget(option, self, key_hint=key_hint)
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
        self.hint_button.setVisible(has_hint)  # its corner badge is a child → follows it
        self.hint_label.hide()  # collapse any previously opened hint on a new card
        print(f"[HINT] set_question card={self.card.get('english')!r} has_hint={has_hint} -> 💡 button {'shown' if has_hint else 'hidden'}")
        word = self.card.get('english', 'No text')
        # For verbs, show the word together with its pattern continuation
        # (e.g. "avoid doing sth", "refuse to do sth") whenever the English word
        # is the prompt. This only changes what's displayed — the answer asked
        # for is still the meaning.
        english_prompt = self.card.get('grammar_pattern') or word

        # Word count of ALL selected topics, shown in the top drag bar (not the title).
        try:
            n = self.vocabulary.active_word_count()
            if n and hasattr(self, 'drag_bar'):
                self.drag_bar.setText(f"{tr('drag_me')}   ·   {tr('words_n', n=n)}")
        except Exception:
            pass

        if self.study_mode.startswith('definition'):
            self.question_label.setText(
                f"{tr('prompt_define')} <b>{english_prompt}</b>"
            )
        elif self.study_mode.startswith('synonym'):
            self.question_label.setText(
                f"{tr('prompt_synonym')} <b>{english_prompt}</b>"
            )
        else:
            question_text = english_prompt if self.question_lang == 'english' else self.card.get(self.question_lang, word)
            prompt_key = self.card_rule['prompt'] if self.card_rule else 'prompt_translate'
            self.question_label.setText(
                f"{tr(prompt_key)} <b>{question_text}</b>"
            )

    def _translation_answers(self):
        """Accepted answers for a typed translation: the full stored string PLUS each
        '/'-separated alternative. Keeping the full string is what lets words with a
        literal slash (e.g. 'On/off button') still be accepted.

        It also accepts the answer from ANY other card of the same English word — the
        same word can live in several topics with different translations, so all of
        them count as correct instead of only the shown card's."""
        out, seen = [], set()

        def add(s):
            for a in [s] + (s.split('/') if s else []):
                a = a.strip()
                if a and a.lower() not in seen:
                    seen.add(a.lower())
                    out.append(a)

        add(self.card.get(self.answer_lang) or '')
        eng = (self.card.get('english') or '').strip().lower()
        if eng and getattr(self, 'vocabulary', None):
            for w in self.vocabulary.words:
                if (w.get('english') or '').strip().lower() == eng:
                    add(w.get(self.answer_lang) or '')
        return out

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
        if hasattr(self, 'enter_badge'):
            self.enter_badge.hide()  # button now shows the answer; hint no longer needed
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
            # Translation / grammar.
            correct_answer_string = self.card[self.answer_lang]
            if self.is_multiple_choice:
                # Options are exact word strings — match the FULL answer (never split on
                # '/', which would wreck words like "On/off button"). Accept any accepted
                # translation, so a valid variant from the same word in another topic
                # also counts.
                accepted = {self._normalize_answer(a) for a in self._translation_answers()}
                is_correct = self._normalize_answer(user_answer) in accepted
            else:
                # Typed answer: accept the full string or any '/'-separated alternative.
                is_correct = any(
                    self.similarity_checker.are_similar(user_answer, p_ans)
                    for p_ans in self._translation_answers()
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
                    # Any accepted translation of this word (incl. other topics' variants).
                    is_this_correct = widget_text in {
                        self._normalize_answer(a) for a in self._translation_answers()
                    }

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

        # Auto-reveal the example (hint) a beat after the answer, while the card still
        # lingers — seeing the word in context right after a retrieval attempt helps it
        # stick (retrieval + feedback / elaborative encoding). Skipped if the learner
        # already opened the hint or there is none.
        if (self.card.get('hint') or '').strip():
            QTimer.singleShot(800, self._auto_show_hint)

        QTimer.singleShot(4000, self.close)

    def _auto_show_hint(self):
        try:
            if (self.isVisible() and self.hint_button.isVisible()
                    and not self.hint_label.isVisible()):
                self.toggle_hint()
        except Exception:
            pass

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Float 💡/🗑 in the top-right corner of the card body, just under the 34px
        # top bar. As overlay children they take NO layout row, so the question keeps
        # its natural height and is never pushed down or shoved aside.
        if hasattr(self, 'delete_button') and hasattr(self, 'hint_button'):
            m, top, gap = 10, 40, 6
            dw = self.delete_button.width()
            sw = self.speak_button.width() if hasattr(self, 'speak_button') else 0
            hw = self.hint_button.width()
            # Fixed slots, positioned UNCONDITIONALLY (isVisible() is unreliable mid
            # resize, which stranded the hint at 0,0). Order right-to-left:
            # [💡 hint] [🔊 speak] [🗑 delete]. The hint just stays hidden when the
            # card has no hint; its slot is reserved so nothing else shifts.
            self.delete_button.move(self.width() - dw - m, top)
            self.delete_button.raise_()
            if hasattr(self, 'speak_button'):
                self.speak_button.move(self.width() - dw - sw - m - gap, top)
                self.speak_button.raise_()
            self.hint_button.move(self.width() - dw - sw - hw - m - gap * 2, top)
            self.hint_button.raise_()
        if hasattr(self, 'enter_badge') and hasattr(self, 'check_button') and not self.enter_badge.isHidden():
            b, eb = self.check_button, self.enter_badge
            if b.width() > 60:
                eb.move(b.width() - eb.width() - 6, 4)  # top-right corner, like the icons
                eb.raise_()
        # The card grows when the correct answer is revealed (a long option widens
        # it). Positioning happens once at show time, so re-clamp on every resize to
        # keep the card fully on-screen — it must never run off the right/bottom edge.
        if not self.isVisible():
            return
        try:
            from PySide6.QtGui import QGuiApplication
            g = self.frameGeometry()
            scr = QGuiApplication.screenAt(g.center()) or QGuiApplication.primaryScreen()
            wa = scr.availableGeometry()
            pad = 20
            # Clamp onto the card's OWN screen. If it's wider/taller than the screen
            # (high-DPI scaling can inflate it), pin the top-left inside the work area
            # so the start stays visible instead of the right edge running off.
            max_x = wa.right() - g.width() - pad
            max_y = wa.bottom() - g.height() - pad
            x = min(max_x, max(wa.left() + pad, self.x())) if max_x >= wa.left() + pad else wa.left() + pad
            y = min(max_y, max(wa.top() + pad, self.y())) if max_y >= wa.top() + pad else wa.top() + pad
            if x != self.x() or y != self.y():
                self.move(int(x), int(y))
        except Exception:
            pass

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

    def _corner_badge(self, button, text):
        """Overlay a tiny key-cap on the top-right edge of an icon button (child of the
        button, so it moves/shows/hides with it and passes clicks through)."""
        badge = QLabel(text, button)
        badge.setObjectName("kbdCorner")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(KBD_CORNER_QSS)
        w = 12 if len(text) == 1 else 16
        badge.setFixedSize(w, 10)
        badge.move(button.width() - w + 3, -2)  # top-right, slightly over the edge
        badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        badge.raise_()
        badge.show()
        return badge

    def _pronounce_word(self):
        """Say the card's English word out loud (🔊 button)."""
        try:
            from .tts import pronounce
            pronounce(self.card.get('english', ''))
        except Exception as e:
            print(f"[TTS] pronounce failed: {e}")

    def keyPressEvent(self, event):
        # Pre-captured int key codes (see top of file) + a try/except so a key press
        # can never crash the card. animateClick() gives visible press feedback.
        try:
            key = int(event.key())
            if key in (_KEY_RETURN, _KEY_ENTER):
                if self.check_button.isEnabled():
                    self.check_button.animateClick()
            elif key == _KEY_ESCAPE:
                self.close()
            elif key == _KEY_M:
                self.menu_button.animateClick()   # 🏠 main menu
            elif key == _KEY_L and self.hint_button.isVisible():
                self.hint_button.animateClick()
            elif key == _KEY_S:
                self.speak_button.animateClick()  # 🔊 pronounce
            elif key in (_KEY_D, _KEY_DELETE) and self.delete_button.isEnabled():
                self.delete_button.animateClick()
            elif self.is_multiple_choice and _KEY_1 <= key <= _KEY_4:
                index = key - _KEY_1
                if index < len(self.option_widgets):
                    self.option_widgets[index].setChecked(True)
                    self.check_answer()
        except Exception as e:
            print(f"[keyPressEvent] ignored error: {e}")

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
