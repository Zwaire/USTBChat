import os


OLLAMA_HOST = os.environ.get("USTBCHAT_OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.environ.get("USTBCHAT_OLLAMA_PORT", "11434"))
MODEL_NAME = os.environ.get("USTBCHAT_OLLAMA_MODEL", "qwen2.5:1.5b")

SERVICE_HOST = os.environ.get("USTBCHAT_AI_SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.environ.get("USTBCHAT_AI_SERVICE_PORT", "5001"))

REQUEST_TIMEOUT = int(os.environ.get("USTBCHAT_AI_TIMEOUT", "60"))

EMOTION_CONFIG = {
    "calm": {"label": "平静", "color": "#4287f5"},
    "angry": {"label": "愤怒", "color": "#f54242"},
    "happy": {"label": "开心", "color": "#f5d742"},
    "sad": {"label": "悲伤", "color": "#888888"},
    "afraid": {"label": "害怕", "color": "#a042f5"},
}

DEFAULT_EMOTION = "calm"

MAX_REPLY_CHARS = 80
MAX_SUMMARY_CHARS = 140
MAX_CONTEXT_CHARS = 500
MAX_FILE_CHARS = 1000

TRIGGER_NAME = os.environ.get("USTBCHAT_AI_TRIGGER", "@lulu")
