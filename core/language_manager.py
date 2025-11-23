                          
import json
import os

_language_manager = None


class LanguageManager:
    def __init__(self, lang="es"):
        self.current_lang = lang
        self.data = {}
        self.fallback = {}

        self.available_langs = self._scan_languages()
        self._load_fallback()
        self.load(lang)

    def _scan_languages(self):
        base = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(base, "..", "i18n")

        langs = []
        for f in os.listdir(folder):
            if f.endswith(".json"):
                langs.append(f[:-5])                 
        return sorted(langs)

    def _load_fallback(self):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "..", "i18n", "es.json")
        with open(path, "r", encoding="utf-8") as f:
            self.fallback = json.load(f)

    def load(self, lang):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "..", "i18n", f"{lang}.json")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing language file: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.current_lang = lang

    def tr(self, key):
        if key in self.data:
            return self.data[key]
        if key in self.fallback:
            return self.fallback[key]
        return key


def init_language(lang="es"):
    global _language_manager
    _language_manager = LanguageManager(lang)


def tr(key):
    global _language_manager
    if _language_manager is None:
        init_language("es")
    return _language_manager.tr(key)
