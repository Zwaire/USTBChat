import requests

from config import (
    OLLAMA_HOST,
    OLLAMA_PORT,
    MODEL_NAME,
    REQUEST_TIMEOUT,
    EMOTION_CONFIG,
    DEFAULT_EMOTION,
    MAX_REPLY_CHARS,
    MAX_SUMMARY_CHARS,
    MAX_CONTEXT_CHARS,
    MAX_FILE_CHARS,
    TRIGGER_NAME,
)
from prompts import (
    build_reply_prompt,
    build_summary_prompt,
    build_atmosphere_prompt,
)


def _truncate_text(text: str, max_len: int) -> str:
    if not text:
        return ""
    return text[:max_len]


def _extract_msg_text(item: dict) -> str:
    """
    recent_messages 每项兼容以下字段：
    - message
    - groupmessage
    """
    if not isinstance(item, dict):
        return ""
    return str(
        item.get("message")
        or item.get("groupmessage")
        or ""
    ).strip()


def _extract_username(item: dict) -> str:
    """
    recent_messages 每项兼容以下字段：
    - username
    - sender_name
    """
    if not isinstance(item, dict):
        return "用户"
    return str(
        item.get("username")
        or item.get("sender_name")
        or "用户"
    ).strip()


def _join_recent_messages(recent_messages: list, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if not recent_messages:
        return ""

    lines = []
    for item in recent_messages:
        if not isinstance(item, dict):
            continue
        username = _extract_username(item)
        msg = _extract_msg_text(item)
        if msg:
            lines.append(f"{username}：{msg}")

    text = "\n".join(lines)
    return _truncate_text(text, max_chars)


def _call_ollama(prompt: str, num_predict: int = 128) -> str:
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "keep_alive": -1,
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict,
        }
    }

    resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", {}).get("content", "").strip()


def _normalize_emotion(raw: str) -> str:
    raw = (raw or "").strip().lower()
    if raw in EMOTION_CONFIG:
        return raw

    mapping = {
        "平静": "calm",
        "愤怒": "angry",
        "生气": "angry",
        "开心": "happy",
        "高兴": "happy",
        "快乐": "happy",
        "悲伤": "sad",
        "伤心": "sad",
        "害怕": "afraid",
        "恐惧": "afraid",
        "紧张": "afraid",
    }
    return mapping.get(raw, DEFAULT_EMOTION)


def clean_trigger_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    text = text.replace(TRIGGER_NAME, "").strip()

    # 简单清理常见符号
    while text[:1] in ["，", ",", "：", ":", " "]:
        text = text[1:].strip()

    return text


def generate_reply(chat_type: str, current_text: str, recent_messages: list | None = None) -> str:
    current_text = (current_text or "").strip()
    if not current_text:
        return "信息不足"

    question = clean_trigger_text(current_text)
    if not question:
        return "请说出你的问题。"

    recent_text = _join_recent_messages(recent_messages or [])
    prompt = build_reply_prompt(
        chat_type=chat_type,
        current_text=question,
        recent_text=recent_text,
        max_chars=MAX_REPLY_CHARS
    )

    reply = _call_ollama(prompt, num_predict=128)
    if not reply:
        return "信息不足"

    return reply[:MAX_REPLY_CHARS]


def summarize_file(chat_type: str, filename: str, content: str) -> str:
    filename = (filename or "未知文件").strip()
    content = (content or "").strip()

    if not content:
        return "文件内容为空，无法生成概要。"

    content = _truncate_text(content, MAX_FILE_CHARS)

    prompt = build_summary_prompt(
        chat_type=chat_type,
        filename=filename,
        content=content,
        max_chars=MAX_SUMMARY_CHARS
    )

    summary = _call_ollama(prompt, num_predict=180)
    if not summary:
        return "未生成概要。"

    return summary[:MAX_SUMMARY_CHARS]


def analyze_atmosphere(recent_messages: list | None = None) -> dict:
    recent_messages = recent_messages or []
    if not recent_messages:
        emotion = DEFAULT_EMOTION
        return {
            "emotion": emotion,
            "label": EMOTION_CONFIG[emotion]["label"],
            "color": EMOTION_CONFIG[emotion]["color"],
        }

    recent_text = _join_recent_messages(recent_messages)
    if not recent_text:
        emotion = DEFAULT_EMOTION
        return {
            "emotion": emotion,
            "label": EMOTION_CONFIG[emotion]["label"],
            "color": EMOTION_CONFIG[emotion]["color"],
        }

    prompt = build_atmosphere_prompt(recent_text)
    raw = _call_ollama(prompt, num_predict=16)
    emotion = _normalize_emotion(raw)

    return {
        "emotion": emotion,
        "label": EMOTION_CONFIG[emotion]["label"],
        "color": EMOTION_CONFIG[emotion]["color"],
    }

