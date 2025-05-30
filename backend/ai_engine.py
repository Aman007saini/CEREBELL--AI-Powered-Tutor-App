## importing necessary imports
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s- %(message)s')
logger= logging.getLogger(__name__)

#loading the key
load_dotenv()
OPENAI_API_KEY= os.getenv('OPENAI_API_KEY')

# making connectivity of LLM with OpenAI
def get_llm():
    try:
        return ChatOpenAI(temperature=0.7, 
                          model_name='gpt-3.5-turbo',
                          openai_api_key= OPENAI_API_KEY
        )
    except Exception as e:
        logger.error(f'Error initializing LLM:{str(e)}')

def generate_tutoring_response(subject, level, question, learning_style, background, language):
    """
    Generating a tutor response
    
    Args:
    subject(str): The academic subject
    level(str): Learning level (Begineer, Intermediate, Advanced)
    question(str): User's specific question
    learning_style (str): Preferred learning style (Visual, Text-based, Hands-on)
    background(str): User's Background knowledge
    language(str): Preferred language for response
    
    Returns:
    str: Formatted tutoring response"""

    try:
        # get LLM instance
        llm= get_llm()

        # Construct an effective prompt
        prompt= _create_tutoring_prompt(subject, level, question, learning_style, background, language)

        # error handling
        logger.info(f'Generating tutoring response for subject:{subject}, level:{level}')
        response= llm([HumanMessage(content=prompt)])

        return _format_tutoring_response(response.content, learning_style)
    except Exception as e:
        logger.error(f'Error generating tutoring response:{str(e)}')
        raise Exception(f'Failed to generate tutoring response:{str(e)}')


# function to creating a structured prompt to pass in the OpenAI
def _create_tutoring_prompt(subject, level, question, learning_style, background, language):
    # Building the prompt
    prompt = f"""
You are an expert AI tutor. Help the student learn the following topic based on their preferences.

Subject: {subject}
Learning Level: {level}
User's Question: {question}
Preferred Learning Style: {learning_style}
Background Knowledge: {background}
Language: {language}

Instructions:
1. Respond clearly and concisely in {language}.
2. Tailor the explanation to a {level} learner.
3. Adapt to the user's learning style:
   - If 'Visual', describe with diagrams, examples, or flowcharts (describe them in text).
   - If 'Text-based', explain using step-by-step written logic.
   - If 'Hands-on', include interactive exercises or simple tasks to try.
4. Avoid technical jargon unless it's appropriate for the user's background.
5. End with a quick quiz or summary to reinforce the key idea.

Start your response now:
"""
    return prompt

# function to format the response    ## from Chatgpt
def _format_tutoring_response(content, learning_style):
    if learning_style=='Visual':
        return content +'\n\n* Note: Visualize these concepts as you read for better retention.*'+ '\n\n* Happy Learning!*'
    elif learning_style=='Hands-on':
        return content+ '\n\n* Tip: Try working through the examples youself to reinforce you learning.*'+ '\n\n* Happy Learning!*'
    else:
        return content+ '\n\n* Happy Learning!*'
    
## code for generating quiz
def _create_quiz_prompt(subject, topic, level, num_questions):
    return f"""
You are a professional educational content creator. Generate a quiz on the following:

Subject: {subject}
Topic: {topic}
Learning Level: {level}
Number of Questions: {num_questions}

Instructions:
1. Create {num_questions} multiple-choice questions (MCQs) that thoroughly cover all key subtopics and concepts within the topic of "{topic}" under the subject "{subject}".
2. Each question should:
   - Match the {level} level of difficulty.
   - Test understanding of a different part of the topic.
   - Include 4 answer options (A, B, C, D) with only one correct answer.
   - Include the correct answer key and a brief explanation.
3. Questions should avoid repetition and increase in complexity where possible.
4. Keep language clear and concise.

Output Format:
Return only a valid JSON array with the following structure for each question:
[
  {{
    "question": "...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "..."
  }}
]
Do not include any extra commentary or markdown formatting.
"""

