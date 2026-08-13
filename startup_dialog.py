"""
Startup dialog for selecting user profile and initial setup.
"""

import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QFrame, QWidget, QTreeWidget, QTreeWidgetItem, QComboBox,
    QStyledItemDelegate, QStyle
)
from PySide6.QtCore import Qt, QSize, QRect, QEvent
from PySide6.QtGui import QFont, QColor

import profile_manager
from i18n import tr, set_language, get_language, LANGUAGES


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

QComboBox {
    background: #1e2235;
    border: 2px solid #2a2e45;
    border-radius: 10px;
    padding: 10px 14px;
    color: #fff;
    font-size: 15px;
}
QComboBox:focus { border: 2px solid #00d9ff; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox QAbstractItemView {
    background: #1e2235;
    border: 1px solid #2a2e45;
    color: #fff;
    selection-background-color: #1a4a5a;
    outline: none;
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


ADD_TOPIC_TABLE_STYLE = """
QTableWidget {
    background: #1e2235;
    border: 1px solid #2a2e45;
    border-radius: 10px;
    color: #eee;
    font-size: 14px;
    gridline-color: #454d76;
}
QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #353c5e;
}
QTableWidget::item:selected { background: #1a4a5a; }
/* The inline cell editor is a QLineEdit — override the big global padding so
   text isn't clipped inside the short row while typing. */
QTableWidget QLineEdit {
    padding: 4px 8px;
    margin: 0;
    min-height: 26px;
    border: 2px solid #00d9ff;
    border-radius: 0;
    background: #232842;
    color: #fff;
    font-size: 14px;
}
QHeaderView::section {
    background: #252a40;
    color: #9fb0c3;
    border: none;
    padding: 8px;
    font-weight: 600;
}
QComboBox {
    background: #1e2235;
    border: 2px solid #2a2e45;
    border-radius: 10px;
    padding: 10px 14px;
    color: #fff;
    font-size: 15px;
}
QComboBox:focus { border: 2px solid #00d9ff; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox QAbstractItemView {
    background: #1e2235;
    border: 1px solid #2a2e45;
    color: #fff;
    selection-background-color: #1a4a5a;
    outline: none;
}
QPushButton#segButton {
    background: #252a40;
    color: #9fb0c3;
    border: 1px solid #2a2e45;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#segButton:hover { background: #2a3050; }
QPushButton#segButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border-color: transparent;
}
"""


class _HelpIcon(QLabel):
    """A small '?' badge that explains a term on hover — for non-obvious fields."""

    def __init__(self, text, parent=None):
        super().__init__("?", parent)
        self.setToolTip(text)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setFixedSize(18, 18)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "QLabel { color:#00d9ff; border:1px solid #00d9ff; border-radius:9px; "
            "font-size:12px; font-weight:bold; background:transparent; }"
        )


