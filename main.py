import base64
import logging
import os
import signal
import sys
from datetime import datetime

from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from app_paths import get_data_dir


def setup_logging():
    """Sets up file logging in the data directory next to the exe."""
    log_dir = get_data_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'app.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Redirect print statements to logger
    sys.stdout = LoggerWriter(logging.getLogger(), logging.INFO)
    sys.stderr = LoggerWriter(logging.getLogger(), logging.ERROR)

    logging.info("=" * 60)
    logging.info(f"Smart Flashcards started at {datetime.now()}")
    logging.info(f"Data directory: {log_dir}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    logging.info(f"Python: {sys.version}")
    logging.info(f"OS: {os.name} / {sys.platform}")
    logging.info("=" * 60)


class LoggerWriter:
    """Redirects print() output to both log file and console."""

    def __init__(self, logger, level):
        self._logger = logger
        self._level = level
        self._original = sys.__stdout__ if level == logging.INFO else sys.__stderr__

    def write(self, message):
        if message and message.strip():
            self._logger.log(self._level, message.strip())

    def flush(self):
        if self._original:
            self._original.flush()


from vocabulary import Vocabulary
from flashcard_widget import FlashcardWidget
from stats_manager import StatsManager
from config_manager import ConfigManager
from similarity_checker import SimilarityChecker
from management_window import ManagementWindow
from startup_dialog import StartupDialog
from icon import icon_b64
import profile_manager

# Global hotkey support
try:
    from pynput import keyboard

    HOTKEY_AVAILABLE = True
except ImportError:
    HOTKEY_AVAILABLE = False
    print("Warning: pynput not installed. Global hotkey disabled.")

# Kernel-level (evdev) hotkey backend — the only reliable way to get GLOBAL
# hotkeys under Wayland, where pynput/X11 can't see keys sent to other windows.
try:
    from evdev_hotkey import EvdevHotkeyListener, EVDEV_AVAILABLE
except ImportError:
    EVDEV_AVAILABLE = False
    EvdevHotkeyListener = None

APP_NAME = "Smart Flashcards"


class HotkeySignal(QObject):
    """Signal emitter for global hotkey."""
    triggered = pyqtSignal()


class FlashcardApp:
    """Main application class."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")  # Required: WindowsVista style breaks border-radius rendering
        self.app.setQuitOnLastWindowClosed(False)

        # Load vocabulary first (needed for startup dialog)
        self.vocabulary = Vocabulary()

        # Show startup dialog for profile selection
        startup = StartupDialog(vocabulary=self.vocabulary)
        if startup.exec() != startup.DialogCode.Accepted:
            sys.exit(0)

        username, selected_topics, study_mode = startup.get_result()
        self.current_user = username
        print(f"User profile: {username}")

        # Initialize managers with user profile path
        user_profile_path = profile_manager.get_profile_path(username)
        self.config_manager = ConfigManager(config_path=user_profile_path / 'config.json')
        self.stats_manager = StatsManager(stats_path=user_profile_path / 'stats.json')
        self.similarity_checker = SimilarityChecker()

        # Save selected study mode
        if study_mode:
            self.config_manager.study_mode = study_mode

        # Set active topics from startup if provided
        if selected_topics:
            self.config_manager.active_topics = selected_topics

        # Create initial deck with topic filtering
        active_topics = self.config_manager.active_topics
        self.vocabulary.shuffle_deck(self.stats_manager, active_topics if active_topics else None)

        self.flashcard_widget = None
        self.management_window = None
        self.next_question_is_mc = True

        # Setup System Tray
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(icon_b64))
        icon = QIcon(pixmap)
        self.tray_icon = QSystemTrayIcon(icon, self.app)
        hotkey = self.config_manager.hotkey
        self.tray_icon.setToolTip(f"{APP_NAME} — {username} (Press {hotkey})")

        # Actions
        self.user_action = QAction(f"👤 {username}")
        self.user_action.setEnabled(False)

        self.manage_action = QAction("📚 Управление...")
        self.manage_action.triggered.connect(self.show_management_window)

        self.shuffle_action = QAction("🔀 Перемешать колоду")
        self.shuffle_action.triggered.connect(self.shuffle_deck)

        self.next_card_action = QAction(f"▶️ Следующая карточка ({hotkey})")
        self.next_card_action.triggered.connect(self.force_show_flashcard)

        self.switch_user_action = QAction("🔄 Сменить пользователя")
        self.switch_user_action.triggered.connect(self.switch_user)

        self.quit_action = QAction("❌ Выход")
        self.quit_action.triggered.connect(self.quit_app)

        # Menu
        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.user_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.manage_action)
        self.tray_menu.addAction(self.shuffle_action)
        self.tray_menu.addAction(self.next_card_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.switch_user_action)
        self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_flashcard)
        self.update_timer_interval()

        # Global hotkey
        self.hotkey_signal = HotkeySignal()
        self.hotkey_signal.triggered.connect(self.force_show_flashcard)
        self.setup_global_hotkey()

        # Show first card
        QTimer.singleShot(0, self.show_flashcard)

    def setup_global_hotkey(self):
        """Sets up the global hotkey listener.

        On Linux we prefer the evdev (kernel-level) backend because it is the
        only one that works globally under Wayland. It also works on X11. We
        fall back to pynput if evdev is unavailable (e.g. no /dev/input access,
        or a non-Linux OS such as Windows, where pynput works natively).
        """
        import platform

        hotkey_config = self.config_manager.hotkey.lower()

        if platform.system() == "Linux" and EVDEV_AVAILABLE and EvdevHotkeyListener is not None:
            listener = EvdevHotkeyListener(
                hotkey_config,
                self.hotkey_signal.triggered.emit,
            )
            if listener.start():
                self.evdev_listener = listener
                print(f"Global hotkey '{hotkey_config}' activated via evdev "
                      f"(kernel-level, works on Wayland & X11).")
                return
            print("evdev hotkey backend unavailable (no /dev/input access?). "
                  "Falling back to pynput. Tip: add yourself to the 'input' "
                  "group with: sudo usermod -aG input $USER  (then re-login).")

        self._setup_pynput_hotkey()

    def _setup_pynput_hotkey(self):
        """Sets up global hotkey listener using pynput with L/R modifier support."""
        if not HOTKEY_AVAILABLE:
            return

        hotkey_config = self.config_manager.hotkey.lower()

        # L/R specific modifiers
        LR_MODIFIERS = {
            'ctrl_l', 'ctrl_r', 'alt_l', 'alt_r',
            'shift_l', 'shift_r', 'win_l', 'win_r'
        }
        # Generic modifiers
        GENERIC_MODIFIERS = {'ctrl', 'alt', 'shift', 'win'}

        # Parse hotkey (e.g., "ctrl+alt+k", "f7", "ctrl_l", "shift_r")
        parts = hotkey_config.split('+')
        required_modifiers = set()
        target_key = None
        is_single_modifier = False
        is_lr_modifier = False

        # Check if hotkey is a single L/R or generic modifier
        if len(parts) == 1:
            single_part = parts[0].strip()
            if single_part in LR_MODIFIERS:
                is_single_modifier = True
                is_lr_modifier = True
                target_key = single_part
            elif single_part in GENERIC_MODIFIERS:
                is_single_modifier = True
                target_key = single_part
            else:
                target_key = single_part
        else:
            for part in parts:
                part = part.strip()
                if part == 'ctrl':
                    required_modifiers.add('ctrl')
                elif part == 'alt':
                    required_modifiers.add('alt')
                elif part == 'shift':
                    required_modifiers.add('shift')
                else:
                    target_key = part

        # Track currently pressed modifiers
        self._pressed_modifiers = set()

        def on_press(key):
            try:
                # Detect specific L/R modifiers
                is_ctrl_l = key == keyboard.Key.ctrl_l
                is_ctrl_r = key == keyboard.Key.ctrl_r
                is_alt_l = key == keyboard.Key.alt_l
                is_alt_r = key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr
                is_shift_l = key == keyboard.Key.shift_l
                is_shift_r = key == keyboard.Key.shift_r

                is_ctrl = is_ctrl_l or is_ctrl_r
                is_alt = is_alt_l or is_alt_r
                is_shift = is_shift_l or is_shift_r

                # Track generic modifier state
                if is_ctrl:
                    self._pressed_modifiers.add('ctrl')
                if is_alt:
                    self._pressed_modifiers.add('alt')
                if is_shift:
                    self._pressed_modifiers.add('shift')

                # Handle single L/R modifier hotkey (e.g., "shift_l", "ctrl_r")
                if is_single_modifier and is_lr_modifier:
                    if (target_key == 'ctrl_l' and is_ctrl_l) or \
                            (target_key == 'ctrl_r' and is_ctrl_r) or \
                            (target_key == 'alt_l' and is_alt_l) or \
                            (target_key == 'alt_r' and is_alt_r) or \
                            (target_key == 'shift_l' and is_shift_l) or \
                            (target_key == 'shift_r' and is_shift_r):
                        self.hotkey_signal.triggered.emit()
                    return

                # Handle generic single modifier hotkey (e.g., just "ctrl")
                if is_single_modifier and not is_lr_modifier:
                    if (target_key == 'ctrl' and is_ctrl) or \
                            (target_key == 'alt' and is_alt) or \
                            (target_key == 'shift' and is_shift):
                        self.hotkey_signal.triggered.emit()
                    return

                # Get key name for combo hotkeys
                key_name = None
                if hasattr(key, 'name'):
                    key_name = key.name.lower()
                elif hasattr(key, 'char') and key.char:
                    key_name = key.char.lower()

                # Special key name mappings
                KEY_MAP = {
                    'space': 'space',
                    'tab': 'tab',
                    'enter': 'enter',
                    'return': 'enter',
                    'backspace': 'backspace',
                    'delete': 'delete',
                    'insert': 'insert',
                    'home': 'home',
                    'end': 'end',
                    'page_up': 'page_up',
                    'page_down': 'page_down',
                    'up': 'up',
                    'down': 'down',
                    'left': 'left',
                    'right': 'right',
                    'caps_lock': 'caps_lock',
                    'num_lock': 'num_lock',
                    'scroll_lock': 'scroll_lock',
                    'pause': 'pause',
                    'print_screen': 'print_screen',
                }

                if key_name in KEY_MAP:
                    key_name = KEY_MAP[key_name]

                if key_name and key_name == target_key:
                    # Check all required modifiers are pressed
                    if required_modifiers <= self._pressed_modifiers:
                        self.hotkey_signal.triggered.emit()
            except AttributeError:
                pass

        def on_release(key):
            try:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self._pressed_modifiers.discard('ctrl')
                elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr:
                    self._pressed_modifiers.discard('alt')
                elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                    self._pressed_modifiers.discard('shift')
            except AttributeError:
                pass

        self.hotkey_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()

        # Linux specific warning for Wayland
        import platform
        if platform.system() == "Linux":
            session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
            if session_type == 'wayland':
                print("⚠️  Warning: You are using Wayland. Global hotkeys may not work when the app is inactive.")
                print("   Switch to an X11 (Xorg) session for full global hotkey support.")
            else:
                print(f"Session: {session_type or 'unknown (assume X11)'}")

        print(f"Global hotkey '{hotkey_config}' activated!")

    def update_timer_interval(self):
        interval_ms = self.config_manager.timer_interval * 1000
        self.timer.start(interval_ms)
        print(f"Timer set to {self.config_manager.timer_interval} seconds")

    def run(self):
        signal.signal(signal.SIGINT, self.quit_app)
        safe_timer = QTimer()
        safe_timer.start(500)
        safe_timer.timeout.connect(lambda: None)

        topics = self.vocabulary.get_all_topics()
        print(f"{APP_NAME} started. Topics: {topics}")
        print(f"Cards every {self.config_manager.timer_interval}s.")
        sys.exit(self.app.exec())

    def force_show_flashcard(self):
        """Forces showing next card (closes existing).

        Used for EXPLICIT triggers (global hotkey / tray menu): the user asked
        for a card right now, so we bring it to the foreground and focus it.
        """
        if self.flashcard_widget and self.flashcard_widget.isVisible():
            self.flashcard_widget.close()
        self.show_flashcard(activate=True)

    def show_flashcard(self, activate=False):
        """Shows the next card.

        activate=False (default, timer-driven): the card appears as a pinned
        overlay WITHOUT stealing focus — you keep typing / gaming and answer it
        by mouse when you have a moment (e.g. between deaths in a match).
        activate=True (hotkey / menu): you asked for it, so it is raised and the
        answer field is focused for immediate typing.
        """
        if self.flashcard_widget and self.flashcard_widget.isVisible():
            return

        card = self.vocabulary.get_random_card()
        if not card:
            active_topics = self.config_manager.active_topics
            self.vocabulary.shuffle_deck(self.stats_manager, active_topics if active_topics else None)
            card = self.vocabulary.get_random_card()
            if not card:
                return

        self.flashcard_widget = FlashcardWidget(
            card,
            self.stats_manager,
            self.vocabulary,
            self.similarity_checker,
            is_multiple_choice=self.next_question_is_mc,
            config_manager=self.config_manager
        )
        self.next_question_is_mc = not self.next_question_is_mc
        self.flashcard_widget.closed.connect(self.on_widget_closed)
        self.flashcard_widget.card_delete_requested.connect(self.handle_card_deletion)

        # --- ИСПРАВЛЕННЫЙ ПОРЯДОК ТУТ ---
        self.flashcard_widget.show()  # 1. Сначала показываем (Qt инициализирует метрики)
        self.flashcard_widget.adjustSize()  # 2. Подгоняем размер под реальный текст
        self.position_widget(self.flashcard_widget)  # 3. Двигаем в нужный угол экрана

        # Always float above other windows...
        self.flashcard_widget.raise_()
        if activate:
            # ...but only grab focus / keyboard when the card was summoned
            # explicitly. The timer-driven overlay must NOT steal focus.
            self.flashcard_widget.activateWindow()
            self.flashcard_widget.focus_answer_input()

    def on_widget_closed(self):
        self.flashcard_widget = None

    def handle_card_deletion(self, card_to_delete):
        english_word = card_to_delete.get('english') if isinstance(card_to_delete, dict) else card_to_delete
        print(f"Deleting: {english_word}")
        deleted = self.vocabulary.delete_word(english_word)
        if deleted:
            QTimer.singleShot(50, self.show_flashcard)

    def shuffle_deck(self):
        print("Shuffle requested.")
        if self.flashcard_widget and self.flashcard_widget.isVisible():
            self.flashcard_widget.close()

        active_topics = self.config_manager.active_topics
        self.vocabulary.shuffle_deck(self.stats_manager, active_topics if active_topics else None)

        self.tray_icon.showMessage(
            "Колода перемешана",
            f"Новая сессия из {len(self.vocabulary.deck)} карт!",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        QTimer.singleShot(100, self.show_flashcard)

    def show_management_window(self):
        print("Opening management window...")
        self.timer.stop()

        dialog = ManagementWindow(
            self.vocabulary,
            self.stats_manager,
            self.config_manager
        )
        dialog.exec()

        active_topics = self.config_manager.active_topics
        self.vocabulary.shuffle_deck(self.stats_manager, active_topics if active_topics else None)
        self.update_timer_interval()
        print("Management closed. Timer resumed.")

    def switch_user(self):
        """Restarts app to switch user."""
        print("Switching user...")
        self.stats_manager.save_stats()
        self.timer.stop()

        # Clear last user to force profile selection
        profile_manager.set_last_user("")

        # Restart the app
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)
        self.app.quit()

    def position_widget(self, widget):
        """Positions widget based on config setting."""
        from PyQt6.QtGui import QCursor

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        widget_size = widget.frameGeometry().size()
        padding = 20

        position = self.config_manager.card_position

        if position == 'mouse':
            # Smart offset from the cursor (tooltip-style), NOT centered on it.
            # Centering covers the exact point the user is reading/working at,
            # which is an intrusive antipattern. Instead we place the card
            # below-right of the pointer with a small gap so that spot stays
            # visible, and flip to the other side near a screen edge.
            cursor_pos = QCursor.pos()
            gap = 18
            w = widget_size.width()
            h = widget_size.height()

            x = cursor_pos.x() + gap
            y = cursor_pos.y() + gap
            # Flip left / up if the card would run off the right / bottom edge.
            if x + w > screen_geometry.right() - padding:
                x = cursor_pos.x() - gap - w
            if y + h > screen_geometry.bottom() - padding:
                y = cursor_pos.y() - gap - h
            # Final clamp so it is always fully on-screen.
            x = max(screen_geometry.left() + padding, min(x, screen_geometry.right() - w - padding))
            y = max(screen_geometry.top() + padding, min(y, screen_geometry.bottom() - h - padding))
        elif position == 'center':
            x = (screen_geometry.width() - widget_size.width()) // 2
            y = (screen_geometry.height() - widget_size.height()) // 2
        elif position == 'top_right':
            x = screen_geometry.right() - widget_size.width() - padding
            y = screen_geometry.top() + padding
        elif position == 'top_left':
            x = screen_geometry.left() + padding
            y = screen_geometry.top() + padding
        elif position == 'bottom_left':
            x = screen_geometry.left() + padding
            y = screen_geometry.bottom() - widget_size.height() - padding
        else:  # bottom_right (default)
            x = screen_geometry.right() - widget_size.width() - padding
            y = screen_geometry.bottom() - widget_size.height() - padding

        widget.move(x, y)

    def quit_app(self, *args):
        print("Saving and quitting...")
        self.stats_manager.save_stats()
        self.timer.stop()
        if hasattr(self, 'evdev_listener'):
            self.evdev_listener.stop()
        if HOTKEY_AVAILABLE and hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        self.app.quit()


def prefer_x11_on_wayland():
    """On a Wayland session, ask Qt to run through XWayland (the 'xcb' plugin).

    Native Wayland forbids a client from (a) querying the global mouse cursor and
    (b) positioning its own top-level window. That breaks the 'card_position'
    feature entirely — the card can't appear at the cursor or in a screen corner,
    because move() and QCursor.pos() are both no-ops there.

    Under XWayland both work again, restoring the Windows-like behavior. The
    other Linux fixes are platform-independent: global hotkeys use the evdev
    backend, and window dragging uses QWindow.startSystemMove(), both of which
    work under xcb too.

    Escape hatch: set SMART_FLASHCARDS_FORCE_WAYLAND=1 to keep native Wayland
    (e.g. to avoid slight blur on fractional HiDPI scaling). An explicitly
    pre-set QT_QPA_PLATFORM is always respected. The 'xcb;wayland' fallback list
    means that if the xcb plugin can't initialise, Qt cleanly falls back to
    native Wayland instead of failing to start.

    Must be called BEFORE QApplication is constructed.
    """
    import platform
    if platform.system() != "Linux":
        return
    if os.environ.get('QT_QPA_PLATFORM'):
        return  # user made an explicit choice; don't override it
    if os.environ.get('SMART_FLASHCARDS_FORCE_WAYLAND') == '1':
        print("SMART_FLASHCARDS_FORCE_WAYLAND=1 set — keeping native Wayland. "
              "Note: card positioning at the mouse cursor / corners won't work.")
        return
    session = os.environ.get('XDG_SESSION_TYPE', '').lower()
    is_wayland = session == 'wayland' or bool(os.environ.get('WAYLAND_DISPLAY'))
    if not is_wayland:
        return
    os.environ['QT_QPA_PLATFORM'] = 'xcb;wayland'
    print("Wayland detected → running Qt via XWayland (xcb) so the flashcard "
          "can be positioned at the mouse cursor / screen corners. "
          "Set SMART_FLASHCARDS_FORCE_WAYLAND=1 to keep native Wayland.")


def exception_hook(exctype, value, traceback):
    """Принудительно выводит нормальный Traceback ошибки в консоль, минуя глушилки Qt"""
    import traceback as tb
    sys.__stderr__.write("".join(tb.format_exception(exctype, value, traceback)))
    sys.exit(1)


if __name__ == '__main__':
    sys.excepthook = exception_hook  # <- Магия здесь
    setup_logging()
    prefer_x11_on_wayland()  # must run before QApplication is created
    flashcard_app = FlashcardApp()
    flashcard_app.run()
