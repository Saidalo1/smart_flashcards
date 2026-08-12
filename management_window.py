# management_window.py
"""
Modern management window with vocabulary, statistics, and settings tabs.
"""

import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QDialog, QLineEdit, QDialogButtonBox, 
    QMessageBox, QTabWidget, QHBoxLayout, QLabel, QSlider, QSpinBox,
    QFrame, QGraphicsDropShadowEffect, QTreeWidget, QTreeWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from i18n import tr


# ============================================================================
# MODERN STYLESHEET
# ============================================================================
MODERN_STYLE = """
/* Main Window */
QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1a2e, stop:1 #16213e);
    color: #eee;
    font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* Tab Widget */
QTabWidget::pane {
    border: none;
    background: transparent;
}

QTabBar::tab {
    background: #1e2235;
    color: #888;
    padding: 12px 24px;
    margin-right: 4px;
    border: none;
    border-radius: 8px 8px 0 0;
    font-size: 14px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #252a40;
    color: #00d9ff;
}

QTabBar::tab:hover {
    background: #222740;
    color: #fff;
}

/* Tables */
QTableWidget {
    background: #1c1f33;
    border: 1px solid #2a2e45;
    border-radius: 12px;
    gridline-color: #252840;
    color: #eee;
    selection-background-color: #1a3a4a;
    alternate-background-color: #20243a;
}

QTableWidget::item {
    padding: 8px;
    border: none;
    background: #1c1f33;
}

QTableWidget::item:alternate {
    background: #20243a;
}

QTableWidget::item:selected {
    background: #1a4a5a;
    color: #fff;
}

QHeaderView::section {
    background: #1e2235;
    color: #00d9ff;
    padding: 12px;
    border: none;
    font-weight: 600;
    font-size: 13px;
}

/* Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #764ba2, stop:1 #667eea);
}

QPushButton:pressed {
    background: #5a67d8;
}

QPushButton#dangerButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e53e3e, stop:1 #c53030);
}

QPushButton#dangerButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #c53030, stop:1 #e53e3e);
}

/* Input Fields */
QLineEdit {
    background: #1e2235;
    border: 2px solid #2a2e45;
    border-radius: 8px;
    padding: 10px 16px;
    color: #eee;
    font-size: 14px;
}

QLineEdit:focus {
    border: 2px solid #00d9ff;
}

/* Labels */
QLabel {
    color: #ccc;
    font-size: 14px;
    background: transparent;
    border: none;
}

QLabel#titleLabel {
    color: #00d9ff;
    font-size: 18px;
    font-weight: 700;
    background: transparent;
    border: none;
}

QLabel#valueLabel {
    color: #fff;
    font-size: 24px;
    font-weight: 700;
    background: transparent;
}

/* Slider */
QSlider::groove:horizontal {
    background: #2a2e45;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00d9ff, stop:1 #667eea);
    width: 20px;
    height: 20px;
    margin: -6px 0;
    border-radius: 10px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #00d9ff);
    border-radius: 4px;
}

/* SpinBox */
QSpinBox {
    background: #1e2235;
    border: 2px solid #2a2e45;
    border-radius: 8px;
    padding: 8px 12px;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
}

QSpinBox:focus {
    border: 2px solid #00d9ff;
}

/* ComboBox */
QComboBox {
    background: #1e2235;
    border: 2px solid #2a2e45;
    border-radius: 8px;
    padding: 8px 12px;
    color: #fff;
    font-size: 14px;
}

QComboBox:focus {
    border: 2px solid #00d9ff;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background: #1e2235;
    border: 1px solid #2a2e45;
    color: #fff;
    selection-background-color: #1a4a5a;
}

/* CheckBox */
QCheckBox {
    color: #ccc;
    font-size: 14px;
    spacing: 8px;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #2a2e45;
    border-radius: 4px;
    background: #1e2235;
}

QCheckBox::indicator:checked {
    background: #00d9ff;
    border-color: #00d9ff;
}

/* Frame for cards */
QFrame#card {
    background: #1c1f33;
    border: 1px solid #2a2e45;
    border-radius: 16px;
    padding: 20px;
}
"""


