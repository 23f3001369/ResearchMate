from groq import Groq
import os

def generate_lit_review(texts):

    combined="\n\n".join(
       t[:3000] for t in texts
    )

    client=Groq(
      api_key=os.getenv("GROQ_API_KEY")
    )

    prompt=f"""
Generate a literature review using these papers.

Include:

- Major themes
- Similar findings
- Contradictions
- Research gaps
- Future directions

Papers:

{combined}
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