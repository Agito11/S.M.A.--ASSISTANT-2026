import threading
import tkinter as tk
from tkinter import ttk, messagebox

from detect_lang import detect_language
from translate import translate_text
from semantic_search import load_faq_data, search_faq


class ChatGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FAQ AI — Chat")
        self.geometry("720x600")
        self.configure(bg="#ececec")

        self._build_ui()

        self.faq_data = None
        self.faq_embeddings = None
        threading.Thread(target=self._load_data_bg, daemon=True).start()

    def _build_ui(self):
        header = tk.Frame(self, bg="#075e54", height=60)
        header.pack(fill="x")
        tk.Label(header, text="FAQ Assistant", bg="#075e54", fg="white", font=(None, 16, "bold")).pack(padx=12, pady=12, anchor="w")

        # Chat area (scrollable)
        container = tk.Frame(self, bg="#ececec")
        container.pack(fill="both", expand=True, padx=12, pady=(8,6))

        self.canvas = tk.Canvas(container, bg="#ececec", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ececec")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Input area
        input_frame = tk.Frame(self, bg="#f0f0f0", height=70)
        input_frame.pack(fill="x", padx=12, pady=(0,12))

        self.entry = tk.Text(input_frame, height=2, wrap=tk.WORD, font=(None, 12))
        self.entry.pack(side="left", fill="x", expand=True, padx=(8,6), pady=8)
        self.entry.bind("<Return>", self._on_enter_pressed)

        send_btn = tk.Button(input_frame, text="Send", bg="#25D366", fg="white", font=(None, 11, "bold"), command=self.on_send)
        send_btn.pack(side="right", padx=6, pady=8)
        self.send_btn = send_btn

        # initial bot welcome
        self.after(300, lambda: self._add_bot_message("مرحبا! اسألني أي سؤال من الأسئلة الشائعة."))

    def _load_data_bg(self):
        try:
            self.faq_data, self.faq_embeddings = load_faq_data()
        except Exception as e:
            print("Failed to load FAQ data:", e)

    def _on_enter_pressed(self, event):
        # Prevent newline insertion on Enter; use Shift+Enter for newline
        if event.state & 0x0001:  # Shift pressed
            return
        self.on_send()
        return "break"

    def on_send(self):
        raw = self.entry.get("1.0", tk.END).strip()
        if not raw:
            return
        self.entry.delete("1.0", tk.END)
        self._add_user_message(raw)
        # show typing indicator
        typing_widget = self._add_bot_message("...")
        self.send_btn.config(state="disabled")
        threading.Thread(target=self._process_question, args=(raw, typing_widget), daemon=True).start()

    def _process_question(self, question: str, typing_widget):
        try:
            # 1. اكتشاف اللغة
            detected = detect_language(question)
            
            # --- بداية التعديل (FIX) ---
            # طباعة اللغة المكتشفة في التيرمينال لمساعدتك في التصحيح
            print(f"DEBUG: Input='{question}' -> Detected Language='{detected}'")

            # إصلاح المشكلة: إذا كانت الكلمة ترحيباً شائعاً بالإنجليزية، نثبت اللغة على 'en'
            # لأن المكتبات أحياناً تظن أن 'hello' كلمة بلغة أخرى
            common_greetings = ["hello", "hi", "hey", "thanks", "thank you"]
            if question.lower().strip() in common_greetings:
                detected = "en"
            
            # (اختياري) إذا كان النص قصيراً جداً ويحتوي حروف إنجليزية فقط، نعتبره إنجليزية لتجنب الخطأ
            if len(question) < 5 and question.isascii():
                detected = "en"
            # --- نهاية التعديل ---

            if detected != "en":
                translated_q = translate_text(question, detected, "en")
            else:
                translated_q = question

            if self.faq_data is None:
                self.faq_data, self.faq_embeddings = load_faq_data()

            result = search_faq(self.faq_data, self.faq_embeddings, translated_q)
            answer_en = result.get("answer", "")
            score = result.get("score", 0.0)

            # إذا كانت لغة المستخدم ليست الإنجليزية، نترجم الرد له
            if detected != "en":
                final_answer = translate_text(answer_en, "en", detected)
            else:
                final_answer = answer_en

            # replace typing indicator with actual answer
            self._replace_bot_message(typing_widget, final_answer)
        except Exception as exc:
            print(f"Error: {exc}") # طباعة الخطأ في التيرمينال
            self._replace_bot_message(typing_widget, "حدث خطأ: " + str(exc))
        finally:
            self.send_btn.config(state="normal")
            # scroll to bottom
            self.canvas.yview_moveto(1.0)
            
    def _add_user_message(self, text: str):
        frame = tk.Frame(self.scrollable_frame, bg="#ececec")
        bubble = tk.Label(frame, text=text, bg="#dcf8c6", justify="left", wraplength=420, font=(None, 11), padx=8, pady=6)
        bubble.pack(anchor="e")
        frame.pack(fill="x", pady=6, padx=10)
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _add_bot_message(self, text: str):
        frame = tk.Frame(self.scrollable_frame, bg="#ececec")
        bubble = tk.Label(frame, text=text, bg="#ffffff", justify="left", wraplength=420, font=(None, 11), padx=8, pady=6)
        bubble.pack(anchor="w")
        frame.pack(fill="x", pady=6, padx=10)
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        return bubble  # return widget so we can replace its text later

    def _replace_bot_message(self, widget, text: str):
        try:
            widget.config(text=text)
        except Exception:
            pass


def main():
    app = ChatGUI()
    app.mainloop()


if __name__ == "__main__":
    main()