class WordEditDialog(QDialog):
    """A dialog for adding or editing a word."""
    
    def __init__(self, english="", uzbek="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('edit_word_dlg'))
        self.setStyleSheet(MODERN_STYLE)
        self.setMinimumWidth(400)

        self.english_edit = QLineEdit(english)
        self.english_edit.setPlaceholderText("Enter English word or phrase...")
        self.uzbek_edit = QLineEdit(uzbek)
        self.uzbek_edit.setPlaceholderText("Enter Uzbek translation...")

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        eng_label = QLabel("🇬🇧 English")
        eng_label.setObjectName("titleLabel")
        layout.addWidget(eng_label)
        layout.addWidget(self.english_edit)
        
        uzb_label = QLabel("🇺🇿 Uzbek")
        uzb_label.setObjectName("titleLabel")
        layout.addWidget(uzb_label)
        layout.addWidget(self.uzbek_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_words(self):
        """Returns the entered words."""
        return self.english_edit.text().strip(), self.uzbek_edit.text().strip()


class ManagementWindow(QDialog):
    """Modern management window with vocabulary, statistics, and settings."""

    def __init__(self, vocabulary, stats_manager, config_manager=None, parent=None):
        super().__init__(parent)
        self.vocabulary = vocabulary
        self.stats_manager = stats_manager
        self.config_manager = config_manager

        self.setWindowTitle(tr('mgmt_title'))
        self.setMinimumSize(900, 650)
        self.setStyleSheet(MODERN_STYLE)

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Vocabulary Tab ---
        self.vocab_tab = QWidget()
        self.tabs.addTab(self.vocab_tab, tr('tab_vocab'))
        self.setup_vocab_tab()

        # --- Stats Tab ---
        self.stats_tab = QWidget()
        self.tabs.addTab(self.stats_tab, tr('tab_stats'))
        self.setup_stats_tab()

        # --- Settings Tab ---
        if self.config_manager:
            self.settings_tab = QWidget()
            self.tabs.addTab(self.settings_tab, tr('tab_settings'))
            self.setup_settings_tab()

        # Load data
        self.load_vocabulary_data()
        self.load_stats_data()

    def setup_vocab_tab(self):
        """Sets up the vocabulary management tab."""
        layout = QVBoxLayout(self.vocab_tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel(tr('tab_vocab'))
        header.setObjectName("titleLabel")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["🇬🇧 English", "🇺🇿 Uzbek", tr('th_level')])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        add_btn = QPushButton(tr('btn_add'))
        add_btn.clicked.connect(self.add_word)
        
        edit_btn = QPushButton(tr('btn_edit'))
        edit_btn.clicked.connect(self.edit_word)
        
        delete_btn = QPushButton(tr('btn_delete'))
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.delete_selected_word)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

    def setup_stats_tab(self):
        """Sets up the statistics tab."""
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel(tr('stats_header'))
        header.setObjectName("titleLabel")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        layout.addWidget(header)

        # Stats table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels([
            tr('stats_th_word'), tr('stats_th_correct'), tr('stats_th_wrong'), tr('stats_th_rate')
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stats_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.stats_table.setSortingEnabled(True)
        self.stats_table.setAlternatingRowColors(True)
        layout.addWidget(self.stats_table)

        # Reset button
        reset_btn = QPushButton(tr('reset_stats_btn'))
        reset_btn.setObjectName("dangerButton")
        reset_btn.clicked.connect(self.reset_all_stats)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(reset_btn)
        layout.addLayout(btn_layout)

    def setup_settings_tab(self):
        """Sets up the settings tab with a modern UI and a scroll area to prevent distortion."""
        from PySide6.QtWidgets import QScrollArea

        # Main layout for the tab
        main_tab_layout = QVBoxLayout(self.settings_tab)
        main_tab_layout.setContentsMargins(0, 0, 0, 0)

        # Create Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        # Container widget for settings content
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Header
        header = QLabel(tr('tab_settings'))
        header.setObjectName("titleLabel")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        layout.addWidget(header)

        # Study mode card
        mode_card = QFrame()
        mode_card.setObjectName("card")
        mode_card_layout = QVBoxLayout(mode_card)
        mode_card_layout.setSpacing(12)

        mode_header = QLabel(tr('study_mode'))
        mode_header.setObjectName("titleLabel")
        mode_card_layout.addWidget(mode_header)

        mode_desc = QLabel(tr('mode_desc'))
        mode_desc.setWordWrap(True)
        mode_card_layout.addWidget(mode_desc)

        from PySide6.QtWidgets import QComboBox
        self.study_mode_combo = QComboBox()
        self.study_mode_options = {
            'adaptive': tr('mode_adaptive'),
            'translation': tr('mode_translation'),
            'definition': tr('mode_definition'),
            'synonym': tr('mode_synonym'),
        }
        for key, label in self.study_mode_options.items():
            self.study_mode_combo.addItem(label, key)

        # Set current value
        current_mode = self.config_manager.study_mode
        mode_keys = list(self.study_mode_options.keys())
        if current_mode in mode_keys:
            self.study_mode_combo.setCurrentIndex(mode_keys.index(current_mode))
        self.study_mode_combo.currentIndexChanged.connect(self._save_study_mode)
        mode_card_layout.addWidget(self.study_mode_combo)
        layout.addWidget(mode_card)

        # Timer interval card
        timer_card = QFrame()
        timer_card.setObjectName("card")
        timer_layout = QVBoxLayout(timer_card)
        timer_layout.setSpacing(16)

        timer_header = QLabel(tr('set_timer_title'))
        timer_header.setObjectName("titleLabel")
        timer_layout.addWidget(timer_header)

        timer_desc = QLabel(tr('set_timer_desc'))
        timer_layout.addWidget(timer_desc)

        # Slider + SpinBox
        slider_layout = QHBoxLayout()
        
        self.timer_slider = QSlider(Qt.Orientation.Horizontal)
        self.timer_slider.setMinimum(10)
        self.timer_slider.setMaximum(300)
        self.timer_slider.setValue(self.config_manager.timer_interval)
        self.timer_slider.setTickInterval(30)
        self.timer_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        
        self.timer_spinbox = QSpinBox()
        self.timer_spinbox.setMinimum(10)
        self.timer_spinbox.setMaximum(300)
        self.timer_spinbox.setValue(self.config_manager.timer_interval)
        self.timer_spinbox.setSuffix(tr('unit_sec'))
        self.timer_spinbox.setFixedWidth(120)
        
        self.timer_slider.valueChanged.connect(self.timer_spinbox.setValue)
        self.timer_spinbox.valueChanged.connect(self.timer_slider.setValue)
        self.timer_spinbox.valueChanged.connect(self.save_timer_setting)
        
        slider_layout.addWidget(self.timer_slider)
        slider_layout.addWidget(self.timer_spinbox)
        timer_layout.addLayout(slider_layout)
        layout.addWidget(timer_card)

        # Grading strictness (similarity threshold) card
        threshold_card = QFrame()
        threshold_card.setObjectName("card")
        threshold_layout = QVBoxLayout(threshold_card)
        threshold_layout.setSpacing(12)

        threshold_header = QLabel(tr('set_strict_title'))
        threshold_header.setObjectName("titleLabel")
        threshold_layout.addWidget(threshold_header)

        threshold_desc = QLabel(tr('set_strict_desc'))
        threshold_desc.setWordWrap(True)
        threshold_layout.addWidget(threshold_desc)

        threshold_row = QHBoxLayout()
        _thr_pct = int(round(self.config_manager.similarity_threshold * 100))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(30)
        self.threshold_slider.setMaximum(95)
        self.threshold_slider.setValue(_thr_pct)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setMinimum(30)
        self.threshold_spinbox.setMaximum(95)
        self.threshold_spinbox.setValue(_thr_pct)
        self.threshold_spinbox.setSuffix(" %")
        self.threshold_spinbox.setFixedWidth(120)

        self.threshold_slider.valueChanged.connect(self.threshold_spinbox.setValue)
        self.threshold_spinbox.valueChanged.connect(self.threshold_slider.setValue)
        self.threshold_spinbox.valueChanged.connect(self.save_threshold_setting)

        threshold_row.addWidget(self.threshold_slider)
        threshold_row.addWidget(self.threshold_spinbox)
        threshold_layout.addLayout(threshold_row)

        self.semantic_checkbox = QCheckBox(tr('set_semantic'))
        self.semantic_checkbox.setChecked(self.config_manager.semantic_grading)
        self.semantic_checkbox.toggled.connect(self.save_semantic_setting)
        threshold_layout.addWidget(self.semantic_checkbox)

        semantic_note = QLabel(tr('set_semantic_note'))
        semantic_note.setWordWrap(True)
        semantic_note.setStyleSheet("color: #888; font-size: 12px;")
        threshold_layout.addWidget(semantic_note)

        layout.addWidget(threshold_card)

        # Topics selection card
        topics_card = QFrame()
        topics_card.setObjectName("card")
        topics_layout = QVBoxLayout(topics_card)
        topics_layout.setSpacing(12)

        topics_header = QLabel(tr('set_topics_title'))
        topics_header.setObjectName("titleLabel")
        topics_layout.addWidget(topics_header)

        topics_desc = QLabel(tr('set_topics_desc'))
        topics_desc.setWordWrap(True)
        topics_layout.addWidget(topics_desc)

        # Hierarchical topics tree
        self.topics_tree = QTreeWidget()
        self.topics_tree.setHeaderHidden(True)
        self.topics_tree.setRootIsDecorated(True)
        self.topics_tree.setAnimated(True)
        self.topics_tree.setIndentation(24)
        self.topics_tree.setStyleSheet("""
            QTreeWidget {
                background: #1e2235;
                border: 1px solid #2a2e45;
                border-radius: 8px;
                color: #eee;
                font-size: 14px;
                padding: 4px;
            }
            QTreeWidget::item { padding: 5px 4px; border: none; }
            QTreeWidget::item:hover { background: #252a40; }
            QTreeWidget::item:selected { background: #1a4a5a; }
            QTreeWidget::branch { background: transparent; }
            QTreeWidget::indicator {
                width: 16px; height: 16px;
                border: 2px solid #2a2e45; border-radius: 4px;
                background: #1e2235;
            }
            QTreeWidget::indicator:checked { background: #00d9ff; border-color: #00d9ff; }
            QTreeWidget::indicator:indeterminate { background: #1a4a5a; border-color: #00d9ff; }
            QHeaderView::section { background: transparent; border: none; }
        """)
        self.topics_tree.itemChanged.connect(self._on_settings_topic_changed)

        self._topic_items = {}  # Maps full category name → QTreeWidgetItem
        self._build_settings_topics_tree()

        topics_layout.addWidget(self.topics_tree)
        layout.addWidget(topics_card)

        # Position selection card
        position_card = QFrame()
        position_card.setObjectName("card")
        position_layout = QVBoxLayout(position_card)
        position_layout.setSpacing(12)

        position_header = QLabel(tr('set_position_title2'))
        position_header.setObjectName("titleLabel")
        position_layout.addWidget(position_header)

        position_desc = QLabel(tr('set_position_desc2'))
        position_layout.addWidget(position_desc)

        from PySide6.QtWidgets import QComboBox
        self.position_combo = QComboBox()
        self.position_options = {
            'bottom_right': tr('pos_bottom_right'),
            'bottom_left': tr('pos_bottom_left'),
            'top_right': tr('pos_top_right'),
            'top_left': tr('pos_top_left'),
            'middle_right': tr('pos_middle_right'),
            'middle_left': tr('pos_middle_left'),
            'top_center': tr('pos_top_center'),
            'bottom_center': tr('pos_bottom_center'),
            'center': tr('pos_center'),
            'mouse': tr('pos_mouse')
        }
        for key, label in self.position_options.items():
            self.position_combo.addItem(label, key)
        
        # Set current value
        current_pos = self.config_manager.card_position
        index = list(self.position_options.keys()).index(current_pos) if current_pos in self.position_options else 0
        self.position_combo.setCurrentIndex(index)
        self.position_combo.currentIndexChanged.connect(self.save_position_setting)
        position_layout.addWidget(self.position_combo)
        layout.addWidget(position_card)

        # Hotkey card
        hotkey_card = QFrame()
        hotkey_card.setObjectName("card")
        hotkey_layout = QVBoxLayout(hotkey_card)
        hotkey_layout.setSpacing(12)

        hotkey_header = QLabel(tr('set_hotkey_title'))
        hotkey_header.setObjectName("titleLabel")
        hotkey_layout.addWidget(hotkey_header)

        hotkey_desc = QLabel(tr('set_hotkey_desc'))
        hotkey_layout.addWidget(hotkey_desc)

        hotkey_row = QHBoxLayout()
        self.hotkey_label = QLabel(tr('set_hotkey_current', key=self.config_manager.hotkey))
        self.hotkey_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        hotkey_row.addWidget(self.hotkey_label)
        
        self.hotkey_btn = QPushButton(tr('set_hotkey_btn'))
        self.hotkey_btn.setObjectName("primaryBtn")
        self.hotkey_btn.clicked.connect(self.start_hotkey_capture)
        hotkey_row.addWidget(self.hotkey_btn)
        hotkey_layout.addLayout(hotkey_row)
        layout.addWidget(hotkey_card)

        # Info card
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        
        info_header = QLabel(tr('info_tip_title'))
        info_header.setObjectName("titleLabel")
        info_layout.addWidget(info_header)
        
        info_text = QLabel(
            tr('hotkey_restart_note')
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_card)
        layout.addStretch()

        # Set the container to the scroll area
        scroll.setWidget(container)
        main_tab_layout.addWidget(scroll)

    def save_timer_setting(self, value):
        """Saves the timer interval setting."""
        if self.config_manager:
            self.config_manager.timer_interval = value
            print(f"Timer interval saved: {value} seconds")

    def save_threshold_setting(self, percent):
        """Saves the answer-grading strictness (similarity threshold), as a percent."""
        if self.config_manager:
            self.config_manager.similarity_threshold = percent / 100.0
            print(f"Similarity threshold saved: {percent}% ({percent / 100.0:.2f})")

    def save_semantic_setting(self, checked):
        """Enables/disables synonym-aware semantic grading (applies on restart)."""
        if self.config_manager:
            self.config_manager.semantic_grading = checked
            print(f"Semantic grading set to: {checked} (restart to apply)")

    def _save_study_mode(self, index):
        """Saves the study mode setting."""
        if self.config_manager and hasattr(self, 'study_mode_combo'):
            mode = self.study_mode_combo.currentData()
            self.config_manager.study_mode = mode
            print(f"Study mode saved: {mode}")

    def _build_settings_topics_tree(self):
        """Builds the hierarchical topic tree for settings."""
        self.topics_tree.blockSignals(True)
        self.topics_tree.clear()
        self._topic_items = {}

        grouped = self.vocabulary.get_grouped_topics()
        active_topics = self.config_manager.active_topics

        for group_name, categories in grouped.items():
            total_words = sum(
                self.vocabulary.get_word_count_for_topic(cat) for cat in categories
            )

            parent = QTreeWidgetItem(self.topics_tree)
            parent.setText(0, f"📁 {group_name} ({tr('words_n', n=total_words)})")
            parent.setFlags(
                parent.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsAutoTristate
            )
            parent.setExpanded(False)

            for cat in categories:
                word_count = self.vocabulary.get_word_count_for_topic(cat)
                match = re.match(r'^.+?\s*\((.+)\)$', cat)
                display_name = match.group(1) if match else cat

                child = QTreeWidgetItem(parent)
                child.setText(0, f"{display_name} ({tr('words_n', n=word_count)})")
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                is_checked = cat in active_topics if active_topics else False
                child.setCheckState(0, Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
                child.setData(0, Qt.ItemDataRole.UserRole, cat)
                self._topic_items[cat] = child

            # Set parent state based on children
            checked = sum(1 for c in categories if self._topic_items[c].checkState(0) == Qt.CheckState.Checked)
            if checked == len(categories):
                parent.setCheckState(0, Qt.CheckState.Checked)
            elif checked == 0:
                parent.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

        self.topics_tree.blockSignals(False)

    def _on_settings_topic_changed(self, item, column):
        """Handles tri-state checkbox logic and saves topics."""
        self.topics_tree.blockSignals(True)

        if item.childCount() > 0:
            state = item.checkState(0)
            if state != Qt.CheckState.PartiallyChecked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, state)
        else:
            parent = item.parent()
            if parent:
                checked = sum(
                    1 for i in range(parent.childCount())
                    if parent.child(i).checkState(0) == Qt.CheckState.Checked
                )
                total = parent.childCount()
                if checked == 0:
                    parent.setCheckState(0, Qt.CheckState.Unchecked)
                elif checked == total:
                    parent.setCheckState(0, Qt.CheckState.Checked)
                else:
                    parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

        self.topics_tree.blockSignals(False)
        self.save_topics_setting()

    def save_topics_setting(self):
        """Saves the active topics setting from the tree widget."""
        if self.config_manager and hasattr(self, '_topic_items'):
            active_topics = [
                cat for cat, item in self._topic_items.items()
                if item.checkState(0) == Qt.CheckState.Checked
            ]
            self.config_manager.active_topics = active_topics
            print(f"Active topics saved: {active_topics if active_topics else 'All topics'}")

    def save_position_setting(self, index):
        """Saves the card position setting."""
        if self.config_manager and hasattr(self, 'position_combo'):
            position_key = self.position_combo.currentData()
            self.config_manager.card_position = position_key
            print(f"Card position saved: {position_key}")

    def start_hotkey_capture(self):
        """Starts capturing a new hotkey."""
        self.hotkey_btn.setText(tr('press_key'))
        self.hotkey_btn.setEnabled(False)
        self._capturing_hotkey = True
        self._current_modifiers = []
        self.grabKeyboard()

    def keyPressEvent(self, event):
        """Captures key for hotkey setting with L/R modifier support."""
        if hasattr(self, '_capturing_hotkey') and self._capturing_hotkey:
            from PySide6.QtCore import Qt
            key = event.key()
            scan_code = event.nativeScanCode()
            modifiers = event.modifiers()
            
            import platform
            is_linux = platform.system() == "Linux"

            # Platform-specific scan codes for L/R modifiers
            if is_linux:
                # X11 / Common Linux scan codes
                SCAN_CODES = {
                    37: 'ctrl_l',      # Left Ctrl
                    105: 'ctrl_r',     # Right Ctrl
                    50: 'shift_l',     # Left Shift
                    62: 'shift_r',     # Right Shift
                    64: 'alt_l',       # Left Alt
                    108: 'alt_r',      # Right Alt (AltGr)
                    133: 'win_l',      # Left Win
                    134: 'win_r',      # Right Win
                }
            else:
                # Windows scan codes
                SCAN_CODES = {
                    29: 'ctrl_l',      # Left Ctrl
                    285: 'ctrl_r',     # Right Ctrl (29 + 256)
                    42: 'shift_l',     # Left Shift
                    54: 'shift_r',     # Right Shift
                    56: 'alt_l',       # Left Alt
                    312: 'alt_r',      # Right Alt (56 + 256)
                    91: 'win_l',       # Left Win
                    92: 'win_r',       # Right Win
                }
            
            # Escape to cancel
            if key == Qt.Key.Key_Escape:
                self._capturing_hotkey = False
                self.releaseKeyboard()
                self.hotkey_btn.setText(tr('set_hotkey_btn'))
                self.hotkey_btn.setEnabled(True)
                return
            
            # Build key name
            key_name = None
            
            # Check for L/R modifiers via scan code first
            if scan_code in SCAN_CODES:
                key_name = SCAN_CODES[scan_code]
            # Fallback to generic modifiers
            elif key == Qt.Key.Key_Control:
                key_name = "ctrl"
            elif key == Qt.Key.Key_Alt:
                key_name = "alt"
            elif key == Qt.Key.Key_Shift:
                key_name = "shift"
            elif key == Qt.Key.Key_Meta:
                key_name = "win"
            # Special keys
            elif key == Qt.Key.Key_CapsLock:
                key_name = "caps_lock"
            elif key == Qt.Key.Key_Tab:
                key_name = "tab"
            elif key == Qt.Key.Key_Space:
                key_name = "space"
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                key_name = "enter"
            elif key == Qt.Key.Key_Backspace:
                key_name = "backspace"
            elif key == Qt.Key.Key_Delete:
                key_name = "delete"
            elif key == Qt.Key.Key_Insert:
                key_name = "insert"
            elif key == Qt.Key.Key_Home:
                key_name = "home"
            elif key == Qt.Key.Key_End:
                key_name = "end"
            elif key == Qt.Key.Key_PageUp:
                key_name = "page_up"
            elif key == Qt.Key.Key_PageDown:
                key_name = "page_down"
            elif key == Qt.Key.Key_Up:
                key_name = "up"
            elif key == Qt.Key.Key_Down:
                key_name = "down"
            elif key == Qt.Key.Key_Left:
                key_name = "left"
            elif key == Qt.Key.Key_Right:
                key_name = "right"
            elif key == Qt.Key.Key_Pause:
                key_name = "pause"
            elif key == Qt.Key.Key_Print:
                key_name = "print_screen"
            elif key == Qt.Key.Key_ScrollLock:
                key_name = "scroll_lock"
            elif key == Qt.Key.Key_NumLock:
                key_name = "num_lock"
            # Function keys F1-F24
            elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
                key_name = f"f{key - Qt.Key.Key_F1 + 1}"
            elif Qt.Key.Key_F13 <= key <= Qt.Key.Key_F24:
                key_name = f"f{key - Qt.Key.Key_F13 + 13}"
            # Regular keys A-Z
            elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                key_name = chr(key).lower()
            # Number keys 0-9
            elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
                key_name = chr(key)
            # Numpad keys
            elif scan_code == 82:   # Numpad 0
                key_name = "num_0"
            elif scan_code == 79:   # Numpad 1
                key_name = "num_1"
            elif scan_code == 80:   # Numpad 2
                key_name = "num_2"
            elif scan_code == 81:   # Numpad 3
                key_name = "num_3"
            elif scan_code == 75:   # Numpad 4
                key_name = "num_4"
            elif scan_code == 76:   # Numpad 5
                key_name = "num_5"
            elif scan_code == 77:   # Numpad 6
                key_name = "num_6"
            elif scan_code == 71:   # Numpad 7
                key_name = "num_7"
            elif scan_code == 72:   # Numpad 8
                key_name = "num_8"
            elif scan_code == 73:   # Numpad 9
                key_name = "num_9"
            elif scan_code == 83:   # Numpad .
                key_name = "num_decimal"
            elif scan_code == 309:  # Numpad /
                key_name = "num_divide"
            elif scan_code == 55:   # Numpad *
                key_name = "num_multiply"
            elif scan_code == 74:   # Numpad -
                key_name = "num_subtract"
            elif scan_code == 78:   # Numpad +
                key_name = "num_add"
            elif scan_code == 284:  # Numpad Enter
                key_name = "num_enter"
            # Symbols
            elif key == Qt.Key.Key_Minus:
                key_name = "minus"
            elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                key_name = "plus"
            elif key == Qt.Key.Key_BracketLeft:
                key_name = "["
            elif key == Qt.Key.Key_BracketRight:
                key_name = "]"
            elif key == Qt.Key.Key_Semicolon:
                key_name = ";"
            elif key == Qt.Key.Key_Apostrophe:
                key_name = "'"
            elif key == Qt.Key.Key_Comma:
                key_name = ","
            elif key == Qt.Key.Key_Period:
                key_name = "."
            elif key == Qt.Key.Key_Slash:
                key_name = "/"
            elif key == Qt.Key.Key_Backslash:
                key_name = "\\"
            elif key == Qt.Key.Key_QuoteLeft:
                key_name = "`"
            
            if key_name:
                # Check if it's a modifier key (single modifier hotkey)
                is_modifier = key_name in ('ctrl', 'alt', 'shift', 'win', 
                                          'ctrl_l', 'ctrl_r', 'alt_l', 'alt_r',
                                          'shift_l', 'shift_r', 'win_l', 'win_r')
                
                if is_modifier:
                    # Single modifier - just use the key name
                    full_hotkey = key_name
                else:
                    # Build combo with modifiers
                    parts = []
                    if modifiers & Qt.KeyboardModifier.ControlModifier:
                        parts.append("ctrl")
                    if modifiers & Qt.KeyboardModifier.AltModifier:
                        parts.append("alt")
                    if modifiers & Qt.KeyboardModifier.ShiftModifier:
                        parts.append("shift")
                    parts.append(key_name)
                    full_hotkey = "+".join(parts)
                
                old_hotkey = self.config_manager.hotkey
                self.config_manager.hotkey = full_hotkey
                self.hotkey_label.setText(tr('set_hotkey_current', key=full_hotkey))
                print(f"Hotkey saved: {full_hotkey} (scan_code: {scan_code})")
                
                # Always ask to restart since hotkey requires restart
                self._capturing_hotkey = False
                self.releaseKeyboard()
                self.hotkey_btn.setText(tr('set_hotkey_btn'))
                self.hotkey_btn.setEnabled(True)
                
                if old_hotkey != full_hotkey:
                    reply = QMessageBox.question(
                        self, 
                        tr('restart_title'),
                        tr('hotkey_changed_restart', key=full_hotkey),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self._request_restart()
                return
            
            # Unknown key - show scan code for debugging
            print(f"Unknown key: Qt.Key={key}, scan_code={scan_code}")
            self._capturing_hotkey = False
            self.releaseKeyboard()
            self.hotkey_btn.setText(tr('set_hotkey_btn'))
            self.hotkey_btn.setEnabled(True)
        else:
            super().keyPressEvent(event)

    def _request_restart(self):
        """Restarts the application (onefile-safe relaunch)."""
        import os
        import sys
        import subprocess
        from PySide6.QtWidgets import QApplication
        self.close()
        # See main.FlashcardApp.switch_user: strip _MEIPASS2 and drop argv[0] so the
        # onefile bootloader in the child doesn't fail to start.
        env = os.environ.copy()
        env.pop('_MEIPASS2', None)
        if getattr(sys, 'frozen', False):
            args = [sys.executable] + sys.argv[1:]
        else:
            args = [sys.executable] + sys.argv
        subprocess.Popen(args, env=env, close_fds=True)
        QApplication.instance().quit()


    def add_word(self):
        """Opens dialog to add a new word."""
        dialog = WordEditDialog(parent=self)
        if dialog.exec():
            english, uzbek = dialog.get_words()
            if english and uzbek:
                if self.vocabulary.add_word(english, uzbek):
                    self.load_vocabulary_data()
                else:
                    QMessageBox.warning(self, tr('dup_title'), tr('dup_msg', word=english))
            else:
                QMessageBox.warning(self, tr('err_title'), tr('err_both_fields'))

    def load_vocabulary_data(self):
        """Loads words into the table with mastery level icons."""
        self.table.setRowCount(0)
        words = self.vocabulary.get_all_words()
        self.table.setRowCount(len(words))

        mastery_icons = {
            'translation': '🌐',
            'definition': '📝',
            'synonym': '🔀',
        }

        for row, word_pair in enumerate(words):
            self.table.setItem(row, 0, QTableWidgetItem(word_pair['english']))
            self.table.setItem(row, 1, QTableWidgetItem(word_pair.get('uzbek', '')))

            level = self.stats_manager.get_mastery_level(word_pair)
            base_level = level.split('_')[0]
            icon = mastery_icons.get(base_level, '🌐')
            level_item = QTableWidgetItem(icon)
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, level_item)

    def load_stats_data(self):
        """Loads statistics into the stats table."""
        stats = self.stats_manager.get_all_stats()
        self.stats_table.setRowCount(len(stats))

        for row, (word, data) in enumerate(stats.items()):
            correct = data.get('correct', 0)
            incorrect = data.get('incorrect', 0)
            total = correct + incorrect
            success_rate = (correct / total * 100) if total > 0 else 0

            word_item = QTableWidgetItem(word)
            correct_item = QTableWidgetItem(str(correct))
            incorrect_item = QTableWidgetItem(str(incorrect))
            success_item = QTableWidgetItem(f"{success_rate:.0f}%")

            # Color code success rate
            if success_rate >= 80:
                success_item.setForeground(QColor("#2ecc71"))
            elif success_rate >= 50:
                success_item.setForeground(QColor("#f39c12"))
            else:
                success_item.setForeground(QColor("#e74c3c"))

            for item in [correct_item, incorrect_item, success_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.stats_table.setItem(row, 0, word_item)
            self.stats_table.setItem(row, 1, correct_item)
            self.stats_table.setItem(row, 2, incorrect_item)
            self.stats_table.setItem(row, 3, success_item)

        self.stats_table.sortByColumn(3, Qt.SortOrder.AscendingOrder)

    def edit_word(self):
        """Opens dialog to edit selected word."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, tr('err_title'), tr('err_select_edit'))
            return

        row = selected_rows[0].row()
        old_english = self.table.item(row, 0).text()
        old_uzbek = self.table.item(row, 1).text()

        dialog = WordEditDialog(english=old_english, uzbek=old_uzbek, parent=self)
        if dialog.exec():
            new_english, new_uzbek = dialog.get_words()
            if new_english and new_uzbek:
                if self.vocabulary.update_word(old_english, new_english, new_uzbek):
                    self.load_vocabulary_data()
                else:
                    QMessageBox.warning(self, tr('err_title'), tr('err_update_failed'))
            else:
                QMessageBox.warning(self, tr('err_title'), tr('err_both_fields'))

    def delete_selected_word(self):
        """Deletes the selected word."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, tr('err_title'), tr('err_select_delete'))
            return

        row = selected_rows[0].row()
        english_word = self.table.item(row, 0).text()

        reply = QMessageBox.question(
            self, tr('confirm_title'),
            tr('confirm_delete_word', word=english_word),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.vocabulary.delete_word(english_word):
                self.load_vocabulary_data()
                QMessageBox.information(self, tr('ok_done'), tr('word_deleted', word=english_word))

    def reset_all_stats(self):
        """Resets all statistics."""
        reply = QMessageBox.question(
            self, tr('reset_stats_title'),
            tr('reset_stats_confirm'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.stats_manager.reset_stats()
            self.load_stats_data()
            QMessageBox.information(self, tr('ok_done'), tr('stats_reset_done'))
