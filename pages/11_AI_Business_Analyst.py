"""Conversational interface for the evidence-grounded business analyst."""

import streamlit as st

from utils.theme import apply_dashboard_theme

from utils.ai_analyst import ask_business_analyst
from utils.data_loader import load_processed_data
from utils.filters import sidebar_filters


st.set_page_config(page_title="AI Business Analyst", layout="wide")

apply_dashboard_theme()


WELCOME_MESSAGE = (
    "Ask me about sales, profit, customers, products, discounts, shipping, "
    "geography, forecasting evidence, or management priorities. I use the "
    "currently filtered Superstore transactions and identify important data "
    "limitations in my answer."
)

SUGGESTED_QUESTIONS = [
    "Which year achieved the highest sales growth?",
    "Which regions require management attention?",
    "Which products should receive priority inventory allocation?",
    "How does discounting relate to profitability?",
    "What are the biggest business risks?",
    "What should management prioritise next?",
]


def reset_conversation() -> None:
    """Restore the chat to its initial assistant greeting."""
    st.session_state["ai_messages"] = [
        {"role": "assistant", "content": WELCOME_MESSAGE, "mode": None}
    ]


# Load and filter data before accepting a question so every answer uses the
# same active dashboard scope shown to the user.
df = load_processed_data()
filtered_df = sidebar_filters(df)

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

if "ai_messages" not in st.session_state:
    reset_conversation()


# Header and analysis scope
header, action = st.columns([5, 1])
with header:
    st.title("AI Business Analyst")
    st.caption(
        "Conversational analysis grounded in Python-verified Superstore evidence"
    )
with action:
    st.write("")
    st.button(
        "New conversation",
        on_click=reset_conversation,
        width="stretch",
    )

st.info(
    f"Analysis scope: {len(filtered_df):,} transactions, "
    f"{filtered_df['order_id'].nunique():,} orders, and "
    f"{filtered_df['customer_id'].nunique():,} customers. "
    "Sidebar filters apply automatically."
)


# Suggested prompts use the exact same processing route as typed questions.
with st.expander("Suggested questions", expanded=True):
    prompt_columns = st.columns(2)
    selected_prompt = None
    for index, prompt in enumerate(SUGGESTED_QUESTIONS):
        with prompt_columns[index % 2]:
            if st.button(prompt, key=f"suggested_prompt_{index}", width="stretch"):
                selected_prompt = prompt


# Conversation history is rendered directly after the suggestions so the page
# reads like a chatbot instead of a dashboard report.
for message in st.session_state["ai_messages"]:
    with st.chat_message(message["role"]):
        if message.get("mode"):
            st.caption(f"Analysis mode: {message['mode']}")
        st.markdown(message["content"])


typed_question = st.chat_input(
    "Ask a question about the currently filtered Superstore data..."
)
question = selected_prompt or typed_question

if question:
    st.session_state["ai_messages"].append(
        {"role": "user", "content": question, "mode": None}
    )
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing the filtered business data..."):
            try:
                result = ask_business_analyst(question, filtered_df)
                answer = result["answer"]
                mode = result["mode"]
                st.caption(f"Analysis mode: {mode}")
                st.markdown(answer)
            except Exception as error:
                mode = "Unavailable"
                answer = (
                    "I could not complete that analysis. Check the AI service "
                    f"configuration and try again. Technical detail: {error}"
                )
                st.error(answer)

    st.session_state["ai_messages"].append(
        {"role": "assistant", "content": answer, "mode": mode}
    )


# Keep governance accessible without pushing the conversation far down the page.
with st.expander("Analysis scope and limitations"):
    st.markdown(
        """
        Responses use Python-generated summaries from the active dashboard data.
        Exact descriptive questions are answered directly from Python evidence;
        broader questions use the configured AI model to interpret that evidence.

        The assistant will not answer unrelated general-knowledge questions. The
        dataset does not include current inventory, supplier lead times, purchase
        costs, marketing expenditure, competitors, customer satisfaction, or
        economic conditions. Recommendations involving those areas are provisional.

        AI interpretation supports management judgment; it does not replace it.
        """
    )
