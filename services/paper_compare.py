from groq import Groq
import os

def compare_papers(text1,text2):

    client=Groq(
      api_key=os.getenv("GROQ_API_KEY")
    )

    prompt=f"""
Compare these two research papers.

Compare:

- Problem addressed
- Methodology
- Dataset
- Results
- Limitations

Paper 1:
{text1[:7000]}

Paper 2:
{text2[:7000]}
"""

    response=client.chat.completions.create(
      model="llama-3.3-70b-versatile",
      messages=[
         {
           "role":"user",
           "content":prompt
         }
      ]
    )

    return response.choices[0].message.content