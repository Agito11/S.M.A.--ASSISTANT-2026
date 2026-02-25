import threading
import customtkinter as ctk
import time

# استيراد ملفات مشروعك
from detect_lang import detect_language
from translate import translate_text
from semantic_search import load_faq_data, search_faq

# --- إعدادات التصميم العام ---
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("green")

class ModernChatGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # إعداد النافذة
        self.title("AI Powered Business Chat Assistant")
        self.geometry("1000x750")
        
        # الشبكة
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  
        self.grid_rowconfigure(2, weight=0)  

        self.faq_data = None
        self.faq_embeddings = None
        
        self._build_ui()
        
        # تحميل البيانات في الخلفية
        threading.Thread(target=self._load_data_bg, daemon=True).start()

    def _build_ui(self):
        # 1. الهيدر
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#00796B")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.header_label = ctk.CTkLabel(
            self.header_frame, 
            text="S.M.A. AI Assistant", 
            font=("Segoe UI", 22, "bold"),
            text_color="white"
        )
        self.header_label.pack(side="left", padx=25, pady=15)

        # زر التبديل (Dark Mode)
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame, 
            text="Dark Mode", 
            command=self.toggle_theme,
            font=("Segoe UI", 12, "bold"),
            text_color="white",
            progress_color="white",
            onvalue="Dark", 
            offvalue="Light"
        )
        self.theme_switch.pack(side="right", padx=25)
        
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()

        # 2. منطقة الشات
        self.chat_frame = ctk.CTkScrollableFrame(
            self, 
            label_text="", 
            fg_color="transparent" 
        )
        self.chat_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # 3. العلامة المائية
        self.watermark = ctk.CTkLabel(
            self, 
            text="S.M.A.-ASSISTANT", 
            font=("Arial Black", 25, "bold"),
            text_color=("gray70", "gray30"),
            fg_color="transparent"
        )
        self.watermark.place(relx=0.5, rely=0.88, anchor="center") 
        
        # تمرير السكرول عبر العلامة المائية
        def pass_scroll(event):
            self.chat_frame._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.watermark.bind("<MouseWheel>", pass_scroll)

        # 4. منطقة الإدخال
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, padx=20, pady=(0, 25), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        # حقل الكتابة
        self.entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="اكتب رسالتك هنا... | Type a message...", 
            height=55, 
            font=("Segoe UI", 15),
            corner_radius=30,
            border_width=2,
            border_color=("#00796B", "#004D40"),
            fg_color=("white", "#2b2b2b")
        )
        self.entry.grid(row=0, column=0, padx=(0, 15), sticky="ew")
        self.entry.bind("<Return>", self.on_send)

        # زر الإرسال
        self.send_btn = ctk.CTkButton(
            self.input_frame, 
            text="➤", 
            width=55, 
            height=55, 
            font=("Arial", 24, "bold"), 
            fg_color="#00C853", 
            hover_color="#00E676",
            corner_radius=30,
            command=self.on_send
        )
        self.send_btn.grid(row=0, column=1)

        # رسالة ترحيب
        self.after(600, lambda: self._add_message("مرحباً بك! أنا مساعدك الذكي S.M.A.\nكيف يمكنني خدمتك اليوم؟", is_user=False))

    def toggle_theme(self):
        if self.theme_switch.get() == "Dark":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def _load_data_bg(self):
        try:
            self.faq_data, self.faq_embeddings = load_faq_data()
        except Exception as e:
            print("Error loading data:", e)

    def on_send(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        
        self.entry.delete(0, "end")
        self._add_message(text, is_user=True)
        
        # حفظ لون الزر الأصلي وتعطيله
        original_color = self.send_btn.cget("fg_color")
        self.send_btn.configure(state="disabled", fg_color="gray") 
        
        # بدء المعالجة في خيط منفصل
        threading.Thread(target=self._process_question, args=(text, original_color), daemon=True).start()

    def _process_question(self, question: str, original_btn_color):
        try:
            # محاكاة التفكير
            time.sleep(0.5) 
            
            # 1. اكتشاف اللغة
            detected = detect_language(question)
            
            # تحسينات بسيطة للترحيب
            greetings = ["hello", "hi", "hey", "marhaba", "مرحبا", "هلا"]
            if any(g in question.lower().strip() for g in greetings):
                detected = "en" if question.isascii() else "ar"

            # 2. الترجمة للإنجليزية إذا لزم الأمر
            if detected != "en":
                translated_q = translate_text(question, detected, "en")
            else:
                translated_q = question

            # التأكد من تحميل البيانات
            if self.faq_data is None:
                self.faq_data, self.faq_embeddings = load_faq_data()

            # 3. البحث عن الإجابة (مع استقبال النتيجة Score)
            # تم استخدام translated_q بدلاً من question لضمان دقة البحث
            best_match, score = search_faq(translated_q, self.faq_data, self.faq_embeddings)
            
            # --- فلتر الدقة (Threshold) ---
            # إذا كانت النسبة أقل من 0.5 (50%)، نعتبر السؤال غير موجود
            if score < 0.5:
                error_msg_en = "I'm sorry, I didn't quite understand that. Could you rephrase?"
                if detected != "en":
                    final_answer = translate_text(error_msg_en, "en", detected)
                else:
                    final_answer = error_msg_en
            else:
                # إذا كانت النسبة جيدة، نأخذ الإجابة
                answer_en = best_match.get("answer", "Answer not found.")
                
                # ترجمة الإجابة للغة المستخدم
                if detected != "en":
                    final_answer = translate_text(answer_en, "en", detected)
                else:
                    final_answer = answer_en

            # 4. عرض الإجابة
            self.after(0, lambda: self._add_message(final_answer, is_user=False))

        except Exception as exc:
            # تحويل الخطأ لنص لتجنب مشاكل النطاق (Scope issues)
            error_msg = str(exc)
            self.after(0, lambda: self._add_message(f"Error: {error_msg}", is_user=False))
        
        finally:
            # إعادة تفعيل الزر دائماً
            self.after(0, lambda: self.send_btn.configure(state="normal", fg_color=original_btn_color))

    def _add_message(self, text, is_user):
        # تحديد اتجاه النص (عربي/إنجليزي)
        is_arabic = any("\u0600" <= c <= "\u06FF" for c in text)

        if is_user:
            bubble_color = ("#E0F2F1", "#00695C") 
            text_color = ("black", "white")
            anchor = "e"
            justify_text = "right" 
            side = "right"
            pad_tuple = (60, 10)
        else:
            bubble_color = ("white", "#37474F")
            text_color = ("black", "white")
            justify_text = "right" if is_arabic else "left"
            anchor = "e" if is_arabic else "w"
            side = "left"
            pad_tuple = (10, 60)

        msg_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_container.pack(fill="x", pady=8)

        bubble = ctk.CTkLabel(
            msg_container, 
            text=text, 
            fg_color=bubble_color, 
            text_color=text_color,
            corner_radius=20,
            wraplength=450, 
            font=("Segoe UI", 15),
            padx=20, pady=12,
            justify=justify_text 
        )
        
        bubble.pack(side=side, padx=pad_tuple)

        self.chat_frame._parent_canvas.yview_moveto(1.0)

if __name__ == "__main__":
    app = ModernChatGUI()
    app.mainloop()