# Fallback quiz generator
def _create_fallback_quiz(subject, topic, num_questions):
    logger.warning(f'Using fallback quiz for {subject}')
    return [
        {
            'question': f'Sample question on {topic} in {subject} #{i + 1}',
            'options': ['Option A', 'Option B', 'Option C', 'Option D'],
            'correct_answer': 'Option A',
            'explanation': 'This is a fallback explanation.'
        }
        for i in range(num_questions)
    ]

# Validate quiz structure
def _validate_quiz_data(quiz_data):
    if not isinstance(quiz_data, list):
        raise ValueError('Quiz data must be a list of questions')
    for q in quiz_data:
        if not isinstance(q, dict):
            raise ValueError('Each question must be a dictionary')
        if not all(k in q for k in ['question', 'options', 'correct_answer']):
            raise ValueError('Missing required fields in quiz question')
        if not isinstance(q['options'], list) or len(q['options']) != 4:
            raise ValueError('Each question must have exactly 4 options')

# Parse quiz from LLM response
def _parse_quiz_response(response_content, subject, topic, num_questions):
    try:
        logger.debug(f"Raw LLM response: {response_content}")

        # Attempt to extract a JSON array
        json_match = re.search(r'(\[\s*\{[\s\S]*?\}\s*\])', response_content)
        quiz_json = json_match.group(1) if json_match else response_content

        quiz_data = json.loads(quiz_json)

        _validate_quiz_data(quiz_data)

        if len(quiz_data) > num_questions:
            quiz_data = quiz_data[:num_questions]

        # Add missing explanation if needed
        for question in quiz_data:
            if 'explanation' not in question:
                question['explanation'] = f"The correct answer is {question['correct_answer']}."

        return quiz_data

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Quiz parsing failed: {e}")
        return _create_fallback_quiz(subject, topic, num_questions)

# Main generation function
def generate_quiz(subject, topic, level, num_questions=5, reveal_answer=True):
    try:
        llm = get_llm()
        prompt = _create_quiz_prompt(subject, topic, level, num_questions)
        logger.info(f"Generating quiz: {subject}, {topic}, {level}, {num_questions}")

        response = llm([HumanMessage(content=prompt)])
        logger.debug(f"LLM Response: {response.content}")

        quiz_data = _parse_quiz_response(response.content, subject, topic, num_questions)

        if reveal_answer:
            formatted = _format_quiz_with_reveal(quiz_data)
            return {"quiz_data": quiz_data, "formatted_quiz": formatted}
        return {"quiz_data": quiz_data}

    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise Exception(f"Failed to generate quiz: {e}")


