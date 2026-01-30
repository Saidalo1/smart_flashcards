import sys
import threading
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
import base64
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
import signal

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

APP_NAME = "Smart Flashcards"


class HotkeySignal(QObject):
    """Signal emitter for global hotkey."""
    triggered = pyqtSignal()


class FlashcardApp:
    """Main application class."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Load vocabulary first (needed for startup dialog)
        self.vocabulary = Vocabulary()

        # Show startup dialog for profile selection
        startup = StartupDialog(vocabulary=self.vocabulary)
        if startup.exec() != startup.DialogCode.Accepted:
            sys.exit(0)
        
        username, selected_topics = startup.get_result()
        self.current_user = username
        print(f"User profile: {username}")

        # Initialize managers with user profile path
        user_profile_path = profile_manager.get_profile_path(username)
        self.config_manager = ConfigManager(config_path=user_profile_path / 'config.json')
        self.stats_manager = StatsManager(stats_path=user_profile_path / 'stats.json')
        self.similarity_checker = SimilarityChecker()

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
        """Sets up global hotkey listener using pynput with full modifier support."""
        if not HOTKEY_AVAILABLE:
            return
        
        hotkey_config = self.config_manager.hotkey.lower()
        
        # Parse hotkey (e.g., "ctrl+alt+k", "f7", or just "ctrl")
        parts = hotkey_config.split('+')
        required_modifiers = set()
        target_key = None
        is_single_modifier = False
        
        # Check if hotkey is single modifier
        if len(parts) == 1 and parts[0] in ('ctrl', 'alt', 'shift', 'win'):
            is_single_modifier = True
            target_key = parts[0]
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
                # Track modifier state
                is_ctrl = key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r
                is_alt = key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr
                is_shift = key == keyboard.Key.shift_l or key == keyboard.Key.shift_r
                
                if is_ctrl:
                    self._pressed_modifiers.add('ctrl')
                elif is_alt:
                    self._pressed_modifiers.add('alt')
                elif is_shift:
                    self._pressed_modifiers.add('shift')
                
                # Handle single modifier hotkey (e.g., just "ctrl")
                if is_single_modifier:
                    if (target_key == 'ctrl' and is_ctrl) or \
                       (target_key == 'alt' and is_alt) or \
                       (target_key == 'shift' and is_shift):
                        self.hotkey_signal.triggered.emit()
                    return
                
                # Check if target key pressed for combo hotkeys
                key_name = None
                if hasattr(key, 'name'):
                    key_name = key.name.lower()
                elif hasattr(key, 'char') and key.char:
                    key_name = key.char.lower()
                
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
        """Forces showing next card (closes existing)."""
        if self.flashcard_widget and self.flashcard_widget.isVisible():
            self.flashcard_widget.close()
        self.show_flashcard()

    def show_flashcard(self):
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
            is_multiple_choice=self.next_question_is_mc
        )
        self.next_question_is_mc = not self.next_question_is_mc
        self.flashcard_widget.closed.connect(self.on_widget_closed)
        self.flashcard_widget.card_delete_requested.connect(self.handle_card_deletion)
        self.flashcard_widget.adjustSize()
        self.position_widget(self.flashcard_widget)
        self.flashcard_widget.show()
        self.flashcard_widget.activateWindow()
        self.flashcard_widget.raise_()

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
            # Position at mouse cursor
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() - widget_size.width() // 2
            y = cursor_pos.y() - widget_size.height() // 2
            # Keep within screen bounds
            x = max(padding, min(x, screen_geometry.right() - widget_size.width() - padding))
            y = max(padding, min(y, screen_geometry.bottom() - widget_size.height() - padding))
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
        if HOTKEY_AVAILABLE and hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        self.app.quit()


if __name__ == '__main__':
    flashcard_app = FlashcardApp()
    flashcard_app.run()
