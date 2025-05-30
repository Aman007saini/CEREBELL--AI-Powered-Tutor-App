import streamlit as st
import requests
import uuid
import random
from streamlit.components.v1 import html

# Page configuration
st.set_page_config(page_title="📚 CEREBELL", layout="wide")

# App title
st.title("🎓 CEREBELL - AI-Powered Tutor & Quiz App")

with st.sidebar:
    st.header("Learning Preferences")
    subject = st.selectbox("📖 Select Subject",
                           
                        ["Mathematics", "Physics", "Computer Science",
                         "History", "Biology", "Programming"])
    
    level = st.selectbox("📚 Select Learning Level",
                      ["Beginner", "Intermediate", "Advanced"])
    
    learning_style = st.selectbox("🧠 Learning Style",
                               ["Visual", "Text-based", "Hands-on"])
    
    language = st.selectbox("🌍 Preferred Language",
                         ["English", "Hindi", "Spanish", "French"])
    
    background = st.selectbox("📊 Background Knowledge",
                           ["Beginner", "Some Knowledge", "Experienced"])



API_ENDPOINT = "http://127.0.0.1:8000"

tab1, tab2 = st.tabs(["📝 Ask a Question", "🧠 Take a Quiz"])

with tab1:
    # Main content area for tutoring
    st.header("Ask Your Question")
    question = st.text_area("❓ What would you like to learn today?",
                         "Explain Newton's Second Law of Motion.")
    
    # Tutor section
    if st.button("Get Explanation 🧠"):
     with st.spinner("Generating personalized explanation..."):
         try:
             response = requests.post(f"{API_ENDPOINT}/tutor",
                  json={
                     "subject": subject,
                     "level": level,
                     "learning_style": learning_style,
                     "language": language,
                     "background": background,
                     "question": question
                 }).json()
             
             if "response" in response:
                 st.success("Here's your personalized explanation:")
                 st.markdown(response["response"], unsafe_allow_html=True)
             else:
                 st.error("Unexpected response format. Please try again.")
                 st.info(f"Response: {response}")
         except Exception as e:
             st.error(f"Error getting explanation: {str(e)}")
             st.info(f"Make sure the backend server is running at {API_ENDPOINT}")


with tab2:
    # Quiz section
    st.header("Test Your Knowledge")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        num_questions = st.slider("Number of Questions", min_value=1, max_value=10, value=5)
        topic = st.text_input("🧑‍🏫 Enter Topic for Quiz", value="Algebra")  # Moved and changed to user input
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        quiz_button = st.button("Generate Quiz 📝", use_container_width=True)
    
    if quiz_button:
        with st.spinner("Creating quiz questions..."):
            try:
                response = requests.post(f"{API_ENDPOINT}/quiz",
                    json={
                        "subject": subject,
                        "topic": topic,
                        "level": level,
                        "num_questions": num_questions,
                        "reveal_format": True
                    }).json()
                
                st.success("Quiz generated! Try answering these questions:")
                
                if "formatted_quiz" in response and response["formatted_quiz"]:
                    html(response["formatted_quiz"], height=num_questions * 300)
                else:
                    for i, q in enumerate(response["quiz"]):
                        with st.expander(f"Question {i+1}: {q['question']}", expanded=True):
                            session_id = str(uuid.uuid4())
                            selected = st.radio(
                                "Select your answer:",
                                q["options"],
                                key=f"q_{session_id}"
                            )
                            if st.button("Check Answer", key=f"check_{session_id}"):
                                if selected == q["correct_answer"]:
                                    st.success(f"✅ Correct! {q.get('explanation', '')}")
                                else:
                                    st.error(f"❌ Incorrect. The correct answer is: {q['correct_answer']}")
                                    if "explanation" in q:
                                        st.info(q["explanation"])
            except Exception as e:
                st.error(f"Error generating quiz: {str(e)}")
                st.info(f"Make sure the backend server is running at {API_ENDPOINT}")

# Footer
st.markdown("---")
st.markdown("Powered by AI - Your Personal Learning Assistant")