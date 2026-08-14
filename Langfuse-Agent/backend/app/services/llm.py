import os

from dotenv import load_dotenv
from openai import OpenAI
from langfuse import observe

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


@observe(as_type="generation")
def call_llm(
    system_prompt: str,
    user_prompt: str,
    operation_name: str = "llm_call",
) -> str:

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""