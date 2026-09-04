import logging
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

def translate_strings(texts: list[str], target_language: str) -> list[str]:
    """
    Translates a list of strings to the target language using Google Translate API (free).
    Returns the translated strings in the same order.
    """
    if not texts or not target_language or target_language.startswith('en'):
        return texts
        
    try:
        # Handle cases like 'hi-IN' by taking the prefix
        lang_code = target_language.split('-')[0]
        translator = GoogleTranslator(source='en', target=lang_code)
        
        # Join all strings with a unique delimiter to make only ONE request
        # This prevents Google from rate-limiting or blocking the scraper
        delimiter = " ||| "
        joined_text = delimiter.join(texts)
        
        translated_joined = translator.translate(joined_text)
        if not translated_joined:
            return texts
            
        # Split back by delimiter
        translated_parts = [p.strip() for p in translated_joined.split("|||")]
        
        # In rare cases, Google might mess up the delimiter count. If so, fallback to individual strings
        if len(translated_parts) != len(texts):
            logger.warning("Delimiter count mismatch. Falling back to individual translation.")
            translated_parts = []
            for text in texts:
                try:
                    res = translator.translate(text)
                    translated_parts.append(res if res else text)
                except Exception:
                    translated_parts.append(text)
                    
        return translated_parts
            
    except Exception as e:
        logger.error(f"Translation setup error: {e}")
        return texts # Fallback to original
