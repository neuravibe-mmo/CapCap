import os
import sys

_workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QListView, QWidget, QStyledItemDelegate

from app.i18n import (
    get_available_languages,
    get_current_language,
    get_i18n_manager,
    set_language,
    tr,
)


class _LanguageItemDelegate(QStyledItemDelegate):
    """Custom item delegate to ensure proper item height in QListView dropdowns."""

    def __init__(self, item_height: int = 34, parent=None):
        super().__init__(parent)
        self.item_height = item_height

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(self.item_height)
        return size


class _PopupBelowComboBox(QComboBox):
    """Subclass QComboBox to force popup positioning strictly below the input box."""

    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        if popup:
            pos = self.mapToGlobal(self.rect().bottomLeft())
            popup.move(pos.x(), pos.y() + 4)
            if popup.width() < self.width():
                popup.setFixedWidth(self.width())


class LanguageSelectorWidget(QWidget):
    """
    A modern dropdown widget allowing users to select the application UI language.
    Automatically integrates with app.i18n manager and updates on change.
    """

    LANGUAGE_NAMES = {
        "en": "English",
        "vi": "Tiếng Việt",
    }

    LANGUAGE_FLAGS = {
        "en": "🇺🇸",
        "vi": "🇻🇳",
    }

    def __init__(self, parent=None, show_label: bool = True):
        super().__init__(parent)
        self.show_label = show_label
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        if self.show_label:
            self.label = QLabel()
            pixmap = self._create_translate_pixmap(18)
            if not pixmap.isNull():
                self.label.setPixmap(pixmap)
            self.label.setToolTip(tr("language.interface", default="UI Language:"))
            self._layout.addWidget(self.label)

        self.combo = _PopupBelowComboBox()
        self.combo.setFixedHeight(34)

        # Custom QListView for clean item rendering and dark theme styling
        list_view = QListView(self.combo)
        list_view.setItemDelegate(_LanguageItemDelegate(34, self.combo))
        list_view.setSpacing(3)
        list_view.setStyleSheet("""
            QListView {
                background-color: #132132;
                color: #e1e9f5;
                border: 1px solid #35506f;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListView::item {
                padding-left: 10px;
                padding-right: 10px;
                border-radius: 4px;
                color: #e1e9f5;
                font-size: 12px;
                font-weight: 600;
            }
            QListView::item:hover, QListView::item:selected {
                background-color: #1a3a5c;
                color: #4ecdc4;
            }
        """)
        self.combo.setView(list_view)

        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #1a2b3c;
                color: #e1e9f5;
                border: 1px solid #34506f;
                border-radius: 6px;
                padding: 4px 28px 4px 10px;
                font-size: 12px;
                font-weight: 600;
                min-width: 140px;
            }
            QComboBox:hover {
                border-color: #4ecdc4;
                background-color: #22374d;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: none;
            }
            QComboBox::down-arrow {
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='14' viewBox='0 0 10 14' fill='none'><path d='M5 1L9 5H1L5 1Z' fill='%238ad7ff'/><path d='M5 13L1 9H9L5 13Z' fill='%238ad7ff'/></svg>");
                width: 10px;
                height: 14px;
                margin-right: 6px;
            }
            QComboBox::down-arrow:hover {
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='14' viewBox='0 0 10 14' fill='none'><path d='M5 1L9 5H1L5 1Z' fill='%234ecdc4'/><path d='M5 13L1 9H9L5 13Z' fill='%234ecdc4'/></svg>");
            }
        """)

        self._populate_languages()
        self.combo.currentIndexChanged.connect(self._on_language_changed)
        self._layout.addWidget(self.combo)

        # Register callback with i18n manager for sync
        self._i18n_manager = get_i18n_manager()
        self._i18n_manager.register_callback(self._on_external_language_change)

    def _create_translate_pixmap(self, size: int = 18) -> QPixmap:
        icon_path = os.path.join(_workspace_root, "assets", "icons", "translate.svg")
        if os.path.exists(icon_path):
            renderer = QSvgRenderer(icon_path)
            if renderer.isValid():
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter, QRectF(0, 0, size, size))
                painter.end()
                return pixmap
        return QPixmap()

    def _populate_languages(self):
        self.combo.blockSignals(True)
        self.combo.clear()
        
        available = get_available_languages()
        current = get_current_language()
        
        selected_index = 0
        for idx, lang_code in enumerate(available):
            display_name = self.LANGUAGE_NAMES.get(lang_code, lang_code.upper())
            flag_icon = self.LANGUAGE_FLAGS.get(lang_code, "🌐")
            self.combo.addItem(f"{flag_icon} {display_name}", userData=lang_code)
            if lang_code == current:
                selected_index = idx

        self.combo.setCurrentIndex(selected_index)
        self.combo.blockSignals(False)

    def _on_language_changed(self, index: int):
        lang_code = self.combo.itemData(index)
        if lang_code:
            set_language(lang_code)

    def _on_external_language_change(self, lang_code: str):
        self.combo.blockSignals(True)
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == lang_code:
                self.combo.setCurrentIndex(i)
                break
        if self.show_label and hasattr(self, "label"):
            self.label.setToolTip(tr("language.interface", default="UI Language:"))
        self.combo.blockSignals(False)

    def retranslate_ui(self):
        """Update label tooltip when language changes."""
        if self.show_label and hasattr(self, "label"):
            self.label.setToolTip(tr("language.interface", default="UI Language:"))
