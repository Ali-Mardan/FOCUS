import json
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

PROMPT_TEMPLATE = """You are a productivity planner. The user wants to: {goal}

Break this into 4-6 concrete, actionable steps.
For each step, list which app window title keywords or exe name substrings would be expected.

Examples of allowed_apps keywords: "winword", "docs.google", "excel", "pycharm", "vscode", "terminal", "cmd", "linkedin", "github", "stackoverflow", "notion", "figma", "chrome", "firefox", "sticky", "onenote", "evernote", "notepad", "obsidian", "roam", "logseq", "bear", "apple notes", "samsung notes"

For note-taking steps always include: "sticky", "onenote", "notepad", "notion", "evernote", "obsidian"
For reading/research steps always include: "chrome", "firefox", "edge", "pdf", "acrobat", "kindle"
For writing steps always include: "winword", "docs.google", "notion", "notepad", "typora"
For coding steps always include: "vscode", "pycharm", "terminal", "cmd", "github"

Do not add generic keywords like "focus" or "window" to allowed_apps.

Respond ONLY with valid JSON, no explanation, no markdown:
{{
  "steps": [
    {{
      "step": "Description of what to do",
      "allowed_apps": ["keyword1", "keyword2"]
    }}
  ]
}}"""


def generate_plan(goal: str) -> list[dict]:
    prompt = PROMPT_TEMPLATE.format(goal=goal)

    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())

    raw = result["response"].strip()
    data = json.loads(raw)
    return data["steps"]
