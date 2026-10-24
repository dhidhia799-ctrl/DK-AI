import streamlit as st

st.set_page_config(page_title="DK AI", page_icon="🤖")
st.title("🇩🇿 DK AI - El Oued")
st.write("المساعد الذكي لأهل الوادي - نسخة Streamlit")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("اكتب سؤالك هنا..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    answer = f"DK AI يرد: {prompt}"
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)
