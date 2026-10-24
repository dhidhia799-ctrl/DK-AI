import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# مكتبة مجانية بلا مفتاح
from g4f.client import Client
client = Client()

st.set_page_config(page_title="DZ DK AI - مجاني بلا مفتاح", page_icon="🤖")
st.sidebar.title("⚙️ التحكم")
mode = st.sidebar.radio("الوضع:", ["🌍 عام - مجاني بلا مفتاح", "📚 دراسة - من كتبي"])

def ask_free_no_key(prompt, context=""):
    try:
        system = "انت DK AI مساعد جزائري من الوادي، تجاوب بالدارجة الجزائرية باختصار ومفيد. لا تكرر نفس الرد."
        if context:
            user_msg = f"اعتمد فقط على هذا النص من الكتب:\n{context[:3000]}\n\nالسؤال: {prompt}\nاذا الجواب مش موجود قل: غير موجود في الكتب."
        else:
            user_msg = prompt

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg}
            ],
            timeout=25
        )
        return response.choices[0].message.content
    except Exception as e:
        # رد محلي ذكي اذا الانترنت ثقيل
        p = prompt.lower()
        if "اهلا" in p or "سلام" in p or "مرحبا" in p:
            return "أهلا بيك خويا! 👋 أنا DK AI تاعك من الوادي، واجد نجاوبك. تحب أفكار فيديو، دراسة، ولا حاجة أخرى؟"
        if "موضوع" in p and "فيديو" in p:
            import random
            ideas = [
                "🎥 فكرة: كيفاش درت بوت ذكاء اصطناعي مجاني بلا مفتاح وربطتو مع ستريمليت؟ الناس تموت على هاذ المحتوى!",
                "🎥 فكرة: 3 مواقع تربح منهم بالدولار وانت في الجزائر (بدون خبرة)",
                "🎥 فكرة: قصة غريبة: كيفاش Llama 3 تفوق على ChatGPT وهو مجاني؟",
                "🎥 فكرة: كيفاش تخدم مصغرات يوتيوب بالذكاء الاصطناعي باطل؟"
            ]
            return random.choice(ideas)
        return f"فهمتك: '{prompt}' - السيرفر المجاني مشغول ثانية برك، عاود جرب، راح نجاوبك!"

if "chunks" not in st.session_state: st.session_state.chunks = []
if "messages" not in st.session_state: st.session_state.messages = []

if mode.startswith("📚"):
    files = st.sidebar.file_uploader("📤 ارفع كتبك PDF", type="pdf", accept_multiple_files=True)
    if files:
        text=""
        for f in files:
            reader=PdfReader(f)
            for pg in reader.pages:
                t=pg.extract_text()
                if t: text+=t+"\n"
        st.session_state.chunks=[text[i:i+800] for i in range(0,len(text),800)]
        st.sidebar.success(f"✅ حفظنا {len(st.session_state.chunks)} مقطع")

st.title("DZ DK AI 🤖 - مجاني بلا مفتاح")
for m in st.session_state.messages:
    if m.get("mode")==mode:
        with st.chat_message(m["role"]): st.markdown(m["content"])

q=st.chat_input("اسألني أي شيء...")
if q:
    st.session_state.messages.append({"role":"user","content":q,"mode":mode})
    with st.chat_message("user"): st.markdown(q)
    
    ctx=""
    if mode.startswith("📚"):
        if not st.session_state.chunks:
            ans="⬅️ ارفع كتابك أولا من الجنب"
            with st.chat_message("assistant"): st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans,"mode":mode})
            st.stop()
        else:
            vec=TfidfVectorizer().fit(st.session_state.chunks+[q])
            sims=cosine_similarity(vec.transform([q]), vec.transform(st.session_state.chunks)).flatten()
            top=sims.argsort()[-3:][::-1]
            ctx="\n".join([st.session_state.chunks[i] for i in top])
            if sims[top[0]]<0.08:
                ans="❌ هذا السؤال غير موجود في الكتب اللي رفعتها."
                with st.chat_message("assistant"): st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans,"mode":mode})
                st.stop()

    with st.spinner("نفكر..."):
        ans=ask_free_no_key(q, ctx)
    with st.chat_message("assistant"): st.markdown(ans)
    st.session_state.messages.append({"role":"assistant","content":ans,"mode":mode})
