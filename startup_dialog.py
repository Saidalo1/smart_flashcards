"""
Startup dialog for selecting user profile and initial setup.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox, QCheckBox,
    QFrame, QWidget
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
}

QLabel#titleLabel {
    color: #00d9ff;
    font-size: 24px;
    font-weight: 700;
}

QLabel#subtitleLabel {
    color: #888;
    font-size: 12px;
}

QListWidget {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
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
    background: rgba(0, 217, 255, 0.3);
}

QListWidget::item:hover {
    background: rgba(255, 255, 255, 0.1);
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
    background: rgba(255, 255, 255, 0.1);
}

QPushButton#secondaryButton:hover {
    background: rgba(255, 255, 255, 0.2);
}

QLineEdit {
    background: rgba(255, 255, 255, 0.08);
    border: 2px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 12px 16px;
    color: #fff;
    font-size: 15px;
}

QLineEdit:focus {
    border: 2px solid #00d9ff;
}

QCheckBox {
    color: #ccc;
    font-size: 14px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.05);
}

QCheckBox::indicator:checked {
    background: #00d9ff;
    border-color: #00d9ff;
}

QFrame#card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
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
        self.setMinimumSize(500, 600)
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
        
        # Topics selection (for new users)
        if self.vocabulary:
            topics_frame = QFrame()
            topics_frame.setObjectName("card")
            topics_layout = QVBoxLayout(topics_frame)
            topics_layout.setSpacing(12)
            
            topics_label = QLabel("📚 Выберите темы для изучения")
            topics_label.setObjectName("titleLabel")
            topics_label.setFont(QFont("Segoe UI", 14))
            topics_layout.addWidget(topics_label)
            
            self.topic_checkboxes = {}
            all_topics = self.vocabulary.get_all_topics()
            for topic in all_topics:
                word_count = len([w for w in self.vocabulary.words if w.get('category') == topic])
                cb = QCheckBox(f"{topic} ({word_count} слов)")
                cb.setChecked(True)  # All checked by default for new users
                topics_layout.addWidget(cb)
                self.topic_checkboxes[topic] = cb
            
            layout.addWidget(topics_frame)
        
        # Continue button
        continue_btn = QPushButton("▶️ Продолжить")
        continue_btn.clicked.connect(self.select_and_continue)
        layout.addWidget(continue_btn)
    
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
        
        # Get selected topics
        if hasattr(self, 'topic_checkboxes'):
            self.selected_topics = [
                topic for topic, cb in self.topic_checkboxes.items() if cb.isChecked()
            ]
        
        self.accept()
    
    def get_result(self):
        """Returns the selected username and topics."""
        return self.selected_username, self.selected_topics
