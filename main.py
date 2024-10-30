import io
from openai import OpenAI
from gtts import gTTS
import streamlit as st
from io import BytesIO

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set page configuration
st.set_page_config(
    page_title='Moma Health',
    page_icon='🌎',
    layout='centered',
    initial_sidebar_state='auto'
)

# Hide Streamlit footer
hide_streamlit_style = """
<style>
    footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Initialize session state for prompts
if "prompts" not in st.session_state:
    st.session_state["prompts"] = []

# Functions to manage prompts
def add_prompt(prompt: str):
    st.session_state["prompts"].append({"id": len(st.session_state["prompts"]), "text": prompt})

def remove_prompt(prompt_id: int):
    st.session_state["prompts"] = [p for p in st.session_state["prompts"] if p["id"] != prompt_id]

def update_prompt(prompt_id: int, new_text: str):
    for p in st.session_state["prompts"]:
        if p["id"] == prompt_id:
            p["text"] = new_text
            break

# Sidebar for adding and managing prompts
st.sidebar.header("Add New Example")
new_prompt = st.sidebar.text_area("Enter your example text here:")
if st.sidebar.button("Add example"):
    if new_prompt:
        add_prompt(new_prompt)
        st.sidebar.success("Example added!")

st.sidebar.header("Manage Existing Examples")
for prompt in st.session_state["prompts"]:
    st.sidebar.text_area(f"Prompt ID {prompt['id']}", prompt["text"], key=f"prompt_{prompt['id']}")
    if st.sidebar.button("Update", key=f"update_{prompt['id']}"):
        update_prompt(prompt["id"], st.session_state[f"prompt_{prompt['id']}"])
        st.sidebar.success(f"Example {prompt['id']} updated!")
    if st.sidebar.button("Remove", key=f"remove_{prompt['id']}"):
        remove_prompt(prompt["id"])
        st.sidebar.success(f"Example {prompt['id']} removed!")

# Main section for audio upload, transcription, and OpenAI query
st.header("Moma Health")

# File uploader for audio input
audio_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])
if audio_file:
    st.audio(audio_file)

    # Transcription and translation on form submit
    with st.form('input_form'):
        submit_button = st.form_submit_button(label='Translate')
        if submit_button:
            try:
                audio_file.seek(0)  # Reset file pointer to the beginning
                transcript = client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file
                )
                st.markdown("***Transcription***")
                st.text_area("Transcription", transcript.text, label_visibility="collapsed")

                user_query = transcript.text
                few_shot_prompts = [{"role": "user", "content": prompt["text"]} for prompt in st.session_state["prompts"]]
                instructions = """You are an expert American physician.
                Your job is to create the patient encounter based on patient doctor conversation.
                The format of the encounter should be same as in previous mentioned examples.
                Don't add anything from the previous examples in the final response.
                Include all relevant information discussed in the transcript.
                Use double asterisks for all the headings.
                Write all the headings that is mentioned in the mentioned examples on separate lines using the newline character (/n)."""
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": instructions},
                              *few_shot_prompts,
                              {"role": "user", "content": user_query}]

                )
                st.write("Response:")
                st.write(completion.choices[0].message.content)


            except Exception as e:
                st.error(f"An error occurred: {e}")
else:
    st.warning('Please upload an audio file to begin transcription and translation.')
