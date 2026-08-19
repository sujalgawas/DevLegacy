SYSTEM_PROMPT = (
    "You are a code reviewer. Given a code snippet, identify quality issues "
    "and respond with a JSON object containing a \"flaws\" list (each with "
    "\"issue\", \"severity\" [critical/major/minor], and \"line\") and a "
    "\"flaw_count\" field. Respond with valid JSON only — no explanation text."
)


def base_prompt(code: str, language: str = "python") -> str:
    """Build the user-facing review prompt with language-aware fence block."""
    return f"Review this {language} code and list any quality issues:\n\n```{language}\n{code}\n```"