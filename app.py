import streamlit as st
import openai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
from PIL import Image
from docx import Document
import base64

# Set up OpenAI API key
openai.api_key = "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"

# Function to retrieve transcript from YouTube video using its ID
def get_video_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = ' '.join([line['text'] for line in transcript_list])
        return transcript
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Function to save transcript to a file
def save_transcript(transcript):
    try:
        with open('transcript.txt', 'w') as f:
            f.write(transcript)
        #st.success("Transcript saved to transcript.txt")
    except Exception as e:
        st.error(f"Error while generating: {str(e)}")

# Function to chunk the transcript into smaller parts
def chunk_transcript(transcript, chunk_size):
    chunks = []
    words = re.findall(r'\b\w+\b', transcript)
    num_words = len(words)
    for i in range(0, num_words, chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    print(len(chunks))
    return chunks

# Function to count words in a text
def count_words(text):
    words = re.findall(r'\b\w+\b', text)
    print(len(words))
    return len(words)

# Function to generate notes using OpenAI API
def generate_notes(transcript_chunk, prompt, max_tokens):
    prompt += f"\n\nTranscript chunk:\n{transcript_chunk}\n\nNotes:"
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=max_tokens  # Adjust as needed
    )
    notes = response.choices[0].text.strip()
    return notes

# Function for the main notes generation process
def generate_notes_process(transcript, prompt):
    word_count = count_words(transcript)
    if word_count > 3000:
        chunk_size = 3000
        chunk_word_limit = 700
        transcript_chunks = chunk_transcript(transcript, chunk_size)
        final_notes = ""
        for chunk in transcript_chunks:
            notes = generate_notes(chunk, prompt, max_tokens=chunk_word_limit)
            final_notes += notes + " "
        # Generate final notes using all chunks
        #final_notes_response = openai.Completion.create(
            #engine="gpt-3.5-turbo-instruct",
            #prompt=final_notes,
            #max_tokens=1500)
        final_notes_response=generate_notes(final_notes,prompt,max_tokens=1500)
        #final_notes = final_notes_response.choices[0].text.strip()
        return final_notes_response
    elif word_count <= 3000:
        # Generate notes for the entire transcript with a word limit of 1000
        return generate_notes(transcript, prompt, max_tokens=1000)
    

# Resize image by a factor of 3
def resize_image(image_path):
    img = Image.open(image_path)
    width, height = img.size
    new_width = width // 1
    new_height = height // 1
    img_resized = img.resize((new_width, new_height))
    return img_resized

# Streamlit app
def main():
    st.set_page_config(page_title="EduPrepAI", page_icon="🤖")
    st.header("EduPrep AI 🤖")
    st.markdown("Educational Video Notes Generator")
    
    
    # Text input for video URL
    video_url = st.text_input("Paste the URL of the educational video:")
    
    # Button to generate notes
    if st.button("Generate Notes"):
        if video_url:
            try:
                video_id = video_url.split("=")[-1]
                transcript = get_video_transcript(video_id)
                if transcript:
                    # Custom prompt for chapter-wise notes
                    prompt = (
                        "Please provide a very detailed notes for the educational video. "
                        "Organize your notes into chapters and subtopics, starting each chapter with the chapter name in *bold*. "
                        "Include key points and important information under each subtopic."
                        "Give the detailed notes in 1500 words"
                    )
                    notes = generate_notes_process(transcript, prompt)
                    st.subheader("Chapter-wise Notes:")
                    st.write(notes)
                    save_transcript(transcript)
                    # Display images from the "figures" folder
                    image_files = [filename for filename in os.listdir("figures") if filename.endswith((".jpg", ".png"))]
                    num_images = len(image_files)
                    num_columns = 2  # Adjust as needed
                    for i in range(0, num_images, num_columns):
                        col1, col2 = st.columns(2)
                        for j, col in enumerate([col1, col2]):
                            index = i + j
                            if index < num_images:
                                image_path = os.path.join("figures", image_files[index])
                                col.image(resize_image(image_path), caption=image_files[index], use_column_width=True)
                                
                    # Option to download notes as a .doc file
                    if notes:
                        download_button_str = f"Download Notes (.doc)"
                        download_filename = "generated_notes.docx"
                        doc = Document()
                        doc.add_paragraph(notes)
                        doc.save(download_filename)
                        
                        with open(download_filename, "rb") as file:
                            btn = st.download_button(
                                label=download_button_str,
                                data=file,
                                file_name=download_filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                            
                        if btn:
                            st.info(f"Notes downloaded as {download_filename}")
                else:
                    st.error("Failed to retrieve the transcript.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please input the video URL first.")

if __name__ == "__main__":
    main()
