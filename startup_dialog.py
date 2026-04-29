"""
Startup dialog for selecting user profile and initial setup.
"""

import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QFrame, QWidget, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import profile_manager


STARTUP_STYLE = """
QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1a2e, stop:1 #16213e);
    color: #eee;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QLabel {
    color: #ccc;
    font-size: 14px;
    background: transparent;
    border: none;
}

QLabel#titleLabel {
    color: #00d9ff;
    font-size: 24px;
    font-weight: 700;
    background: transparent;
}

QLabel#subtitleLabel {
    color: #888;
    font-size: 12px;
    background: transparent;
}

QListWidget {
    background: #1e2235;
    border: 1px solid #2a2e45;
    border-radius: 12px;
    color: #fff;
    font-size: 16px;
    padding: 8px;
}

QListWidget::item {
    padding: 12px;
    border-radius: 8px;
    margin: 4px 0;
}

QListWidget::item:selected {
    background: #1a4a5a;
}

QListWidget::item:hover {
    background: #252a40;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 14px 28px;
    font-size: 15px;
    font-weight: 600;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #764ba2, stop:1 #667eea);
}

QPushButton#secondaryButton {
    background: #252a40;
}

QPushButton#secondaryButton:hover {
    background: #2a3050;
}

QLineEdit {
    background: #1e2235;
    border: 2px solid #2a2e45;
    border-radius: 10px;
    padding: 12px 16px;
    color: #fff;
    font-size: 15px;
}

QLineEdit:focus {
    border: 2px solid #00d9ff;
}

QFrame#card {
    background: #1c1f33;
    border: 1px solid #2a2e45;
    border-radius: 16px;
}

/* Tree Widget for hierarchical topics */
QTreeWidget {
    background: #1c1f33;
    border: 1px solid #2a2e45;
    border-radius: 12px;
    color: #eee;
    font-size: 14px;
    padding: 4px;
    outline: none;
}

QTreeWidget::item {
    padding: 6px 4px;
    border: none;
}

QTreeWidget::item:hover {
    background: #252a40;
    border-radius: 6px;
}

QTreeWidget::item:selected {
    background: #1a4a5a;
    border-radius: 6px;
}

QTreeWidget::branch {
    background: transparent;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeWidget::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #2a2e45;
    border-radius: 4px;
    background: #1e2235;
}

QTreeWidget::indicator:checked {
    background: #00d9ff;
    border-color: #00d9ff;
}

QTreeWidget::indicator:indeterminate {
    background: #1a4a5a;
    border-color: #00d9ff;
}

QHeaderView {
    background: transparent;
}

QHeaderView::section {
    background: transparent;
    border: none;
}
"""


