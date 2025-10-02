import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

def getLatex(b64Image):
    # noinspection PyTypeChecker
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "You will be provided with a screenshot of a math equation, and your task is to output the math equation as a TeX equation. You should output only the equation, with no other text or formatting *at all*"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{b64Image}"
                    }
                ]
            }
        ],
        text={
            "format": {
                "type": "text"
            }
        },
        reasoning={},
        tools=[],
        temperature=1,
        max_output_tokens=2048,
        top_p=1,
        store=True,
        include=["web_search_call.action.sources"]
    )
    return response.output_text