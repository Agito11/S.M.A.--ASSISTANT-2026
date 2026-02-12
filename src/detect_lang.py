
from langdetect import detect

def detect_language(text):
    try:
        language = detect(text)
        return language
    except:
        return "unknown"

if __name__ == "__main__":
    test_text = input("Enter a sentence: ")
    lang = detect_language(test_text)
    print(f"Detected language: {lang}")