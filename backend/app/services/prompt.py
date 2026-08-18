SYSTEM_PROMPT = (
    "You are a code reviewer. Given a code snippet, identify quality issues "
    "and respond with a JSON object containing a \"flaws\" list (each with "
    "\"issue\", \"severity\" [critical/major/minor], and \"line\") and a "
    "\"flaw_count\" field."
)

def base_prompt(prompt:str):
    return f"Review this python code and list any quality issues:\n\n```python\n{prompt}\n```"