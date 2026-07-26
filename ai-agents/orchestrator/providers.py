"""
Provider registry for the Hermes orchestrator.

Each entry describes one provider: which pipeline script implements it,
and which environment variables it requires. This is metadata only —
no AI calls happen here.
"""

from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"

VALIDATION_PROVIDERS = {
    "claude": {
        "script": PIPELINE_DIR / "claude_validate.py",
        "required_env": ["CLAUDE_API_KEY"],
    },
    "groq": {
        "script": PIPELINE_DIR / "groq_validate.py",
        "required_env": ["GROQ_API_KEY"],
    },
    "deepseek": {
        "script": PIPELINE_DIR / "deepseek_validate.py",
        "required_env": ["DEEPSEEK_API_KEY"],
    },
}

REPORT_PROVIDERS = {
    "groq": {
        "script": PIPELINE_DIR / "chatgpt_report.py",
        "required_env": ["GROQ_API_KEY", "GROQ_REPORT_MODEL"],
    },
    "openai": {
        "script": PIPELINE_DIR / "chatgpt_report.py",
        "required_env": ["OPENAI_API_KEY", "OPENAI_MODEL"],
    },
}

PREPROCESS_SCRIPT = PIPELINE_DIR / "gemini_preprocess.py"
PREPROCESS_REQUIRED_ENV = ["GEMINI_API_KEY"]
