# utils.py
# دوال مساعدة للمشروع

def clean_text(text):
    """تنظيف النص من الفراغات والرموز الزايدة"""
    return text.strip().lower()