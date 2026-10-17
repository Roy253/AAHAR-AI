
import streamlit as st
from src.ollama_client import ask_ollama

st.set_page_config(
    page_title="AAHAR AI | Local LLM Test",
    page_icon="🥗",
    layout="centered",
)

st.title("🥗 AAHAR AI")
st.subheader("Your local AI nutrition assistant")

st.info(
    "This is a separate test interface powered by Ollama. "
    "It does not modify your existing AAHAR application."
)

with st.sidebar:
    st.header("About")
    st.write("Model: Qwen 2.5 3B")
    st.write("Runtime: Local Ollama")
    st.write("API usage cost: ₹0 for local inference")
    st.caption(
        "Food suggestions are AI-generated. "
        "Verify nutrition values and prices using reliable data."
    )

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm AAHAR AI. Ask me about affordable vegetarian "
                "foods, hostel meals, or ways to improve meal balance."
            ),
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask AAHAR AI a question...")

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking with your local AI model..."):
            answer = ask_ollama(
                "You are AAHAR AI, a practical hostel nutrition assistant. "
                "Give concise, affordable food suggestions. "
                "Do not invent exact nutrition values, prices, or medical "
                "claims. If precise data is unavailable, say so.\n\n"
                f"User question: {question}"
            )

        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
