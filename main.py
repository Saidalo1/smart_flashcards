import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
import base64
from PyQt6.QtGui import QIcon, QCursor, QPixmap, QAction
from PyQt6.QtCore import QTimer
import signal

from vocabulary import Vocabulary
from flashcard_widget import FlashcardWidget
from stats_manager import StatsManager
from similarity_checker import SimilarityChecker
from management_window import ManagementWindow
from icon import icon_b64

# --- Constants ---
APP_NAME = "Smart Flashcards"
TIMER_INTERVAL_MS = 10 * 1000  # 10 seconds for testing

class FlashcardApp:
    """Main application class to manage the timer and flashcard windows."""

    def __init__(self):
        """Initializes the application, vocabulary, and system tray icon."""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # App stays running

        self.stats_manager = StatsManager()
        self.vocabulary = Vocabulary()
        self.similarity_checker = SimilarityChecker()
        self.flashcard_widget = None
        self.management_window = None
        self.next_question_is_mc = True # Start with multiple choice

        # Setup System Tray Icon
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(icon_b64))
        icon = QIcon(pixmap)
        self.tray_icon = QSystemTrayIcon(icon, self.app)
        self.tray_icon.setToolTip(f"{APP_NAME} is running")

        # --- Actions ---
        # Make actions instance variables to prevent garbage collection
        self.manage_action = QAction("Управление...")
        self.manage_action.triggered.connect(self.show_management_window)

        self.shuffle_action = QAction("Перемешать колоду")
        self.shuffle_action.triggered.connect(self.shuffle_deck)

        self.quit_action = QAction("Выход")
        self.quit_action.triggered.connect(self.quit_app)

        # --- Menu ---
        # Also make the menu an instance variable
        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.manage_action)
        self.tray_menu.addAction(self.shuffle_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Setup Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_flashcard)
        self.timer.start(TIMER_INTERVAL_MS)

        # --- Show the first card immediately on startup ---
        QTimer.singleShot(0, self.show_flashcard)

    def run(self):
        """Starts the application's main loop and sets up signal handling."""
        # This allows the Python interpreter to run and process signals like Ctrl+C
        signal.signal(signal.SIGINT, self.quit_app)
        safe_timer = QTimer()
        safe_timer.start(500)
        safe_timer.timeout.connect(lambda: None)

        print(f"{APP_NAME} started. A card will appear every {TIMER_INTERVAL_MS / 1000} seconds.")
        print("Right-click the tray icon for options.")
        sys.exit(self.app.exec())

    def show_flashcard(self):
        """Creates and shows a new flashcard widget if one isn't already visible."""
        if self.flashcard_widget and self.flashcard_widget.isVisible():
            return # Don't show a new card if one is already open

        card = self.vocabulary.get_random_card()
        if not card:
            print("Vocabulary is empty. Please add words to data/vocabulary.json")
            return

        self.flashcard_widget = FlashcardWidget(
            card,
            self.stats_manager,
            self.vocabulary,
            self.similarity_checker,
            is_multiple_choice=self.next_question_is_mc
        )
        self.next_question_is_mc = not self.next_question_is_mc # Alternate for next time
        self.flashcard_widget.closed.connect(self.on_widget_closed)
        self.flashcard_widget.card_delete_requested.connect(self.handle_card_deletion)
        # Position, show, and activate
        self.flashcard_widget.adjustSize() # Ensure size is calculated before positioning
        self.position_widget(self.flashcard_widget)
        self.flashcard_widget.show()
        self.flashcard_widget.activateWindow() # Ensure it gets focus
        self.flashcard_widget.raise_() # Bring to front

    def on_widget_closed(self):
        """Handles cleanup after the flashcard widget is closed."""
        self.flashcard_widget = None

    def handle_card_deletion(self, card_to_delete):
        """Handles the request to delete a card from the vocabulary."""
        print(f"Handling deletion for: {card_to_delete}")
        deleted = self.vocabulary.delete_word(card_to_delete)
        if deleted:
            # Use a single-shot timer to show the next card immediately
            # This allows the current event loop to finish cleanly.
            QTimer.singleShot(50, self.show_flashcard)
        else:
            print("Could not delete card, it was not found.")

    def shuffle_deck(self):
        """Shuffles the deck, closes any open card, and shows a new one."""
        print("Shuffle requested by user.")
        # Close the current card if it's open
        if self.flashcard_widget and self.flashcard_widget.isVisible():
            # Set a flag to prevent the timer from re-showing the card immediately
            self.flashcard_widget.close()

        # Shuffle the deck to create a new session
        self.vocabulary.shuffle_deck()

        # Show a notification
        self.tray_icon.showMessage(
            "Колода перемешана",
            f"Новая сессия из {len(self.vocabulary.deck)} карт готова!",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

        # Use a single-shot timer to show the new card almost immediately
        # This ensures the UI has time to process the close event first
        QTimer.singleShot(100, self.show_flashcard)

    def show_management_window(self):
        """Stops the timer and shows the management window as a modal dialog."""
        print("Pausing timer to show management window.")
        self.timer.stop()

        # Create and execute the dialog
        dialog = ManagementWindow(self.vocabulary, self.stats_manager)
        dialog.exec() # This blocks until the dialog is closed

        # Resume timer after the dialog is closed
        print("Management window closed. Resuming timer.")
        self.timer.start(TIMER_INTERVAL_MS)

    def position_widget(self, widget):
        """Positions the widget near the cursor, ensuring it stays on screen."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        cursor_pos = QCursor.pos()
        widget_size = widget.frameGeometry().size()

        x = cursor_pos.x() - widget_size.width() // 2
        y = cursor_pos.y() - widget_size.height() - 40 # A bit more space

        # Clamp to available screen geometry to avoid docks/taskbars
        if x < screen_geometry.left():
            x = screen_geometry.left()
        if y < screen_geometry.top():
            y = screen_geometry.top()
        if x + widget_size.width() > screen_geometry.right():
            x = screen_geometry.right() - widget_size.width()
        if y + widget_size.height() > screen_geometry.bottom():
            y = screen_geometry.bottom() - widget_size.height()

        widget.move(x, y)

    def open_settings(self):
        """Placeholder for opening the settings window."""
        # TODO: Implement the settings window in the next step
        print("Settings window will be implemented here.")

    def quit_app(self, *args):
        """Stops the timer, saves stats, and quits the application gracefully."""
        print("Saving stats...")
        self.stats_manager.save_stats()
        self.timer.stop()
        self.app.quit()

if __name__ == '__main__':
    flashcard_app = FlashcardApp()
    flashcard_app.run()
