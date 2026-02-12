"""Run a quick non-GUI demo of the FAQ pipeline.

This script runs language detection, optional translation, semantic search,
and translation of the answer back to the user's language for two sample
questions (one Arabic, one English).
"""
from detect_lang import detect_language
from translate import translate_text
from semantic_search import load_faq_data, search_faq


def run_question(q: str):
    print("\nQuestion:", q)
    detected = detect_language(q)
    print("Detected language:", detected)

    if detected != "en":
        translated_q = translate_text(q, detected, "en")
        print("Translated to EN:", translated_q)
    else:
        translated_q = q

    faq_data, faq_embeddings = load_faq_data()
    result = search_faq(faq_data, faq_embeddings, translated_q)

    answer_en = result["answer"]
    score = result.get("score", 0.0)

    if detected != "en":
        final_answer = translate_text(answer_en, "en", detected)
    else:
        final_answer = answer_en

    print("Matched question (EN):", result["question"])
    print("Answer to user:", final_answer)
    print(f"Score: {score:.4f}")


def main():
    samples = [
        "ما هي مواعيد عملكم؟",
        "How do I reset my password?",
    ]

    for s in samples:
        run_question(s)


if __name__ == "__main__":
    main()
