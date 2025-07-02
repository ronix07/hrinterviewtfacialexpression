import streamlit as st
import google.generativeai as genai
import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
from PyPDF2 import PdfReader
import os
import tempfile
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime
import sys
from streamlit.web import cli as stcli
import cv2
from gtts import gTTS
import mediapipe as mp
import pygame
import threading
from queue import Queue

# Set page configuration
st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

# Initialize session states
if 'start_camera' not in st.session_state:
    st.session_state.start_camera = False
if 'video_capture' not in st.session_state:
    st.session_state.video_capture = None
if 'frame_placeholder' not in st.session_state:
    st.session_state.frame_placeholder = None
if 'attention_warning' not in st.session_state:
    st.session_state.attention_warning = False
if 'last_face_detected_time' not in st.session_state:
    st.session_state.last_face_detected_time = time.time()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'domain' not in st.session_state:
    st.session_state.domain = ""
if 'interview_ended' not in st.session_state:
    st.session_state.interview_ended = False
if 'performance_analysis' not in st.session_state:
    st.session_state.performance_analysis = None
if 'audio_queue' not in st.session_state:
    st.session_state.audio_queue = Queue()

# Configure Gemini API
genai.configure(api_key="AIzaSyAfu-ok5QV1nBuxZSgDkn63NGIWulQHh5I")
model = genai.GenerativeModel("models/gemini-1.5-pro")

# Initialize Whisper model
whisper_model = whisper.load_model("base")