class WordDetailsDialog(QDialog):
    """Per-word rich fields: definition, synonyms (added one by one), pattern."""

    def __init__(self, english="", data=None, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QListWidget
        data = data or {}
        self.setWindowTitle(tr('word_details'))
        self.setMinimumWidth(460)
        self.setStyleSheet(STARTUP_STYLE + ADD_TOPIC_TABLE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel(tr('word_details_of', word=english) if english else tr('word_details'))
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Definition
        layout.addLayout(self._field_header(tr('def_label'), tr('def_help')))
        self.definition_input = QLineEdit(data.get('definition') or '')
        self.definition_input.setPlaceholderText(tr('def_ph'))
        layout.addWidget(self.definition_input)

        # Synonyms — added one at a time
        layout.addLayout(self._field_header(tr('syn_label'), tr('syn_help')))
        syn_row = QHBoxLayout()
        self.syn_input = QLineEdit()
        self.syn_input.setPlaceholderText(tr('syn_ph'))
        self.syn_input.returnPressed.connect(self._add_synonym)
        add_syn = QPushButton("＋")
        add_syn.setObjectName("secondaryButton")
        add_syn.setFixedWidth(52)
        add_syn.clicked.connect(self._add_synonym)
        syn_row.addWidget(self.syn_input)
        syn_row.addWidget(add_syn)
        layout.addLayout(syn_row)
        self.syn_list = QListWidget()
        self.syn_list.setMaximumHeight(120)
        for s in (data.get('synonyms') or []):
            self.syn_list.addItem(s)
        self.syn_list.itemDoubleClicked.connect(
            lambda it: self.syn_list.takeItem(self.syn_list.row(it)))
        layout.addWidget(self.syn_list)
        syn_hint = QLabel(tr('syn_remove_hint'))
        syn_hint.setObjectName("subtitleLabel")
        layout.addWidget(syn_hint)

        # Pattern
        layout.addLayout(self._field_header(tr('pat_label'), tr('pat_help')))
        self.pattern_input = QLineEdit(data.get('grammar_pattern') or '')
        self.pattern_input.setPlaceholderText(tr('pat_ph'))
        layout.addWidget(self.pattern_input)

        btns = QHBoxLayout()
        cancel = QPushButton(tr('cancel'))
        cancel.setObjectName("secondaryButton")
        cancel.clicked.connect(self.reject)
        ok = QPushButton(tr('ok_done'))
        ok.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addStretch()
        btns.addWidget(ok)
        layout.addLayout(btns)

    def _field_header(self, label_text, help_text):
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(QLabel(label_text))
        row.addWidget(_HelpIcon(help_text))
        row.addStretch()
        return row

    def _add_synonym(self):
        text = self.syn_input.text().strip()
        if text:
            self.syn_list.addItem(text)
            self.syn_input.clear()
        self.syn_input.setFocus()

    def get_data(self):
        synonyms = [self.syn_list.item(i).text() for i in range(self.syn_list.count())]
        return {
            'definition': self.definition_input.text().strip(),
            'synonyms': synonyms,
            'grammar_pattern': self.pattern_input.text().strip(),
        }


class AddTopicDialog(QDialog):
    """Create a new topic and add words to it — reachable from the main menu."""

    def __init__(self, vocabulary, parent=None):
        super().__init__(parent)
        self.vocabulary = vocabulary
        self.setWindowTitle(tr('new_topic_title'))
        self.setMinimumSize(620, 580)
        self.setStyleSheet(STARTUP_STYLE + ADD_TOPIC_TABLE_STYLE)
        self._build_ui()

    def _build_ui(self):
        from PySide6.QtWidgets import QTableWidget, QHeaderView, QComboBox, QTableWidgetItem

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel(tr('new_topic_title'))
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel(tr('topic_name')))
        # Editable combo: pick an existing topic to EXTEND it, or type a new name.
        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)
        self.name_combo.addItems(self.vocabulary.get_all_topics())
        self.name_combo.setCurrentIndex(-1)
        self.name_combo.lineEdit().setPlaceholderText(tr('topic_name_ph'))
        layout.addWidget(self.name_combo)

        last_topic = self._last_topic()
        if last_topic:
            last_label = QLabel(tr('last_topic', topic=last_topic))
            last_label.setObjectName("subtitleLabel")
            last_label.setWordWrap(True)
            layout.addWidget(last_label)

        tip = QLabel(tr('addtopic_tip'))
        tip.setObjectName("subtitleLabel")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        self.table = QTableWidget(6, 4)
        self.table.setHorizontalHeaderLabels([tr('col_english') if False else "English", tr('col_translation'), tr('col_hint'), "✎"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(3, 52)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        for r in range(self.table.rowCount()):
            self._add_details_button(r)
        layout.addWidget(self.table)

        row_btns = QHBoxLayout()
        add_row = QPushButton(tr('btn_add_row'))
        add_row.setObjectName("secondaryButton")
        add_row.clicked.connect(self._add_row)
        del_row = QPushButton(tr('btn_del_row'))
        del_row.setObjectName("secondaryButton")
        del_row.clicked.connect(self._delete_row)
        row_btns.addWidget(add_row)
        row_btns.addWidget(del_row)
        row_btns.addStretch()
        layout.addLayout(row_btns)

        actions = QHBoxLayout()
        cancel = QPushButton(tr('cancel'))
        cancel.setObjectName("secondaryButton")
        cancel.clicked.connect(self.reject)
        save = QPushButton(tr('save'))
        save.clicked.connect(self._save)
        actions.addWidget(cancel)
        actions.addStretch()
        actions.addWidget(save)
        layout.addLayout(actions)

    def _delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self._add_details_button(r)

    def _add_details_button(self, row):
        btn = QPushButton("✎")
        btn.setObjectName("secondaryButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tr('details_tooltip'))
        btn.clicked.connect(self._open_details)
        self.table.setCellWidget(row, 3, btn)

    def _open_details(self):
        from PySide6.QtWidgets import QTableWidgetItem
        btn = self.sender()
        row = next((r for r in range(self.table.rowCount())
                    if self.table.cellWidget(r, 3) is btn), -1)
        if row < 0:
            return
        eng_item = self.table.item(row, 0)
        english = eng_item.text().strip() if eng_item else ""
        data = eng_item.data(Qt.ItemDataRole.UserRole) if eng_item else None
        dlg = WordDetailsDialog(english, data, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            details = dlg.get_data()
            if eng_item is None:
                eng_item = QTableWidgetItem("")
                self.table.setItem(row, 0, eng_item)
            eng_item.setData(Qt.ItemDataRole.UserRole, details)
            has_extra = any([details['definition'], details['synonyms'],
                             details['grammar_pattern']])
            btn.setText("✎ ✓" if has_extra else "✎")

    def _last_topic(self):
        """The category of the most recently added word, for quick reference."""
        for word in reversed(self.vocabulary.get_all_words()):
            cat = (word.get('category') or '').strip()
            if cat:
                return cat
        return None

    def _save(self):
        name = self.name_combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, tr('err_title'), tr('err_enter_topic'))
            return
        pairs = []
        for r in range(self.table.rowCount()):
            def cell(c):
                item = self.table.item(r, c)
                return item.text().strip() if item else ""
            english = cell(0)
            if not english:
                continue
            row = {"english": english, "uzbek": cell(1), "hint": cell(2)}
            eng_item = self.table.item(r, 0)
            details = eng_item.data(Qt.ItemDataRole.UserRole) if eng_item else None
            if details:
                row["definition"] = details.get('definition') or ''
                row["synonyms"] = details.get('synonyms') or []
                row["grammar_pattern"] = details.get('grammar_pattern') or ''
            pairs.append(row)
        if not pairs:
            QMessageBox.warning(self, tr('err_title'), tr('err_add_one_word'))
            return
        added = self.vocabulary.add_words_to_topic(name, pairs)
        if added:
            QMessageBox.information(self, tr('ok_done'), tr('words_added', added=added, name=name))
        else:
            QMessageBox.information(self, tr('ok_done'), tr('no_new_words'))
        self.accept()


class ProfileItemDelegate(QStyledItemDelegate):
    """Renders profile rows natively (so text and selection just work) and paints a
    trash icon on the right of each row. A click inside that icon's area deletes the
    profile. This avoids setItemWidget's pitfalls (collapsed rows, clicks that don't
    select the item)."""

    ICON_W = 36

    def __init__(self, owner):
        super().__init__(owner)
        self._owner = owner

    def _icon_rect(self, option):
        r = option.rect
        return QRect(r.right() - self.ICON_W, r.top(), self.ICON_W, r.height())

    def paint(self, painter, option, index):
        super().paint(painter, option, index)  # native text + selection highlight
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        painter.save()
        painter.setPen(QColor("#ff6b81") if hovered else QColor("#b7808c"))
        painter.drawText(self._icon_rect(option), Qt.AlignmentFlag.AlignCenter, "🗑")
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            if self._icon_rect(option).contains(event.position().toPoint()):
                name = index.data(Qt.ItemDataRole.UserRole)
                if name:
                    self._owner._delete_profile_by_name(name)
                return True
        return super().editorEvent(event, model, option, index)


class StartupDialog(QDialog):
    """Dialog for selecting or creating a user profile at startup."""

    RESTART_CODE = 100  # exec() returns this when the language was changed

    def __init__(self, vocabulary=None, parent=None):
        super().__init__(parent)
        self.vocabulary = vocabulary
        self.selected_username = None
        self.selected_topics = []

        self.setWindowTitle("Smart Flashcards")
        self.setMinimumSize(500, 420)
        self.setStyleSheet(STARTUP_STYLE)

        self.init_ui()
        self.load_profiles()

    def _on_language_changed(self, index):
        code = self.lang_combo.itemData(index)
        if code and code != get_language():
            set_language(code)
            self.done(self.RESTART_CODE)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)

        # Header: the welcome text and the language selector sit on the SAME row —
        # the selector is bottom-aligned to the subtitle, so the top doesn't waste a
        # whole extra row on the language picker.
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        welcome_box = QVBoxLayout()
        welcome_box.setSpacing(2)
        title = QLabel(tr('welcome_title'))
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_box.addWidget(title)
        subtitle = QLabel(tr('welcome_subtitle'))
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_box.addWidget(subtitle)

        self.lang_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        codes = list(LANGUAGES.keys())
        self.lang_combo.setCurrentIndex(codes.index(get_language()) if get_language() in codes else 0)
        self.lang_combo.setFixedWidth(140)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_lbl = QLabel(f"🌍 {tr('language')}:")
        lang_lbl.setStyleSheet("color:#cfd6e6; font-size:14px; background:transparent;")
        lang_widget = QWidget()
        lang_box = QHBoxLayout(lang_widget)
        lang_box.setContentsMargins(0, 0, 0, 0)
        lang_box.setSpacing(6)
        lang_box.addWidget(lang_lbl)
        lang_box.addWidget(self.lang_combo)

        # Left spacer the same width as the language box, so the welcome text stays
        # centred in the dialog instead of being pushed left by the selector.
        left_spacer = QWidget()
        left_spacer.setFixedWidth(max(lang_widget.sizeHint().width(), 160))
        header_row.addWidget(left_spacer)
        header_row.addStretch(1)
        header_row.addLayout(welcome_box)
        header_row.addStretch(1)
        header_row.addWidget(lang_widget, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(header_row)

        # Profile list. Its height is fitted to the number of profiles (see
        # _fit_profile_list_height) so 2 profiles don't get a scrollbar while 1 topic
        # leaves a huge gap — the two areas stay visually balanced.
        self.profile_list = QListWidget()
        self.profile_list.setMouseTracking(True)  # so the trash icon highlights on hover
        self.profile_list.setItemDelegate(ProfileItemDelegate(self))
        self.profile_list.itemDoubleClicked.connect(self.select_and_continue)
        self.profile_list.currentItemChanged.connect(self._on_profile_selection_changed)
        layout.addWidget(self.profile_list)

        # New profile section
        new_profile_frame = QFrame()
        new_profile_frame.setObjectName("card")
        new_profile_layout = QVBoxLayout(new_profile_frame)
        new_profile_layout.setSpacing(12)
        
        new_label = QLabel(tr('new_profile'))
        new_label.setObjectName("titleLabel")
        new_label.setFont(QFont("Segoe UI", 14))
        new_profile_layout.addWidget(new_label)

        input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr('enter_name'))
        self.name_input.returnPressed.connect(self.create_new_profile)
        input_layout.addWidget(self.name_input)

        create_btn = QPushButton(tr('create'))
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
            
            topics_header = QHBoxLayout()
            topics_label = QLabel(tr('choose_topics'))
            topics_label.setObjectName("titleLabel")
            topics_label.setFont(QFont("Segoe UI", 14))
            topics_header.addWidget(topics_label)
            topics_header.addStretch()
            add_topic_btn = QPushButton(tr('add_topic'))
            add_topic_btn.setObjectName("secondaryButton")
            add_topic_btn.clicked.connect(self.open_add_topic_dialog)
            topics_header.addWidget(add_topic_btn)
            topics_layout.addLayout(topics_header)

            self.topics_tree = QTreeWidget()
            self.topics_tree.setHeaderHidden(True)
            self.topics_tree.setRootIsDecorated(True)
            self.topics_tree.setAnimated(True)
            self.topics_tree.setIndentation(24)
            self.topics_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.topics_tree.itemChanged.connect(self._on_topic_item_changed)
            # Adaptive height (like the profile list): grow to the visible rows up to a
            # cap, then scroll. Re-fit when groups expand/collapse.
            self.topics_tree.itemExpanded.connect(self._fit_topics_tree_height)
            self.topics_tree.itemCollapsed.connect(self._fit_topics_tree_height)

            self._build_topics_tree()

            topics_layout.addWidget(self.topics_tree)

            self.empty_topics_label = QLabel(tr('empty_topics'))
            self.empty_topics_label.setObjectName("subtitleLabel")
            self.empty_topics_label.setWordWrap(True)
            topics_layout.addWidget(self.empty_topics_label)

            self._update_empty_state()
            layout.addWidget(topics_frame)

        # Study mode selector
        mode_frame = QFrame()
        mode_frame.setObjectName("card")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setSpacing(12)

        mode_label = QLabel(tr('study_mode'))
        mode_label.setObjectName("titleLabel")
        mode_label.setFont(QFont("Segoe UI", 14))
        mode_layout.addWidget(mode_label)

        self.study_mode_combo = QComboBox()
        self.study_mode_options = {
            'adaptive': tr('mode_adaptive'),
            'translation': tr('mode_translation'),
            'definition': tr('mode_definition'),
            'synonym': tr('mode_synonym'),
        }
        for key, label in self.study_mode_options.items():
            self.study_mode_combo.addItem(label, key)
        mode_layout.addWidget(self.study_mode_combo)
        layout.addWidget(mode_frame)

        # Continue button
        continue_btn = QPushButton(tr('continue'))
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
            parent.setText(0, f"📁 {group_name} ({tr('words_n', n=total_words)})")
            parent.setFlags(
                parent.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsAutoTristate
            )
            parent.setCheckState(0, Qt.CheckState.Checked)
            parent.setExpanded(False)

            # Create child items for each sub-category
            for cat in categories:
                word_count = self.vocabulary.get_word_count_for_topic(cat)
                # Extract the range part from "SAT Vocabulary (1-15)" → "1-15"
                match = re.match(r'^.+?\s*\((.+)\)$', cat)
                display_name = match.group(1) if match else cat

                child = QTreeWidgetItem(parent)
                child.setText(0, f"{display_name} ({tr('words_n', n=word_count)})")
                child.setFlags(
                    child.flags() | Qt.ItemFlag.ItemIsUserCheckable
                )
                child.setCheckState(0, Qt.CheckState.Checked)
                child.setData(0, Qt.ItemDataRole.UserRole, cat)  # Store full category name
                self._topic_items[cat] = child

        self.topics_tree.blockSignals(False)
        self._update_empty_state()
        self._fit_topics_tree_height()

    def _update_empty_state(self):
        """Shows guidance instead of an empty tree when there are no topics yet."""
        if not hasattr(self, 'empty_topics_label'):
            return
        has_topics = self.topics_tree.topLevelItemCount() > 0
        self.topics_tree.setVisible(has_topics)
        self.empty_topics_label.setVisible(not has_topics)

    def open_add_topic_dialog(self):
        """Opens the 'new topic' dialog and refreshes the tree on success."""
        if not self.vocabulary:
            return
        dialog = AddTopicDialog(self.vocabulary, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._build_topics_tree()

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
    
    def _fit_profile_list_height(self):
        """Sizes the profile list to its contents (up to 5 rows) so a couple of
        profiles fit without a scrollbar, and only long lists scroll."""
        count = self.profile_list.count()
        row_h = self.profile_list.sizeHintForRow(0) if count else 0
        if row_h <= 0:
            row_h = 40  # sensible fallback before rows are measured
        visible = min(max(count, 1), 5)
        frame = 2 * self.profile_list.frameWidth() + 6
        self.profile_list.setFixedHeight(row_h * visible + frame)

    def _fit_topics_tree_height(self, *args):
        """Size the topics tree to its visible rows (up to a cap), then scroll —
        adaptive like the profile list, so it neither crowds the profiles nor leaves
        a big empty gap. Recomputed when groups expand/collapse."""
        if not hasattr(self, 'topics_tree'):
            return
        rows = self.topics_tree.topLevelItemCount()
        if rows == 0:
            return
        for i in range(self.topics_tree.topLevelItemCount()):
            it = self.topics_tree.topLevelItem(i)
            if it.isExpanded():
                rows += it.childCount()
        # sizeHintForRow under-reports before the widget is shown (it misses the
        # stylesheet padding), which squashed the tree to ~3 rows. Floor it to a
        # realistic per-row height so the cap actually shows ~6 rows.
        row_h = max(self.topics_tree.sizeHintForRow(0),
                    self.topics_tree.fontMetrics().height() + 16)
        visible = min(max(rows, 3), 6)  # show 3..6 rows, then scroll inside the tree
        frame = 2 * self.topics_tree.frameWidth() + 8
        self.topics_tree.setFixedHeight(row_h * visible + frame)

    def _delete_profile_by_name(self, name):
        """Deletes a profile (invoked from its row's trash button) after confirmation."""
        reply = QMessageBox.question(
            self, tr('confirm_title'), tr('del_profile_confirm', name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            profile_manager.delete_profile(name)
            self.load_profiles()

    def load_profiles(self):
        """Loads existing profiles. Rows render natively (reliable text + selection);
        the per-row trash icon is drawn by ProfileItemDelegate."""
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

        self._fit_profile_list_height()
    
    def create_new_profile(self):
        """Creates a new profile and selects it."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, tr('err_title'), tr('err_enter_name'))
            return

        if profile_manager.profile_exists(name):
            QMessageBox.warning(self, tr('err_title'), tr('err_profile_exists', name=name))
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
            QMessageBox.warning(self, tr('err_title'), tr('err_select_profile'))
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
    
    def _on_profile_selection_changed(self, current, previous):
        """Loads and updates active topics for the selected profile."""
        if not current:
            return
        username = current.data(Qt.ItemDataRole.UserRole)
        
        # Load user config
        user_profile_path = profile_manager.get_profile_path(username)
        config_path = user_profile_path / 'config.json'
        
        import json
        active_topics = None
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    active_topics = config.get('active_topics')
            except Exception:
                pass

        # Update check states in tree
        self.topics_tree.blockSignals(True)
        for cat, item in self._topic_items.items():
            is_checked = (cat in active_topics) if active_topics is not None else True
            item.setCheckState(0, Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
            
        # Update parent states
        for i in range(self.topics_tree.topLevelItemCount()):
            parent = self.topics_tree.topLevelItem(i)
            checked = 0
            for j in range(parent.childCount()):
                if parent.child(j).checkState(0) == Qt.CheckState.Checked:
                    checked += 1
            if checked == parent.childCount():
                parent.setCheckState(0, Qt.CheckState.Checked)
            elif checked == 0:
                parent.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
                
        self.topics_tree.blockSignals(False)

    def get_result(self):
        """Returns the selected username, topics, and study mode."""
        study_mode = 'adaptive'
        if hasattr(self, 'study_mode_combo'):
            study_mode = self.study_mode_combo.currentData() or 'adaptive'
        return self.selected_username, self.selected_topics, study_mode
