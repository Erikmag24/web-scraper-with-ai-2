# translator.py
from deep_translator import GoogleTranslator

def translate_text(text, languages):
    """
    Translate the given text into specified languages.

    :param text: Text to be translated.
    :param languages: List of language codes to translate into.
    :return: Dictionary with translations.
    """
    translations = {}
    for lang in languages:
        translated = GoogleTranslator(source='auto', target=lang).translate(text)
        translations[lang] = translated
    return translations

def get_available_languages():
    """
    Retrieves all available languages for translation as a dictionary.
    """
    translator = GoogleTranslator()
    languages = translator.get_supported_languages()
    return {lang: lang.title() for lang in languages}