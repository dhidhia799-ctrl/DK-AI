import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests, urllib.parse

st.set_page_config(page_title="DZ DK AI - مجاني", page_icon="🤖")
st.sidebar.title("⚙️ التحكم")
mode = st.sidebar.radio("الوضع:", ["🌍 عام - مجاني 100%", "📚 دراسة - من كتبي"])

def ask_free_ai(prompt, context=""):
    try:
        # هذا موقع مجاني 100% بدون مفتاح
        system = "انت DK AI جزائري من الوادي، تجاوب بالعربية الدارجة باختصار ومفيد."
        if context:
            full_prompt = f"{system}\n\nالنص من الكتب:\n{context[:3000]}\n\nالسؤال: {prompt}\nاذا الجواب مش في النص قل: هذا غير موجود في الكتب التي رفعتها."
        else:
            full_prompt = f"{system}\n\nالسؤال: {prompt}"
        
        encoded = urllib.parse.quote(full_prompt)
        # pollinations مجاني تماما
        url = f"https://text.pollinations.ai/{encoded}?model=openai"
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.text) > 10:
            return r.text
        else:
            return "جرب مرة ثانية، السيرفر مشغول شوية..."
    except Exception as e:
        return f"خطأ بسيط: {e} - عاود المحاولة"

if "chunks" not in st.session_state: st.session_state.chunks = []
if "messages" not in st.session_state: st.session_state.messages = []

if mode.startswith("📚"):
    files = st.sidebar.file_uploader("📤 ارفع كتبك PDF", type="pdf", accept_multiple_files=True)
    if files:
        text = ""
        for f in files:
            reader = PdfReader(f)
            for p in reader.pages:
                t = p.extract_text()
                if t: text += t + "\n"
        st.session_state.chunks = [text[i:i+800] for i in range(0,len(text),800)]
        st.sidebar.success(f"✅ حفظنا {len(st.session_state.chunks)} مقطع")

st.title("DZ DK AI 🇩🇿 - مجاني")
for m in st.session_state.messages:
    if m.get("mode")==mode:
        with st.chat_message(m["role"]): st.markdown(m["content"])

prompt = st.chat_input("اسألني أي شيء...")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt,"mode":mode})
    with st.chat_message("user"): st.markdown(prompt)
    
    ctx=""
    if mode.startswith("📚"):
        if not st.session_state.chunks:
            ans = "⬅️ ارفع كتابك أولا من الجنب"
        else:
            vec = TfidfVectorizer().fit(st.session_state.chunks+[prompt])
            sims = cosine_similarity(vec.transform([prompt]), vec.transform(st.session_state.chunks)).flatten()
            top = sims.argsort()[-3:][::-1]
            ctx = "\n".join([st.session_state.chunks[i] for i in top])
            if sims[top[0]] < 0.08:
                ans = f"❌ هذا السؤال غير موجود في الكتب اللي رفعتها."
            else:
                with st.spinner("نقرا في الكتب..."):
                    ans = ask_free_ai(prompt, ctx)
            with st.chat_message("assistant"): st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans,"mode":mode})
            st.stop()
    
    with st.spinner("نفكر..."):
        ans = ask_free_ai(prompt, "")
    with st.chat_message("assistant"): st.markdown(ans)
    st.session_state.messages.append({"role":"assistant","content":ans,"mode":mode})
