import json
import os
import threading
from typing import Any, Callable, Dict, List, Optional

try:
    from PySide6.QtCore import QObject, Signal
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False


class _I18nSignalEmitter(QObject if _QT_AVAILABLE else object):
    if _QT_AVAILABLE:
        language_changed = Signal(str)


class I18nManager:
    """Thread-safe Internationalization (i18n) Manager for CapCap."""

    _instance: Optional["I18nManager"] = None
    _instance_lock = threading.RLock()

    def __init__(self, locales_dir: Optional[str] = None, default_locale: str = "en"):
        self._lock = threading.RLock()
        self._default_locale = default_locale
        self._current_locale = default_locale
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._callbacks: List[Callable[[str], None]] = []
        
        if _QT_AVAILABLE:
            self.emitter = _I18nSignalEmitter()
        else:
            self.emitter = None

        if locales_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            locales_dir = os.path.join(base_dir, "locales")
        
        self.locales_dir = locales_dir
        self.load_all_locales()

    @classmethod
    def instance(cls, locales_dir: Optional[str] = None, default_locale: str = "en") -> "I18nManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(locales_dir=locales_dir, default_locale=default_locale)
            return cls._instance

    def load_all_locales(self) -> None:
        """Scan locales directory and load all JSON language dictionaries."""
        with self._lock:
            if not os.path.isdir(self.locales_dir):
                return

            for filename in os.listdir(self.locales_dir):
                if filename.endswith(".json"):
                    lang_code = os.path.splitext(filename)[0].lower()
                    filepath = os.path.join(self.locales_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            self._translations[lang_code] = json.load(f)
                    except Exception as e:
                        print(f"[i18n] Error loading locale '{filename}': {e}")

    def load_locale_file(self, lang_code: str, filepath: str) -> bool:
        """Load or merge custom locale file into specified language code."""
        with self._lock:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                lang = lang_code.lower()
                if lang not in self._translations:
                    self._translations[lang] = {}
                self._translations[lang].update(data)
                return True
            except Exception as e:
                print(f"[i18n] Failed to load locale file '{filepath}' for '{lang_code}': {e}")
                return False

    @property
    def current_locale(self) -> str:
        with self._lock:
            return self._current_locale

    def set_language(self, lang_code: str) -> bool:
        """Change current active language locale."""
        lang_code = lang_code.lower().strip()
        with self._lock:
            if lang_code == self._current_locale:
                return True
            
            if lang_code not in self._translations and lang_code != self._default_locale:
                # Try loading if file exists
                possible_path = os.path.join(self.locales_dir, f"{lang_code}.json")
                if os.path.exists(possible_path):
                    self.load_locale_file(lang_code, possible_path)
                else:
                    print(f"[i18n] Language locale '{lang_code}' not available.")
                    return False

            self._current_locale = lang_code

        # Notify subscribers outside lock to avoid deadlocks
        self._notify_language_changed(lang_code)
        return True

    def get_available_languages(self) -> List[str]:
        """Return list of loaded language codes (e.g. ['en', 'vi'])."""
        with self._lock:
            return sorted(list(self._translations.keys()))

    def register_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback function to be executed when language changes."""
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str], None]) -> None:
        """Unregister a language change callback function."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def _notify_language_changed(self, lang_code: str) -> None:
        if _QT_AVAILABLE and self.emitter:
            try:
                self.emitter.language_changed.emit(lang_code)
            except Exception as e:
                print(f"[i18n] Error emitting Qt language_changed signal: {e}")

        for cb in list(self._callbacks):
            try:
                cb(lang_code)
            except Exception as e:
                print(f"[i18n] Error executing callback: {e}")

    def _lookup_key(self, lang_data: Dict[str, Any], key: str) -> Optional[Any]:
        parts = key.split(".")
        current = lang_data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def translate(self, key: str, default: str = "", **kwargs) -> str:
        """
        Translate a dot-separated key (e.g., 'workflow.prepare').
        Supports string interpolation kwargs (e.g., tr('welcome', name='User')).
        Fallback order: Current Locale -> Default Locale -> default parameter -> key name.
        """
        with self._lock:
            result = None
            
            # 1. Search in current locale
            current_dict = self._translations.get(self._current_locale)
            if current_dict:
                result = self._lookup_key(current_dict, key)

            # 2. Fallback to default locale if not found
            if result is None and self._current_locale != self._default_locale:
                default_dict = self._translations.get(self._default_locale)
                if default_dict:
                    result = self._lookup_key(default_dict, key)

            # 3. Fallback to default arg or raw key
            if result is None:
                result = default if default != "" else key

            if not isinstance(result, str):
                result = str(result)

            # Format parameters if provided
            if kwargs and result:
                try:
                    result = result.format(**kwargs)
                except Exception as e:
                    print(f"[i18n] Error formatting string for key '{key}': {e}")

            return result
