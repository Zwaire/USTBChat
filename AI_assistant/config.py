OLLAMA_HOST = "192.168.1.1"
OLLAMA_PORT = 11434
MODEL_NAME = "qwen2.5:1.5b"

SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 5001

REQUEST_TIMEOUT = 60

EMOTION_CONFIG = {
    "calm":   {"label": "平静", "color": "#4287f5"},
    "angry":  {"label": "愤怒", "color": "#f54242"},
    "happy":  {"label": "开心", "color": "#f5d742"},
    "sad":    {"label": "悲伤", "color": "#888888"},
    "afraid": {"label": "害怕", "color": "#a042f5"},
}

DEFAULT_EMOTION = "calm"

MAX_REPLY_CHARS = 80
MAX_SUMMARY_CHARS = 140

MAX_CONTEXT_CHARS = 500
MAX_FILE_CHARS = 1000

TRIGGER_NAME = "@智能助手"