class StartupDialog(QDialog):
    """Dialog for selecting or creating a user profile at startup."""
    
    def __init__(self, vocabulary=None, parent=None):
        super().__init__(parent)
        self.vocabulary = vocabulary
        self.selected_username = None
        self.selected_topics = []
        
        self.setWindowTitle("Smart Flashcards — Добро пожаловать!")
        self.setMinimumSize(500, 700)
        self.setStyleSheet(STARTUP_STYLE)
        
        self.init_ui()
        self.load_profiles()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title
        title = QLabel("👋 Добро пожаловать!")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Выберите профиль или создайте новый")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.itemDoubleClicked.connect(self.select_and_continue)
        layout.addWidget(self.profile_list)
        
        # New profile section
        new_profile_frame = QFrame()
        new_profile_frame.setObjectName("card")
        new_profile_layout = QVBoxLayout(new_profile_frame)
        new_profile_layout.setSpacing(12)
        
        new_label = QLabel("✨ Новый профиль")
        new_label.setObjectName("titleLabel")
        new_label.setFont(QFont("Segoe UI", 14))
        new_profile_layout.addWidget(new_label)
        
        input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите имя...")
        self.name_input.returnPressed.connect(self.create_new_profile)
        input_layout.addWidget(self.name_input)
        
        create_btn = QPushButton("Создать")
        create_btn.clicked.connect(self.create_new_profile)
        create_btn.setFixedWidth(120)
        input_layout.addWidget(create_btn)
        
        new_profile_layout.addLayout(input_layout)
        layout.addWidget(new_profile_frame)
        
        # Topics selection with hierarchical tree
        if self.vocabulary:
            topics_frame = QFrame()
            topics_frame.setObjectName("card")
            topics_layout = QVBoxLayout(topics_frame)
            topics_layout.setSpacing(12)
            
            topics_label = QLabel("📚 Выберите темы для изучения")
            topics_label.setObjectName("titleLabel")
            topics_label.setFont(QFont("Segoe UI", 14))
            topics_layout.addWidget(topics_label)
            
            self.topics_tree = QTreeWidget()
            self.topics_tree.setHeaderHidden(True)
            self.topics_tree.setRootIsDecorated(True)
            self.topics_tree.setAnimated(True)
            self.topics_tree.setIndentation(24)
            self.topics_tree.itemChanged.connect(self._on_topic_item_changed)
            
            self._build_topics_tree()
            
            topics_layout.addWidget(self.topics_tree)
            layout.addWidget(topics_frame)
        
        # Continue button
        continue_btn = QPushButton("▶️ Продолжить")
        continue_btn.clicked.connect(self.select_and_continue)
        layout.addWidget(continue_btn)
    
    def _build_topics_tree(self):
        """Builds the hierarchical topic tree from vocabulary groups."""
        self.topics_tree.blockSignals(True)
        self.topics_tree.clear()
        self._topic_items = {}  # Maps full category name → QTreeWidgetItem

        grouped = self.vocabulary.get_grouped_topics()

        for group_name, categories in grouped.items():
            # Calculate total words in group
            total_words = sum(
                self.vocabulary.get_word_count_for_topic(cat) for cat in categories
            )

            # Create parent item
            parent = QTreeWidgetItem(self.topics_tree)
            parent.setText(0, f"📁 {group_name} ({total_words} слов)")
            parent.setFlags(
                parent.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsAutoTristate
            )
            parent.setCheckState(0, Qt.CheckState.Checked)
            parent.setExpanded(True)

            # Create child items for each sub-category
            for cat in categories:
                word_count = self.vocabulary.get_word_count_for_topic(cat)
                # Extract the range part from "SAT Vocabulary (1-15)" → "1-15"
                match = re.match(r'^.+?\s*\((.+)\)$', cat)
                display_name = match.group(1) if match else cat

                child = QTreeWidgetItem(parent)
                child.setText(0, f"{display_name} ({word_count} слов)")
                child.setFlags(
                    child.flags() | Qt.ItemFlag.ItemIsUserCheckable
                )
                child.setCheckState(0, Qt.CheckState.Checked)
                child.setData(0, Qt.ItemDataRole.UserRole, cat)  # Store full category name
                self._topic_items[cat] = child

        self.topics_tree.blockSignals(False)

    def _on_topic_item_changed(self, item, column):
        """Handles tri-state checkbox logic for parent/child items."""
        self.topics_tree.blockSignals(True)

        # If parent changed → update all children
        if item.childCount() > 0:
            state = item.checkState(0)
            if state != Qt.CheckState.PartiallyChecked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, state)
        else:
            # Child changed → update parent tri-state
            parent = item.parent()
            if parent:
                checked = 0
                total = parent.childCount()
                for i in range(total):
                    if parent.child(i).checkState(0) == Qt.CheckState.Checked:
                        checked += 1

                if checked == 0:
                    parent.setCheckState(0, Qt.CheckState.Unchecked)
                elif checked == total:
                    parent.setCheckState(0, Qt.CheckState.Checked)
                else:
                    parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

        self.topics_tree.blockSignals(False)
    
    def load_profiles(self):
        """Loads existing profiles into the list."""
        self.profile_list.clear()
        profiles = profile_manager.get_all_profiles()
        last_user = profile_manager.get_last_user()
        
        for profile in profiles:
            item = QListWidgetItem(f"👤 {profile}")
            item.setData(Qt.ItemDataRole.UserRole, profile)
            self.profile_list.addItem(item)
            if profile == last_user:
                item.setSelected(True)
                self.profile_list.setCurrentItem(item)
    
    def create_new_profile(self):
        """Creates a new profile and selects it."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя профиля!")
            return
        
        if profile_manager.profile_exists(name):
            QMessageBox.warning(self, "Ошибка", f"Профиль '{name}' уже существует!")
            return
        
        profile_manager.create_profile(name)
        self.name_input.clear()
        self.load_profiles()
        
        # Select the new profile
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                item.setSelected(True)
                self.profile_list.setCurrentItem(item)
                break
    
    def select_and_continue(self):
        """Selects the current profile and closes the dialog."""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите или создайте профиль!")
            return
        
        self.selected_username = current_item.data(Qt.ItemDataRole.UserRole)
        profile_manager.set_last_user(self.selected_username)
        
        # Get selected topics from tree
        if hasattr(self, '_topic_items'):
            self.selected_topics = [
                cat for cat, item in self._topic_items.items()
                if item.checkState(0) == Qt.CheckState.Checked
            ]
        
        self.accept()
    
    def get_result(self):
        """Returns the selected username and topics."""
        return self.selected_username, self.selected_topics
