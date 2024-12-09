import streamlit as st
from anthropic import Anthropic
import time

# Initialize Anthropic client
if 'client' not in st.session_state:
    st.session_state.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state.messages = []

system_message = """The following is a multilingual conversation. Each user message is from a person in the conversation. 
The assistant then provides a translation of the message in the remaining languages.
The languages in this conversation are: English, Spanish, Haitian Creole.

Format your response as plain text with each translation on a new line:

- **English**: {translation}
- **Spanish**: {translation}
- **Haitian Creole**: {translation}

Don't include a line for the source language.

Important:
1. Translate ONLY the exact content given - do not add any additional text or context
2. Do not create responses or add content that wasn't in the original message
3. Maintain the tone appropriate for each language
4. Consider cultural context in translations while keeping the exact meaning
5. Preserve emojis and basic punctuation where appropriate
"""

# Page config
st.set_page_config(page_title="Multilingual Chat", page_icon="🌎")
st.title("Multilingual Chat 🌎")

# Language selector
LANGUAGES = ["English", "Spanish", "Haitian Creole"]

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "assistant":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if idx < len(st.session_state.messages) - 1:
            # Display translations directly since they're already formatted
            st.markdown(st.session_state.messages[idx + 1]["content"])

# Chat input
if prompt := st.chat_input("Type your message here"):
    # Add user message to chat history
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)

    message_container = st.chat_message("user")
    message_container.write(prompt)

    # Get translations for user message
    with st.spinner("Translating..."):
        try:
            def translation_generator():
                response_text = ""
                stream = st.session_state.client.messages.stream(
                    model="claude-3-5-haiku-20241022",
                    messages=st.session_state.messages,
                    system=system_message,
                    max_tokens=1000,
                    temperature=0.7
                )
                with stream as text_stream:                    
                    for chunk in text_stream:
                        if chunk.type == 'text':
                            yield chunk.text

            # Stream the translations and capture final response
            final_response = message_container.write_stream(translation_generator())

            # Add complete response to chat history
            assistant_message = {"role": "assistant", "content": final_response}
            st.session_state.messages.append(assistant_message)

        except Exception as e:
            st.error(f"Translation error: {str(e)}")
            st.stop()

# Sidebar options
with st.sidebar:
    st.markdown("### About")
    st.markdown("""
    This app enables multilingual conversations with automatic translation between:
    - English 🇺🇸
    - Spanish 🇪🇸
    - Haitian Creole 🇭🇹
    
    Messages are translated while preserving context and tone.
    """)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []  # No need to keep system message in array
        st.rerun()