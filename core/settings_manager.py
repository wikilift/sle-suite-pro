import os
import json
from core.language_manager import LanguageManager


def _get_settings_path():
    if os.name == "nt":
        base = os.path.join(os.getenv("APPDATA"), "sle_suite")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config", "sle_suite")

    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "settings.json")


class SettingsManager:
    def __init__(self):
        self.path = _get_settings_path()

        self.data = {
            "theme": "dark",
            "language": "es",
            "accent_color": "#00aaff",
            "reader_preference": None,
        }
        self.load()
        self.lang_manager = LanguageManager(self.data["language"])
        self.available_langs = self.lang_manager.available_langs
        self.validate()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k in self.data:
                    if k in loaded:
                        self.data[k] = loaded[k]
            except Exception:
                print("Settings corruptos, usando defaults.")

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def validate(self):
        if self.data.get("theme") not in ("dark", "light"):
            self.data["theme"] = "dark"

        if self.data.get("language") not in self.available_langs:
            self.data["language"] = "es"

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def apply_theme(self, window):
        from gui.themes import THEMES
        theme = self.get("theme", "dark")
        window.setStyleSheet(THEMES.get(theme, THEMES["dark"]))