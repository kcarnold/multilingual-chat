import streamlit as st
from anthropic import Anthropic
import time

# Initialize Anthropic client
if 'client' not in st.session_state:
    st.session_state.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'languages' not in st.session_state:
    st.session_state.languages = ["English", "Spanish", "Haitian Creole"]

def get_system_message():
    langs = ", ".join(st.session_state.languages)
    return f"""The following is a multilingual conversation. Each user message is from a person in the conversation. 
The assistant then provides a translation of the message in the remaining languages.
The languages in this conversation are: {langs}.

Format your response as plain text with each translation on a new line:

{'\n'.join([f'- **{lang}**: {{translation}}' for lang in st.session_state.languages])}

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
st.title("Multilingual Chat")

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
                    system=get_system_message(),  # Use dynamic system message
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
    st.markdown("### Languages")
    
    # Language management
    new_lang = st.text_input("Add new language:")
    if st.button("Add Language") and new_lang and new_lang not in st.session_state.languages:
        st.session_state.languages.append(new_lang)
        st.rerun()
    
    # Display current languages with remove buttons
    for lang in st.session_state.languages:
        col1, col2 = st.columns([3, 1])
        col1.write(lang)
        if col2.button("🗑️", key=f"remove_{lang}") and len(st.session_state.languages) > 2:
            st.session_state.languages.remove(lang)
            st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app enables multilingual conversations with automatic translation between 
    the selected languages.
    
    Messages are translated while preserving context and tone.
    """)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []  # No need to keep system message in array
        st.rerun()