import streamlit as st
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from g4f.client import Client
import urllib.parse
import time

client = Client()
st.set_page_config(page_title="بوت الباك المباشر - مربوط بالمواقع", page_icon="🎓")

# --- المواقع الموثوقة فقط ---
TRUSTED_SITES = [
    "dzexams.com",
    "bac-feljib.com",
    "etuddz.com",
    "dzbac.com",
    "ency-education.com"
]

STREAMS = {
    "🧪 علوم تجريبية": "علوم تجريبية",
    "📐 رياضيات": "رياضيات",
    "💼 تسيير واقتصاد": "تسيير واقتصاد",
    "📜 آداب وفلسفة": "آداب وفلسفة",
    "🌍 لغات أجنبية": "لغات أجنبية"
}

if "messages" not in st.session_state:
    st.session_state.messages = {k: [] for k in STREAMS.keys()}

with st.sidebar:
    st.title("🎓 بوت الباك المباشر")
    selected_stream = st.radio("اختر شعبتك:", list(STREAMS.keys()))
    st.divider()
    st.markdown("### 🌐 مربوط مباشرة بـ:")
    for s in TRUSTED_SITES:
        st.write(f"✅ {s}")
    st.caption("البوت يبحث في هذه المواقع فقط لايف، بلا ما ترفع كتب!")

def search_in_trusted_sites(query, stream):
    """يبحث في المواقع الموثوقة فقط"""
    all_texts = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # نكون رابط بحث DuckDuckGo مقيد بالمواقع
    search_query = f"site:dzexams.com OR site:bac-feljib.com {stream} {query}"
    encoded = urllib.parse.quote_plus(search_query)
    
    try:
        # نجيب نتائج البحث
        search_url = f"https://html.duckduckgo.com/html/?q={encoded}"
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        links = []
        for a in soup.find_all('a', class_='result__url', limit=5):
            href = a.get('href')
            if href and any(site in href for site in TRUSTED_SITES):
                # DuckDuckGo يخبي الرابط الحقيقي
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                real_url = parsed.get('uddg', [None])[0]
                if real_url:
                    links.append(real_url)
        
        # لو ما لقيناش، نجربو مباشرة dzexams
        if not links:
            # بحث مباشر في dzexams
            dz_search = f"https://dzexams.com/ar/?s={urllib.parse.quote_plus(query + ' ' + stream)}"
            r2 = requests.get(dz_search, headers=headers, timeout=10)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            for a in soup2.find_all('a', href=True)[:5]:
                if 'dzexams.com' in a['href']:
                    links.append(a['href'])
        
        # الآن نجيب محتوى أول 3 روابط
        for url in links[:3]:
            try:
                page = requests.get(url, headers=headers, timeout=8)
                s = BeautifulSoup(page.text, 'lxml')
                for tag in s(["script","style","nav","footer","header"]): tag.decompose()
                text = s.get_text(separator="\n")
                lines = [l.strip() for l in text.splitlines() if len(l.strip())>40]
                clean = "\n".join(lines)
                if len(clean) > 300:
                    all_texts.append(clean[:4000])
            except:
                continue
            time.sleep(0.5)
            
    except Exception as e:
        print(f"search error: {e}")
    
    return all_texts

def ask_from_live_sites(question, contexts, stream):
    if not contexts:
        return f"عذرا يا بطل شعبة {stream}، بحثت في المواقع الرسمية (dzexams و الباك في الجيب) وما لقيتش هذه المعلومة بالضبط. جرب تصيغ السؤال بكلمات من الدرس 💪"
    
    combined = "\n\n---\n\n".join(contexts)[:6000]
    
    system = f"""
انت أستاذ بكالوريا جزائري لطيف جدا في شعبة {stream}.
عندك هذا النص الحي الذي جبته الآن مباشرة من المواقع الرسمية dzexams.com و bac-feljib.com:
\"\"\"
{combined}
\"\"\"

القوانين:
1. جاوب فقط من النص اللي فوق، ممنوع تزيد أي معلومة من عندك
2. صغ الجواب بأسلوب لطيف ومشجع وبالدارجة الجزائرية الخفيفة: "الله يبارك سؤال ممتاز يا بطل..."
3. لا تذكر الروابط ولا تقول انك بحثت، جاوب مباشرة كأنك الأستاذ
4. اذا النص لا يحتوي الجواب قل: هذه النقطة غير متوفرة حاليا في المواقع الرسمية لشعبة {stream}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},{"role":"user","content":question}]
        )
        return resp.choices[0].message.content
    except:
        # لو طاح الذكاء، رجع النص الخام بلباقة
        return f"يا بطل، حسب المواقع الرسمية لشعبة {stream}:\n\n{contexts[0][:1000]}"

# --- الواجهة ---
st.title(f"{selected_stream} - بوت الباك المباشر 🌐")
st.caption(f"مربوط مباشرة بـ dzexams.com و bac-feljib.com - شعبة {selected_stream} - يجاوب فقط منهم")

for m in st.session_state.messages[selected_stream]:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if len(st.session_state.messages[selected_stream]) == 0:
    with st.chat_message("assistant"):
        st.markdown(f"أهلا يا بطل *{selected_stream}! 👋\n\nأنا مربوط مباشرة بمواقع الباك الرسمية، اسألني أي درس من دروس *{selected_stream}** ونجيبلك الجواب في ثواني من dzexams و الباك في الجيب، بلا ما ترفع حتى كتاب!")

q = st.chat_input(f"اسأل في {selected_stream}...")

if q:
    st.session_state.messages[selected_stream].append({"role":"user","content":q})
    with st.chat_message("user"): st.markdown(q)

    with st.spinner(f"🔍 نبحث الآن في dzexams.com و bac-feljib.com عن {selected_stream}..."):
        contexts = search_in_trusted_sites(q, STREAMS[selected_stream])
    
    with st.spinner("✍️ نكتبلك الجواب بأسلوب لطيف..."):
        ans = ask_from_live_sites(q, contexts, STREAMS[selected_stream])

    with st.chat_message("assistant"): st.markdown(ans)
    st.session_state.messages[selected_stream].append({"role":"assistant","content":ans})
    
    # للمطور فقط: وري منين جبنا
    with st.expander("🔎 (للمطور) شوف النص الخام اللي جبناه من المواقع"):
        for i, c in enumerate(contexts):
            st.text(f"--- مصدر {i+1} ---\n{c[:800]}...")
