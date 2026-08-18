"""
Internationalization (i18n) package for CapCap.
"""

from typing import List
from app.i18n.manager import I18nManager


def get_i18n_manager() -> I18nManager:
    """Return the global I18nManager instance."""
    return I18nManager.instance()


def tr(key: str, default: str = "", **kwargs) -> str:
    """
    Translate a string key using current active locale.
    Example:
        tr("workflow.prepare") -> "Prepare" (or "Chuẩn bị")
        tr("greeting", name="User") -> "Hello, User!"
    """
    return get_i18n_manager().translate(key, default=default, **kwargs)


def set_language(lang_code: str) -> bool:
    """Set active language locale (e.g. 'en', 'vi')."""
    return get_i18n_manager().set_language(lang_code)


def get_current_language() -> str:
    """Get active language code."""
    return get_i18n_manager().current_locale


def get_available_languages() -> List[str]:
    """Get list of loaded language codes."""
    return get_i18n_manager().get_available_languages()


__all__ = [
    "I18nManager",
    "get_i18n_manager",
    "tr",
    "set_language",
    "get_current_language",
    "get_available_languages",
]
