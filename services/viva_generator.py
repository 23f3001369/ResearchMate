from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()


def generate_viva_questions(paper_text):

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
Generate 15 viva questions from this research paper.

Include:
- Basic questions
- Methodology questions
- Result interpretation questions
- Critical thinking questions

Paper:

{paper_text[:10000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response.choices[0].message.content