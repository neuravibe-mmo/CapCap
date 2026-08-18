import unittest
from app.i18n import (
    tr,
    set_language,
    get_current_language,
    get_available_languages,
    get_i18n_manager,
)


class TestI18nSystem(unittest.TestCase):

    def setUp(self):
        # Reset to default language 'en'
        set_language("en")

    def test_default_language_is_en(self):
        self.assertEqual(get_current_language(), "en")

    def test_translation_en(self):
        self.assertEqual(tr("workflow.prepare"), "Prepare")
        self.assertEqual(tr("workflow.status.completed"), "Completed")
        self.assertEqual(tr("common.ok"), "OK")

    def test_translation_vi(self):
        self.assertTrue(set_language("vi"))
        self.assertEqual(get_current_language(), "vi")
        self.assertEqual(tr("workflow.prepare"), "Chuẩn bị")
        self.assertEqual(tr("workflow.status.completed"), "Đã hoàn thành")
        self.assertEqual(tr("common.ok"), "Đồng ý")

    def test_available_languages(self):
        languages = get_available_languages()
        self.assertIn("en", languages)
        self.assertIn("vi", languages)

    def test_missing_key_fallback(self):
        set_language("vi")
        # Missing key should fallback to default parameter or key name
        self.assertEqual(tr("nonexistent.key", default="Fallback"), "Fallback")
        self.assertEqual(tr("nonexistent.key"), "nonexistent.key")

    def test_string_formatting(self):
        manager = get_i18n_manager()

        # Dynamically load a locale snippet with placeholders
        manager._translations["en"]["test_greeting"] = "Hello, {name}!"
        manager._translations["vi"]["test_greeting"] = "Xin chào, {name}!"

        set_language("en")
        self.assertEqual(tr("test_greeting", name="CapCap"), "Hello, CapCap!")

        set_language("vi")
        self.assertEqual(tr("test_greeting", name="CapCap"), "Xin chào, CapCap!")

    def test_language_changed_callback(self):
        received_languages = []

        def on_lang_changed(lang):
            received_languages.append(lang)

        manager = get_i18n_manager()
        manager.register_callback(on_lang_changed)

        set_language("en")
        set_language("vi")
        set_language("en")

        manager.unregister_callback(on_lang_changed)

        self.assertEqual(received_languages, ["vi", "en"])


if __name__ == "__main__":
    unittest.main()