# Initialize Pygame mixer for audio
pygame.mixer.init()

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Video frame */
    .video-frame {
        border: 3px solid #00FF9F;
        border-radius: 10px;
        margin: 10px 0;
        background-color: #2D2D2D;
    }
    
    /* Attention warning */
    .attention-warning {
        background-color: #FF4444;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        text-align: center;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        50% { opacity: 0.5; }
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #00FF9F !important;
        font-family: 'Segoe UI', sans-serif !important;
        font-weight: 700 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
        text-shadow: 0 0 10px rgba(0,255,159,0.5) !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #2D2D2D !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
        border: 1px solid #00FF9F !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #00FF9F !important;
        color: #1E1E1E !important;
        font-weight: bold !important;
        border-radius: 25px !important;
        padding: 10px 25px !important;
        border: none !important;
        box-shadow: 0 0 15px rgba(0,255,159,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 20px rgba(0,255,159,0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def record_audio(duration=10):
    fs = 44100
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    with st.status("🎙️ Recording in progress...", expanded=True) as status:
        st.write(f"Recording for {duration} seconds...")
        progress_bar = st.progress(0)
        for i in range(duration * 10):
            time.sleep(0.1)
            progress_bar.progress((i + 1) / (duration * 10))
        sd.wait()
        status.update(label="✅ Recording complete!", state="complete")
    return recording, fs

def get_ai_response(prompt, resume_text, domain):
    context = f"""You are an expert interviewer conducting a technical interview. 
    Resume: {resume_text}
    Domain: {domain}
    Based on this information, respond to: {prompt}
    Keep your responses focused and professional."""
    
    response = model.generate_content(context)
    return response.text

def analyze_interview_performance(messages, domain):
    # Prepare the conversation history for analysis
    conversation = "\n".join([f"{'AI' if msg['role'] == 'assistant' else 'Candidate'}: {msg['content']}" 
                            for msg in messages if msg['role'] != 'system'])
    
    analysis_prompt = f"""As an expert technical interviewer, analyze the following interview conversation for a {domain} position.
    Provide a detailed evaluation including:
    1. Overall Performance (Score out of 100)
    2. Key Strengths
    3. Areas for Improvement
    4. Communication Skills
    5. Technical Proficiency
    6. Specific Recommendations for Growth

    Interview Conversation:
    {conversation}

    Format the response in a clear, structured manner with emoji indicators for each section.
    """
    
    response = model.generate_content(analysis_prompt)
    return response.text

def generate_pdf_report(analysis, domain, resume_text):
    # Create a buffer to store the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    elements.append(Paragraph("Interview Performance Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Add date and domain
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.gray,
        alignment=1
    )
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", date_style))
    elements.append(Paragraph(f"Domain: {domain}", date_style))
    elements.append(Spacer(1, 20))
    
    # Add analysis content
    content_style = ParagraphStyle(
        'ContentStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        spaceAfter=16
    )
    
    # Split analysis into sections and format them
    sections = analysis.split('\n\n')
    for section in sections:
        elements.append(Paragraph(section, content_style))
        elements.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_audio.name)
        return temp_audio.name
    except Exception as e:
        st.error(f"Error in text to speech conversion: {str(e)}")
        return None

def play_audio_response(audio_file):
    try:
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        st.error(f"Error playing audio: {str(e)}")
    finally:
        try:
            os.remove(audio_file)
        except:
            pass

def start_video():
    """Initialize and start video capture"""
    if st.session_state.video_capture is None:
        st.session_state.video_capture = cv2.VideoCapture(0)
    return st.session_state.video_capture.isOpened()

def stop_video():
    """Stop and release video capture"""
    if st.session_state.video_capture is not None:
        st.session_state.video_capture.release()
        st.session_state.video_capture = None

def process_frame(frame):
    """Process video frame and detect face"""
    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect faces
    results = face_detection.process(frame_rgb)
    
    # Draw detection results
    if results.detections:
        st.session_state.last_face_detected_time = time.time()
        st.session_state.attention_warning = False
        
        for detection in results.detections:
            mp_drawing.draw_detection(frame_rgb, detection)
            
        # Add green border to indicate attention
        frame_rgb = cv2.copyMakeBorder(
            frame_rgb, 10, 10, 10, 10,
            cv2.BORDER_CONSTANT,
            value=[0, 255, 0]
        )
    else:
        # Check if face hasn't been detected for more than 3 seconds
        if time.time() - st.session_state.last_face_detected_time > 3:
            st.session_state.attention_warning = True
            # Add red border to indicate lack of attention
            frame_rgb = cv2.copyMakeBorder(
                frame_rgb, 10, 10, 10, 10,
                cv2.BORDER_CONSTANT,
                value=[255, 0, 0]
            )
    
    return frame_rgb

def update_video_frame():
    """Update video frame in the UI"""
    if st.session_state.video_capture is not None:
        ret, frame = st.session_state.video_capture.read()
        if ret:
            # Process frame and detect face
            processed_frame = process_frame(frame)
            
            # Display frame
            if st.session_state.frame_placeholder is not None:
                st.session_state.frame_placeholder.image(
                    processed_frame,
                    channels="RGB",
                    use_column_width=True
                )
            
            # Display attention warning if needed
            if st.session_state.attention_warning:
                st.warning("⚠️ Please look at the camera! Maintaining eye contact is important during interviews.")
            
            return True
    return False

def main():
    # Create three columns for layout
    left_col, middle_col, right_col = st.columns([1.5, 2, 1.5])
    
    with left_col:
        st.markdown("<h1>🤖 AI Interview Assistant</h1>", unsafe_allow_html=True)
        
        # Domain selection
        st.markdown("### 🎯 Select Your Domain")
        domains = [
            "Software Development", "Data Science", "DevOps",
            "Machine Learning", "Web Development", "Cloud Computing",
            "Cybersecurity"
        ]
        selected_domain = st.selectbox("", domains)
        st.session_state.domain = selected_domain
        
        # Resume upload
        st.markdown("### 📄 Upload Your Resume")
        uploaded_file = st.file_uploader("", type="pdf")
        
        if uploaded_file and not st.session_state.resume_text:
            with st.spinner("📝 Analyzing your resume..."):
                st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
                st.session_state.start_camera = True
    
    with middle_col:
        st.markdown("### 📹 Interview Session")
        
        # Initialize video frame placeholder
        if st.session_state.frame_placeholder is None:
            st.session_state.frame_placeholder = st.empty()
        
        # Start video capture if resume is uploaded
        if st.session_state.start_camera:
            if start_video():
                # Update video frame continuously
                while update_video_frame():
                    time.sleep(0.1)
    
    with right_col:
        if st.session_state.interview_ended:
            st.markdown("### 📊 Interview Analysis")
            st.markdown(st.session_state.performance_analysis)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Start New Interview"):
                    st.session_state.messages = []
                    st.session_state.interview_ended = False
                    st.session_state.performance_analysis = None
                    st.rerun()
            
            with col2:
                if st.button("📥 Download Report"):
                    pdf_buffer = generate_pdf_report(
                        st.session_state.performance_analysis,
                        st.session_state.domain,
                        st.session_state.resume_text
                    )
                    st.download_button(
                        label="📄 Save PDF Report",
                        data=pdf_buffer,
                        file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.markdown("### 💬 Chat")
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
            
            # Audio recording interface
            if not st.session_state.interview_ended:
                st.markdown("### 🎙️ Your Response")
                if st.button("Start Recording (10s)"):
                    if st.session_state.resume_text:
                        recording, fs = record_audio()
                        
                        try:
                            with st.spinner("🔄 Processing your response..."):
                                temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                                temp_audio_path = temp_audio.name
                                temp_audio.close()
                                
                                sf.write(temp_audio_path, recording, fs)
                                result = whisper_model.transcribe(temp_audio_path)
                                user_response = result["text"]
                                
                                st.session_state.messages.append({"role": "user", "content": user_response})
                                
                                # Generate and speak AI response
                                ai_response = get_ai_response(user_response, st.session_state.resume_text, st.session_state.domain)
                                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                                
                                # Convert AI response to speech
                                audio_file = text_to_speech(ai_response)
                                if audio_file:
                                    st.session_state.audio_queue.put(audio_file)
                                
                        finally:
                            try:
                                if os.path.exists(temp_audio_path):
                                    os.unlink(temp_audio_path)
                            except Exception as e:
                                st.warning(f"Note: Could not delete temporary file: {str(e)}")
                        
                        st.rerun()
                    else:
                        st.error("⚠️ Please upload your resume first!")

    # Process audio queue
    while not st.session_state.audio_queue.empty():
        audio_file = st.session_state.audio_queue.get()
        play_audio_response(audio_file)

# Cleanup function
def cleanup():
    """Clean up resources"""
    stop_video()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        if st.runtime.exists():
            main()
        else:
            sys.argv = ["streamlit", "run", sys.argv[0], "--server.address", "0.0.0.0", "--server.port", "8502"]
            sys.exit(stcli.main())
    finally:
        cleanup()