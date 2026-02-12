from deep_translator import GoogleTranslator

def translate_text(text: str, source_lang: str, target_lang: str = "en") -> str:
    return GoogleTranslator(source=source_lang, target=target_lang).translate(text)