#fromating the quize   ## chatgpt
def _format_quiz_with_reveal(quiz_data):
    """
    Format quiz data into HTML with hidden answers that can be revealed on click.
    
    Args:
        quiz_data (list): List of question dictionaries
        
    Returns:
        str: HTML string with quiz questions and hidden answers
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                color: white;
                background-color: #121212;
            }
            .quiz-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .question {
                margin-bottom: 30px;
                padding: 20px;
                border: 1px solid #444;
                border-radius: 10px;
                background-color: #1e1e2f;
            }
            .question h3 {
                margin-top: 0;
                color: #90caf9;
            }
            .options {
                margin-left: 10px;
            }
            .option {
                margin: 10px 0;
                padding: 12px;
                border: 1px solid #555;
                border-radius: 6px;
                cursor: pointer;
                background-color: #2d2d44;
                transition: background-color 0.2s;
            }
            .option:hover {
                background-color: #3a3a5a;
            }
            .reveal-btn {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin-top: 15px;
                transition: background-color 0.2s;
            }
            .reveal-btn:hover {
                background-color: #0d8bf2;
            }
            .answer-section {
                margin-top: 20px;
                border: 2px solid #ffeb3b;
                border-radius: 8px;
                padding: 0;
                overflow: hidden;
                display: none;
            }
            .answer-header {
                background-color: #ffeb3b;
                color: #000;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;
                text-align: center;
            }
            .answer-content {
                padding: 15px;
                background-color: #1a237e;
            }
            .correct-answer {
                font-size: 18px;
                font-weight: bold;
                color: white;
                margin-bottom: 15px;
            }
            .explanation {
                color: #e1f5fe;
                font-size: 16px;
                line-height: 1.5;
            }
            .selected-correct {
                background-color: #1b5e20 !important;
                border-color: #4caf50 !important;
            }
            .selected-incorrect {
                background-color: #b71c1c !important;
                border-color: #f44336 !important;
            }
        </style>
    </head>
    <body>
        <div class="quiz-container">
            <h2 style="color: #2196f3; text-align: center; margin-bottom: 30px;">Interactive Quiz</h2>
    """
    
    for i, question in enumerate(quiz_data, 1):
        option_letters = ["A", "B", "C", "D"]
        correct_index = question["options"].index(question["correct_answer"]) if question["correct_answer"] in question["options"] else 0
        
        html += f"""
            <div class="question" id="question-{i}">
                <h3>Question {i}</h3>
                <p>{question["question"]}</p>
                <div class="options">
        """
        
        for j, option in enumerate(question["options"]):
            is_correct = j == correct_index
            html += f"""
                    <div class="option" id="option-{i}-{j}" onclick="selectOption({i}, {j}, {is_correct})">
                        <strong>{option_letters[j]}.</strong> {option}
                    </div>
            """
        
        html += f"""
                </div>
                <button class="reveal-btn" onclick="revealAnswer({i})">SHOW ANSWER</button>
                <div class="answer-section" id="answer-{i}">
                    <div class="answer-header">CORRECT ANSWER</div>
                    <div class="answer-content">
                        <div class="correct-answer">{option_letters[correct_index]}. {question["correct_answer"]}</div>
                        <div class="explanation">{question.get("explanation", "")}</div>
                    </div>
                </div>
            </div>
        """
    
    html += """
        </div>
        <script>
            function selectOption(questionNum, optionNum, isCorrect) {
                const questionId = `question-${questionNum}`;
                const options = document.querySelectorAll(`#${questionId} .option`);
                
                // Reset all options
                options.forEach(option => {
                    option.className = 'option';
                });
                
                // Highlight selected option
                const selectedOption = document.getElementById(`option-${questionNum}-${optionNum}`);
                if (isCorrect) {
                    selectedOption.className = 'option selected-correct';
                } else {
                    selectedOption.className = 'option selected-incorrect';
                    // Show answer if incorrect
                    revealAnswer(questionNum);
                }
            }
            
            function revealAnswer(questionNum) {
                const answerDiv = document.getElementById(`answer-${questionNum}`);
                answerDiv.style.display = 'block';
                
                // Scroll to answer
                setTimeout(() => {
                    answerDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
                
                // Add animation for attention
                answerDiv.animate([
                    { transform: 'scale(1)', boxShadow: '0 0 0 rgba(255, 235, 59, 0)' },
                    { transform: 'scale(1.03)', boxShadow: '0 0 20px rgba(255, 235, 59, 0.7)' },
                    { transform: 'scale(1)', boxShadow: '0 0 10px rgba(255, 235, 59, 0.3)' }
                ], {
                    duration: 1000,
                    iterations: 1
                });
            }
        </script>
    </body>
    </html>
    """
    
    return html


# Export quiz to file (new function)
def export_quiz_to_html(quiz_data, file_path="quiz.html"):
    """
    Export the formatted quiz to an HTML file
    
    Args:
        quiz_data (list): List of question dictionaries
        file_path (str): Path to save the HTML file
    """
    try:
        html_content = _format_quiz_with_reveal(quiz_data)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Quiz exported successfully to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error exporting quiz to HTML: {str(e)}")
        return False
