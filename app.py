import streamlit as st
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

st.set_page_config(page_title="DZ DK AI - وضعين", page_icon="📚", layout="wide")

# --- التصميم ---
st.sidebar.title("⚙️ التحكم")
mode = st.sidebar.radio("اختر الوضع:", ["🌍 الوضع العام - ذكاء عام", "📚 وضع الدراسة - من كتبي فقط"])

st.title("DZ DK AI - El Oued")
if mode.startswith("🌍"):
    st.caption("الوضع العام - أجيب على أي شيء مثل ChatGPT و Meta AI")
else:
    st.caption("وضع الدراسة - أجيب فقط من الكتب التي رفعتها")

# --- وظائف قراءة الكتب ---
def extract_text_from_pdfs(files):
    all_text = ""
    for file in files:
        try:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                all_text += page.extract_text() + "\n"
        except: pass
    return all_text

def chunk_text(text, size=800):
    return [text[i:i+size] for i in range(0, len(text), size)]

# --- تخزين ---
if "book_chunks" not in st.session_state:
    st.session_state.book_chunks = []
if "book_name" not in st.session_state:
    st.session_state.book_name = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- واجهة وضع الدراسة ---
if mode.startswith("📚"):
    st.sidebar.markdown("---")
    uploaded = st.sidebar.file_uploader("📤 ارفع كتبك (PDF)", type="pdf", accept_multiple_files=True)
    if uploaded:
        with st.spinner("نقرا في الكتب..."):
            full_text = extract_text_from_pdfs(uploaded)
            st.session_state.book_chunks = chunk_text(full_text)
            st.session_state.book_name = ", ".join([f.name for f in uploaded])
            st.sidebar.success(f"تم حفظ {len(st.session_state.book_chunks)} صفحة من: {st.session_state.book_name}")
    
    if not st.session_state.book_chunks:
        st.warning("⬅️ ارفع كتابك من الشريط الجانبي أولا لكي أبدأ الدراسة معك")
        st.stop()

# --- عرض المحادثة ---
for m in st.session_state.messages:
    # نعرض فقط رسائل نفس الوضع
    if m.get("mode") == mode:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

prompt = st.chat_input("اسألني هنا...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "mode": mode})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- توليد الإجابة ---
    answer = ""
    if mode.startswith("📚"):
        # البحث في الكتب فقط
        if st.session_state.book_chunks:
            vectorizer = TfidfVectorizer().fit(st.session_state.book_chunks + [prompt])
            vecs = vectorizer.transform(st.session_state.book_chunks + [prompt])
            sims = cosine_similarity(vecs[-1], vecs[:-1]).flatten()
            top_idx = sims.argsort()[-3:][::-1]
            
            if sims[top_idx[0]] < 0.1:
                answer = f"❌ هذا السؤال غير موجود في الكتب التي رفعتها ({st.session_state.book_name}). اسأل فقط مما هو داخل الكتب."
            else:
                context = "\n\n---\n\n".join([st.session_state.book_chunks[i] for i in top_idx])
                answer = f"📖 *الإجابة حسب كتبك ({st.session_state.book_name}):\n\n{context[:2000]}\n\n---\nالخلاصة:* المعلومات أعلاه هي كل ما وجدته في كتبك يخص سؤالك: '{prompt}'"
        else:
            answer = "لم ترفع أي كتاب بعد."
    else:
        # الوضع العام - ذكاء عام بدون كتب
        # هنا يمكنك لاحقا ربطه بـ Groq API مجاني، حاليا إجابات ذكية
        p = prompt.lower()
        if "شركات الشحن" in p or "الشحن" in p:
            answer = "*أفضل شركات الشحن في الجزائر 2025-2026:\n\n1. **Yalidine Express:* الأفضل تغطية 58 ولاية، تطبيق مليح\n2. *ZR Express:* الأسرع للتجارة الإلكترونية، الدفع عند الاستلام\n3. *Maystro Delivery:* رخيص للمبتدئين\n4. *EMS / DHD:* تاع الدولة\n\n*نصيحة من DK AI:* ابدا بـ Yalidine اذا تبيع في كامل الجزائر."
        elif "البرمجة" in p or "python" in p:
            answer = "البرمجة سهلة يا خويا! اذا حاب تبدا: \n1. تعلم Python\n2. تعلم Streamlit باش تدير مواقع AI\n3. تعلم GitHub\nرانا درناها مع بعض! تحب نعلمك الخطوة الجاية؟"
        else:
            answer = f"تمام، فهمت سؤالك: *{prompt}*\n\nكذكاء عام، نقدر نجاوبك على أي حاجة: دراسة، تجارة، برمجة، نصائح حياة، تلخيص، كتابة... \n\nاحكيلي بتفصيل أكثر واش حاب نعاونك فيه، وانا نعطيك إجابة دقيقة ومفصلة كيما ChatGPT."

    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer, "mode": mode})
