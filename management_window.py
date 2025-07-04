# management_window.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QDialog, QLineEdit, QDialogButtonBox, 
    QMessageBox, QTabWidget, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt

class WordEditDialog(QDialog):
    """A dialog for adding or editing a word."""
    def __init__(self, english="", uzbek="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Word")

        self.english_edit = QLineEdit(english)
        self.uzbek_edit = QLineEdit(uzbek)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("English:"))
        layout.addWidget(self.english_edit)
        layout.addWidget(QLabel("Uzbek:"))
        layout.addWidget(self.uzbek_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_words(self):
        """Returns the entered words."""
        return self.english_edit.text().strip(), self.uzbek_edit.text().strip()


class ManagementWindow(QDialog):
    """A window for managing the vocabulary and viewing stats."""

    def __init__(self, vocabulary, stats_manager, parent=None):
        super().__init__(parent)
        self.vocabulary = vocabulary
        self.stats_manager = stats_manager

        self.setWindowTitle("Управление словарем и статистикой")
        self.setMinimumSize(800, 600)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        
        # --- Tab Widget ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Vocabulary Tab ---
        self.vocab_tab = QWidget()
        self.tabs.addTab(self.vocab_tab, "Словарь")
        self.setup_vocab_tab()

        # --- Stats Tab ---
        self.stats_tab = QWidget()
        self.tabs.addTab(self.stats_tab, "Статистика")
        self.setup_stats_tab()

        # Load initial data
        self.load_vocabulary_data()
        self.load_stats_data()

    def setup_vocab_tab(self):
        """Sets up the UI for the vocabulary management tab."""
        layout = QVBoxLayout(self.vocab_tab)
        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["English", "Uzbek"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only for now
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_word)
        edit_button = QPushButton("Редактировать")
        edit_button.clicked.connect(self.edit_word)
        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.delete_selected_word)
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

    def add_word(self):
        """Opens a dialog to add a new word."""
        dialog = WordEditDialog(parent=self)
        if dialog.exec():
            english, uzbek = dialog.get_words()
            if english and uzbek:
                if self.vocabulary.add_word(english, uzbek):
                    self.load_vocabulary_data()
                else:
                    QMessageBox.warning(self, "Дубликат", f"Слово '{english}' уже существует в словаре.")
            else:
                QMessageBox.warning(self, "Пустые поля", "Оба поля должны быть заполнены.")

    def setup_stats_tab(self):
        """Sets up the UI for the statistics tab."""
        layout = QVBoxLayout(self.stats_tab)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["Слово", "Правильно", "Неправильно", "Успешность (%)"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stats_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.stats_table.setSortingEnabled(True)
        layout.addWidget(self.stats_table)

    def load_vocabulary_data(self):
        """Loads words from the vocabulary manager into the table."""
        self.table.setRowCount(0) # Clear existing data
        words = self.vocabulary.get_all_words()
        self.table.setRowCount(len(words))

        for row, word_pair in enumerate(words):
            english_item = QTableWidgetItem(word_pair['english'])
            uzbek_item = QTableWidgetItem(word_pair['uzbek'])
            self.table.setItem(row, 0, english_item)
            self.table.setItem(row, 1, uzbek_item)

    def load_stats_data(self):
        """Loads statistics into the stats table."""
        stats = self.stats_manager.get_all_stats()
        self.stats_table.setRowCount(len(stats))

        for row, (word, data) in enumerate(stats.items()):
            correct = data.get('correct', 0)
            incorrect = data.get('incorrect', 0)
            total = correct + incorrect
            success_rate = (correct / total * 100) if total > 0 else 0

            # Create items for the table
            word_item = QTableWidgetItem(word)
            correct_item = QTableWidgetItem(str(correct))
            incorrect_item = QTableWidgetItem(str(incorrect))
            success_rate_item = QTableWidgetItem(f"{success_rate:.1f}")

            # Set alignment for numeric columns
            correct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            incorrect_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            success_rate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.stats_table.setItem(row, 0, word_item)
            self.stats_table.setItem(row, 1, correct_item)
            self.stats_table.setItem(row, 2, incorrect_item)
            self.stats_table.setItem(row, 3, success_rate_item)

        self.stats_table.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def edit_word(self):
        """Opens a dialog to edit the selected word."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите слово для редактирования.")
            return

        selected_row = selected_rows[0].row()
        old_english = self.table.item(selected_row, 0).text()
        old_uzbek = self.table.item(selected_row, 1).text()

        dialog = WordEditDialog(english=old_english, uzbek=old_uzbek, parent=self)
        if dialog.exec():
            new_english, new_uzbek = dialog.get_words()
            if new_english and new_uzbek:
                if self.vocabulary.update_word(old_english, new_english, new_uzbek):
                    self.load_vocabulary_data()
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось обновить слово '{old_english}'.")
            else:
                QMessageBox.warning(self, "Пустые поля", "Оба поля должны быть заполнены.")

    def delete_selected_word(self):
        """Deletes the selected word from the table and vocabulary."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите слово для удаления.")
            return

        # We only allow single row selection, so we take the first one
        selected_row = selected_rows[0].row()
        english_word = self.table.item(selected_row, 0).text()

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить слово '<b>{english_word}</b>'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted = self.vocabulary.delete_word(english_word)
            if deleted:
                self.load_vocabulary_data() # Refresh the table
                QMessageBox.information(self, "Успех", f"Слово '{english_word}' было удалено.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить слово. Оно не найдено в словаре.")


