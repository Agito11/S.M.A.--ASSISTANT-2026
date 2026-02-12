import csv
import os
from sentence_transformers import SentenceTransformer, util
import torch

# Lazy-load the model to avoid long import times
_MODEL = None

def _get_model():
    """
    Get (and cache) the SentenceTransformer model.
    Checks local 'models' folder first, otherwise downloads and saves it.
    """
    global _MODEL
    
    # اسم الموديل
    model_name = "all-MiniLM-L6-v2"

    # تحديد مسار مجلد models بشكل ديناميكي
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    model_save_path = os.path.join(project_root, 'models', model_name)

    if _MODEL is None:
        # 1. محاولة التحميل من المجلد المحلي (Cache)
        if os.path.exists(model_save_path) and len(os.listdir(model_save_path)) > 0:
            print(f"Loading model from local cache: {model_save_path} ...")
            try:
                _MODEL = SentenceTransformer(model_save_path)
            except Exception as e:
                print(f"Error loading local model: {e}. Downloading again...")
                _MODEL = SentenceTransformer(model_name)
                _MODEL.save(model_save_path)
        else:
            # 2. التحميل من الإنترنت إذا لم يكن موجوداً
            print(f"Model not found locally. Downloading {model_name}...")
            _MODEL = SentenceTransformer(model_name)
            
            # التأكد من وجود المجلد وحفظ الموديل فيه
            os.makedirs(model_save_path, exist_ok=True)
            _MODEL.save(model_save_path)
            print(f"Model saved to: {model_save_path}")

    return _MODEL

def load_faq_data():
    """
    Loads FAQ data from csv and computes embeddings.
    """
    model = _get_model()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # المسار إلى ملف faqs.csv
    csv_path = os.path.join(script_dir, '..', 'data', 'faqs.csv')
    
    _FAQ = []
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return [], None

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            _FAQ.append(row)
            
    questions = [item["question"] for item in _FAQ]
    
    # إنشاء الـ embeddings للأسئلة
    embeddings = model.encode(questions, convert_to_tensor=True)
    
    return _FAQ, embeddings

def search_faq(query, arg2, arg3):
    """
    Searches for the most similar question.
    Smartly detects argument order (faq_data vs embeddings).
    """
    model = _get_model()
    
    # --- كود ذكي لتصحيح ترتيب المتغيرات تلقائياً ---
    # نتحقق أيهما هو الـ Tensor (الأرقام) وأيهما القائمة (البيانات)
    if isinstance(arg2, torch.Tensor):
        embeddings = arg2
        faq_data = arg3
    elif isinstance(arg3, torch.Tensor):
        embeddings = arg3
        faq_data = arg2
    else:
        # في حال فشل التحميل أو كانت البيانات غير صحيحة
        print("Error: No embeddings tensor found in arguments.")
        return None, 0
    # -----------------------------------------------

    # تحويل سؤال المستخدم إلى vector
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    # حساب التشابه (Cosine Similarity)
    # ملاحظة: نستخدم embeddings الصحيحة الآن
    hits = util.semantic_search(query_embedding, embeddings, top_k=1)
    
    if hits and hits[0]:
        best_hit = hits[0][0]
        score = best_hit['score']
        idx = best_hit['corpus_id']
        
        return faq_data[idx], score
    
    return None, 0