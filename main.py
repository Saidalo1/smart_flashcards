import base64
import logging
import os
import signal
import sys
from datetime import datetime

from PySide6.QtCore import QTimer, Signal, QObject
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from app_paths import get_data_dir, is_frozen


def setup_logging():
    """Sets up file logging in the data directory next to the exe."""
    log_dir = get_data_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'app.log'

    # In a windowed PyInstaller build (console=False) sys.stdout/err are None, so a
    # StreamHandler(None) would fail on every record and recurse into "Logging error".
    # Only attach a console handler when there really is a console.
    handlers = [logging.FileHandler(str(log_file), encoding='utf-8')]
    if sys.stdout is not None:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers,
    )

    # Redirect print()/errors into the logger so the app's many print() calls keep
    # working even without a console (where sys.stdout/err are None).
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
from i18n import tr

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
    triggered = Signal()


class UpdateChecker(QObject):
    """Checks the releases repo off the UI thread; signals back if an update exists."""
    update_found = Signal(str, str)  # (version, installer_url)

    def check_async(self):
        import threading
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            from updater import check_for_update
            result = check_for_update()
        except Exception:
            result = None
        if result:
            self.update_found.emit(result[0], result[1])


class FlashcardApp:
    """Main application class."""

    def __init__(self):
        # Windows shows the taskbar icon per "AppUserModelID". Without our own id the
        # button inherits pythonw's (blank) icon even though the tray icon is fine.
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('SmartFlashcards.App.1')
            except Exception:
                pass

        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")  # Required: WindowsVista style breaks border-radius rendering
        self.app.setQuitOnLastWindowClosed(False)

        # Build the app icon once and set it app-wide so every window (and the taskbar
        # button) shows it. The tray icon below reuses the same QIcon.
        self._app_pixmap = QPixmap()
        self._app_pixmap.loadFromData(base64.b64decode(icon_b64))
        self.app_icon = QIcon(self._app_pixmap)
        self.app.setWindowIcon(self.app_icon)

        # Dark styling for the dropdown list of every QComboBox. Without this, the
        # opened list is white-on-white on light-themed Windows (only the arrow
        # glyphs show) — unreadable. Applied app-wide so all combos are covered.
        self.app.setStyleSheet(self.app.styleSheet() + """
            QComboBox QAbstractItemView {
                background-color: #16213e;
                color: #eaeaea;
                selection-background-color: #7b2ff7;
                selection-color: #ffffff;
                border: 1px solid #0f3460;
                outline: 0;
            }
            QComboBox QAbstractItemView::item { min-height: 26px; padding: 4px 8px; }
        """)

        # Load vocabulary first (needed for startup dialog)
        self.vocabulary = Vocabulary()

        # Very first launch only: ask the interface language up front (audience is
        # mostly Uzbek friends), then remember it. Skipped on every later launch.
        from i18n import is_language_chosen
        if not is_language_chosen():
            self._ask_language_first_run()

        # Show startup dialog for profile selection. It returns RESTART_CODE when
        # the user switches the interface language, so we re-open it localized.
        while True:
            startup = StartupDialog(vocabulary=self.vocabulary)
            code = startup.exec()
            if code == StartupDialog.RESTART_CODE:
                continue
            if code != startup.DialogCode.Accepted:
                sys.exit(0)
            break

        username, selected_topics, study_mode = startup.get_result()
        self.current_user = username
        print(f"User profile: {username}")

        # Initialize managers with user profile path
        user_profile_path = profile_manager.get_profile_path(username)
        self.config_manager = ConfigManager(config_path=user_profile_path / 'config.json')
        self.stats_manager = StatsManager(stats_path=user_profile_path / 'stats.json')
        self.similarity_checker = SimilarityChecker(
            threshold=self.config_manager.similarity_threshold,
            fuzz_threshold=self.config_manager.fuzz_threshold,
            use_semantic=self.config_manager.semantic_grading,
        )

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

        # Setup System Tray (reuse the app-wide icon built above)
        self.tray_icon = QSystemTrayIcon(self.app_icon, self.app)
        hotkey = self.config_manager.hotkey
        self.tray_icon.setToolTip(f"{APP_NAME} — {username} (Press {hotkey})")

        # Actions
        self.user_action = QAction(f"👤 {username}")
        self.user_action.setEnabled(False)

        self.manage_action = QAction(tr('tray_manage'))
        self.manage_action.triggered.connect(self.show_management_window)

        self.shuffle_action = QAction(tr('tray_shuffle'))
        self.shuffle_action.triggered.connect(self.shuffle_deck)

        self.next_card_action = QAction(tr('tray_next_card', hotkey=hotkey))
        self.next_card_action.triggered.connect(self.force_show_flashcard)

        self.switch_user_action = QAction(tr('tray_main_menu'))
        self.switch_user_action.triggered.connect(self.switch_user)

        self.quit_action = QAction(tr('tray_quit'))
        self.quit_action.triggered.connect(self.quit_app)

        # Quick topic switcher: a checkable submenu right in the tray, so a set can
        # be toggled in two clicks without opening the management window (or having
        # to "switch user"). Rebuilt on open so added/deleted topics stay in sync.
        self.topics_menu = QMenu(tr('tray_topics'))
        self.topics_menu.aboutToShow.connect(self._rebuild_topics_menu)

        # Menu
        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.user_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addMenu(self.topics_menu)
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

        # Background update check (packaged builds only). If a newer release exists
        # in the public dist repo, offer to download & run its installer.
        if is_frozen():
            self._update_checker = UpdateChecker()
            self._update_checker.update_found.connect(self._on_update_found)
            self._update_checker.check_async()

        sys.exit(self.app.exec())

    def _on_update_found(self, version, url):
        """A newer release exists — offer to download and run its installer."""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            None, tr('update_title'),
            tr('update_available', version=version),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        from updater import download_installer, run_installer
        path = download_installer(url)
        if path and run_installer(path):
            # Quit so the installer can replace the running files.
            self.quit_app()
        else:
            QMessageBox.warning(None, tr('update_title'), tr('update_failed'))

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
            config_manager=self.config_manager,
            accept_focus=activate
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
            # explicitly (hotkey / menu). The timer-driven overlay must NOT steal
            # focus — it is answered by mouse, or you click its field to type.
            self.flashcard_widget.summon_focus()

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
            tr('deck_shuffled'),
            tr('deck_shuffled_msg', n=len(self.vocabulary.deck)),
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        QTimer.singleShot(100, self.show_flashcard)

    def _rebuild_topics_menu(self):
        """(Re)builds the checkable topic submenu from current vocabulary + config.

        Topics are grouped by their base name (the part before '(...)') so a set
        like "vocab 7" collapses into one sub-menu of its chunks instead of a flat
        wall of items.
        """
        from collections import OrderedDict

        menu = self.topics_menu
        menu.clear()

        all_topics = self.vocabulary.get_all_topics()
        active = self.config_manager.active_topics
        all_active = not active            # empty list = every topic is active
        selected = set(active)

        select_all = QAction(tr('tray_select_all'), menu)
        select_all.triggered.connect(self._select_all_topics)
        menu.addAction(select_all)
        menu.addSeparator()

        if not all_topics:
            empty = QAction(tr('tray_no_topics'), menu)
            empty.setEnabled(False)
            menu.addAction(empty)
            return

        groups = OrderedDict()
        for t in all_topics:
            groups.setdefault(t.split(' (')[0], []).append(t)

        for base, items in groups.items():
            if len(items) == 1 and items[0] == base:
                self._add_topic_action(menu, items[0], base, all_active or items[0] in selected)
            else:
                sub = QMenu(base, menu)
                for t in items:
                    label = t[len(base):].strip() or t   # e.g. "(1-15)"
                    self._add_topic_action(sub, t, label, all_active or t in selected)
                menu.addMenu(sub)

    def _add_topic_action(self, parent_menu, topic_name, label, checked):
        act = QAction(label, parent_menu)
        act.setCheckable(True)
        act.setChecked(checked)   # set BEFORE connecting so it doesn't fire toggled
        act.toggled.connect(lambda ch, name=topic_name: self._toggle_topic(name, ch))
        parent_menu.addAction(act)

    def _toggle_topic(self, topic_name, checked):
        """Adds/removes one topic from the active set and reshuffles."""
        all_topics = self.vocabulary.get_all_topics()
        current = set(self.config_manager.active_topics) or set(all_topics)
        if checked:
            current.add(topic_name)
        else:
            current.discard(topic_name)
        # Empty stored list means "all active", so collapse a full selection to [].
        new_topics = [] if len(current) >= len(all_topics) else [t for t in all_topics if t in current]
        self.config_manager.active_topics = new_topics
        self._apply_topic_change()

    def _select_all_topics(self):
        self.config_manager.active_topics = []
        self._apply_topic_change()

    def _apply_topic_change(self):
        """Reshuffles the deck for the current topic selection and shows a card."""
        active = self.config_manager.active_topics
        if self.flashcard_widget and self.flashcard_widget.isVisible():
            self.flashcard_widget.close()
        self.vocabulary.shuffle_deck(self.stats_manager, active if active else None)
        count = len(active) if active else len(self.vocabulary.get_all_topics())
        if self.config_manager.get('show_notifications', True):
            self.tray_icon.showMessage(
                tr('topics_updated'),
                tr('topics_updated_msg', count=count, deck=len(self.vocabulary.deck)),
                QSystemTrayIcon.MessageIcon.Information,
                1800,
            )
        QTimer.singleShot(100, self.show_flashcard)

    def _ask_language_first_run(self):
        """First launch only: a small three-button interface-language picker."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import Qt
        from i18n import LANGUAGES, set_language

        dlg = QDialog()
        dlg.setWindowTitle("Til / Язык / Language")
        dlg.setWindowIcon(self.app_icon)
        dlg.setModal(True)
        dlg.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QLabel { color: #eaeaea; }
            QPushButton {
                background-color: #16213e; color: #eaeaea;
                border: 1px solid #0f3460; border-radius: 10px;
                padding: 12px 18px; font-size: 14px;
            }
            QPushButton:hover { background-color: #0f3460; border-color: #7b2ff7; }
        """)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        title = QLabel("🌐  Tilni tanlang · Выберите язык · Choose language")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        lay.addWidget(title)

        # Uzbek first (main audience), then Russian, then English.
        for code in ('uz', 'ru', 'en'):
            btn = QPushButton(LANGUAGES[code])
            btn.clicked.connect(lambda _=False, c=code: (set_language(c), dlg.accept()))
            lay.addWidget(btn)

        dlg.exec()

    def show_management_window(self):
        # Guard against a second click spawning a duplicate: if the window is already
        # open, just bring it to the front instead of opening another one.
        if self.management_window is not None:
            self.management_window.raise_()
            self.management_window.activateWindow()
            return

        print("Opening management window...")
        self.timer.stop()

        self.management_window = ManagementWindow(
            self.vocabulary,
            self.stats_manager,
            self.config_manager
        )
        try:
            self.management_window.exec()
        finally:
            self.management_window = None

        # Apply any settings changed in the window without needing a restart.
        # (semantic_grading on/off still needs a restart to load/unload the model.)
        self.similarity_checker.threshold = self.config_manager.similarity_threshold
        self.similarity_checker.fuzz_threshold = self.config_manager.fuzz_threshold
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

        # Relaunch the app. In a onefile PyInstaller build the running process sets
        # _MEIPASS2 in the environment; if a freshly spawned copy inherits it, its
        # bootloader thinks it's already unpacked and dies with "Failed to start
        # embedded python interpreter" (+ "Failed to remove temporary directory").
        # Strip it so the child extracts into its own _MEI dir. Also sys.argv[0] is
        # already the exe when frozen, so relaunch with argv[1:] to avoid passing the
        # exe path as an argument.
        import subprocess
        env = os.environ.copy()
        # PyInstaller 6.x points a re-exec'd process at the parent's temp dir via
        # _MEIPASS2 AND several _PYI_* vars; a child that inherits any of them fails
        # to bootstrap. Strip them all so the relaunched exe extracts cleanly.
        for _k in [k for k in env if k.startswith('_MEIPASS') or k.startswith('_PYI')]:
            env.pop(_k, None)
        if is_frozen():
            # Packaged build (PyInstaller OR Nuitka): relaunch the exe itself.
            # sys.executable can be empty/wrong under Nuitka, so fall back to argv[0].
            exe = sys.executable if (sys.executable and os.path.exists(sys.executable)) else os.path.abspath(sys.argv[0])
            args = [exe]
        else:
            args = [sys.executable] + sys.argv
        subprocess.Popen(args, env=env, close_fds=True)
        self.app.quit()

    def position_widget(self, widget):
        """Positions widget based on config setting."""
        from PySide6.QtGui import QCursor

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
            x = screen_geometry.left() + (screen_geometry.width() - widget_size.width()) // 2
            y = screen_geometry.top() + (screen_geometry.height() - widget_size.height()) // 2
        elif position == 'middle_right':
            x = screen_geometry.right() - widget_size.width() - padding
            y = screen_geometry.top() + (screen_geometry.height() - widget_size.height()) // 2
        elif position == 'middle_left':
            x = screen_geometry.left() + padding
            y = screen_geometry.top() + (screen_geometry.height() - widget_size.height()) // 2
        elif position == 'top_center':
            x = screen_geometry.left() + (screen_geometry.width() - widget_size.width()) // 2
            y = screen_geometry.top() + padding
        elif position == 'bottom_center':
            x = screen_geometry.left() + (screen_geometry.width() - widget_size.width()) // 2
            y = screen_geometry.bottom() - widget_size.height() - padding
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
    """Logs an uncaught exception, then exits.

    In a windowed PyInstaller build (console=False) sys.__stderr__ is None, so
    writing to it would itself raise and hide the real error. Route through the
    logging file handler (always present) and only touch stderr if it exists.
    """
    import traceback as tb
    text = "".join(tb.format_exception(exctype, value, traceback))
    try:
        logging.critical("Uncaught exception:\n%s", text)
    except Exception:
        pass
    if sys.__stderr__ is not None:
        sys.__stderr__.write(text)
    sys.exit(1)


if __name__ == '__main__':
    sys.excepthook = exception_hook  # <- Магия здесь
    setup_logging()
    prefer_x11_on_wayland()  # must run before QApplication is created
    flashcard_app = FlashcardApp()
    flashcard_app.run()
