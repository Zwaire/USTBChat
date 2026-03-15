import re

try:
    from ollama import Client
except Exception:  # pragma: no cover
    Client = None  # type: ignore

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


_LAST_OLLAMA_ERROR = ""
_CLIENT_HOST = ""
_CLIENT = None


def _truncate_text(text: str, max_len: int) -> str:
    if not text:
        return ""
    return text[:max_len]


def _extract_msg_text(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    return str(item.get("message") or item.get("groupmessage") or "").strip()


def _extract_username(item: dict) -> str:
    if not isinstance(item, dict):
        return "用户"
    return str(item.get("username") or item.get("sender_name") or "用户").strip()


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

    return _truncate_text("\n".join(lines), max_chars)


def _normalize_host(host: str, port: int) -> str:
    raw = str(host or "").strip()
    if not raw:
        raw = "127.0.0.1"

    if raw.startswith("http://") or raw.startswith("https://"):
        if re.search(r":\d+$", raw.split("//", 1)[-1]):
            return raw.rstrip("/")
        return f"{raw.rstrip('/')}:{port}"

    return f"http://{raw}:{port}"


def _extract_error_text(err: Exception) -> str:
    try:
        return str(err).strip()
    except Exception:
        return "未知错误"


def _extract_chat_content(resp) -> str:
    if isinstance(resp, dict):
        message = resp.get("message", {})
        if isinstance(message, dict):
            text = str(message.get("content", "") or "").strip()
            if text:
                return text
        return str(resp.get("content", "") or "").strip()

    message = getattr(resp, "message", None)
    if message is not None:
        text = str(getattr(message, "content", "") or "").strip()
        if text:
            return text

    return str(getattr(resp, "content", "") or "").strip()


def _extract_model_names(resp) -> list[str]:
    if isinstance(resp, dict):
        models = resp.get("models", [])
    else:
        models = getattr(resp, "models", [])

    names = []
    for item in models or []:
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("model") or "").strip()
        else:
            name = str(getattr(item, "name", None) or getattr(item, "model", None) or "").strip()
        if name:
            names.append(name)
    return names


def _get_client():
    global _CLIENT
    global _CLIENT_HOST
    global _LAST_OLLAMA_ERROR

    if Client is None:
        _LAST_OLLAMA_ERROR = "未安装 Python ollama 库"
        return None

    host = _normalize_host(OLLAMA_HOST, OLLAMA_PORT)
    if _CLIENT is not None and _CLIENT_HOST == host:
        return _CLIENT

    try:
        _CLIENT = Client(host=host, timeout=REQUEST_TIMEOUT)  # type: ignore[arg-type]
    except TypeError:
        try:
            _CLIENT = Client(host=host)  # type: ignore[arg-type]
        except Exception as e:
            _CLIENT = None
            _CLIENT_HOST = ""
            _LAST_OLLAMA_ERROR = _extract_error_text(e)
            return None
    except Exception as e:
        _CLIENT = None
        _CLIENT_HOST = ""
        _LAST_OLLAMA_ERROR = _extract_error_text(e)
        return None

    _CLIENT_HOST = host
    return _CLIENT


def _call_ollama(prompt: str, num_predict: int = 128) -> str:
    global _LAST_OLLAMA_ERROR

    _LAST_OLLAMA_ERROR = ""
    client = _get_client()
    if client is None:
        if not _LAST_OLLAMA_ERROR:
            _LAST_OLLAMA_ERROR = "Ollama 客户端初始化失败"
        return ""

    try:
        resp = client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            keep_alive="20m",
            options={
                "temperature": 0.2,
                "num_predict": num_predict,
            },
        )
        text = _extract_chat_content(resp)
        if not text:
            _LAST_OLLAMA_ERROR = "模型返回为空内容"
        return text
    except Exception as e:
        _LAST_OLLAMA_ERROR = _extract_error_text(e)
        return ""


def get_ollama_runtime_status() -> dict:
    global _LAST_OLLAMA_ERROR

    host = _normalize_host(OLLAMA_HOST, OLLAMA_PORT)
    model_ready = False
    available_models = []

    client = _get_client()
    if client is not None:
        try:
            model_list = client.list()
            available_models = _extract_model_names(model_list)
            model_ready = MODEL_NAME in available_models
            if not model_ready:
                _LAST_OLLAMA_ERROR = f"模型未拉取：{MODEL_NAME}"
        except Exception as e:
            _LAST_OLLAMA_ERROR = _extract_error_text(e)

    return {
        "sdk_available": Client is not None,
        "host": host,
        "configured_model": MODEL_NAME,
        "active_model": MODEL_NAME if model_ready else "",
        "available_models": available_models,
        "model_ready": model_ready,
        "last_error": _LAST_OLLAMA_ERROR,
    }


def _normalize_emotion(raw: str) -> str:
    raw = (raw or "").strip().lower()
    if raw in EMOTION_CONFIG:
        return raw

    mapping = {
        "平静": "calm",
        "愤怒": "angry",
        "开心": "happy",
        "悲伤": "sad",
        "害怕": "afraid",
    }
    return mapping.get(raw, DEFAULT_EMOTION)


def clean_trigger_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    if TRIGGER_NAME and text.startswith(TRIGGER_NAME):
        text = text[len(TRIGGER_NAME):].strip()

    while text[:1] in ["，", ",", "：", ":", " "]:
        text = text[1:].strip()

    return text


def generate_reply(scene: str, current_text: str, recent_messages: list | None = None) -> str:
    current_text = (current_text or "").strip()
    if not current_text:
        return "信息不足"

    question = clean_trigger_text(current_text)
    if not question:
        return "请说出你的问题。"

    recent_text = _join_recent_messages(recent_messages or [])
    prompt = build_reply_prompt(
        scene=scene,
        current_text=question,
        recent_text=recent_text,
        max_chars=MAX_REPLY_CHARS,
    )

    reply = _call_ollama(prompt, num_predict=128)
    if reply:
        return reply[:MAX_REPLY_CHARS]
    if _LAST_OLLAMA_ERROR:
        return f"AI服务暂时不可用：{_LAST_OLLAMA_ERROR[:120]}"
    return "AI服务未返回有效内容，请稍后重试。"


def summarize_file(scene: str, filename: str, content: str) -> str:
    filename = (filename or "未知文件").strip()
    content = (content or "").strip()

    if not content:
        return "文件内容为空，无法生成概要。"

    content = _truncate_text(content, MAX_FILE_CHARS)
    prompt = build_summary_prompt(
        scene=scene,
        filename=filename,
        content=content,
        max_chars=MAX_SUMMARY_CHARS,
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
