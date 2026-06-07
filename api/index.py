from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from io import StringIO
import traceback
import sys
import os
import json

from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str


class ErrorResponse(BaseModel):
    error_lines: list[int]


def execute_python_code(code):

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        exec(code)

        output = sys.stdout.getvalue()

        return {
            "success": True,
            "output": output
        }

    except Exception:

        output = traceback.format_exc()

        return {
            "success": False,
            "output": output
        }

    finally:
        sys.stdout = old_stdout

def analyze_error(code, tb):

    client = OpenAI(
        api_key=os.environ["eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDM3MjRAZHMuc3R1ZHkuaWl0bS5hYy5pbiIsImlhdCI6MTc4MDgyMTYwMSwiaXNzIjoiaHR0cHM6Ly9haXBpcGUub3JnIiwiYXVkIjoiYWlwaXBlLWFwaSIsImV4cCI6MTc4MTQyNjQwMX0.NK-BpreUs_oS-4VwHWbwrR0yBT656HYmq-GUhLF1fZ0"],
        base_url="https://aipipe.org/openai/v1"
    )

    prompt = f"""
Find the line numbers causing the error.

CODE:
{code}

TRACEBACK:
{tb}

Return JSON only.

Example:
{{"error_lines":[3]}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"}
    )

    data = json.loads(
        response.choices[0].message.content
    )

    return data["error_lines"]
    
@app.post("/code-interpreter")
def code_interpreter(req: CodeRequest):

    result = execute_python_code(req.code)

    if result["success"]:

        return {
            "error": [],
            "result": result["output"]
        }

    lines = analyze_error(
        req.code,
        result["output"]
    )

    return {
        "error": lines,
        "result": result["output"]
    }
