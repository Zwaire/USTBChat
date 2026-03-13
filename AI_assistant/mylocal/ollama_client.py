import re
from typing import Any

try:
    from ollama import Client, ResponseError
except Exception:  # pragma: no cover
    Client = None  # type: ignore
    ResponseError = Exception  # type: ignore

from config import (
    OLLAMA_HOST,
    OLLAMA_PORT,
    MODEL_NAME,
    FALLBACK_MODELS,
    REQUEST_TIMEOUT,
    EMOTION_CONFIG,
    DEFAULT_EMOTION,
    MAX_REPLY_CHARS,
    MAX_SUMMARY_CHARS,
    MAX_CONTEXT_CHARS,
    MAX_FILE_CHARS,
    TRIGGER_NAME,
    TRIGGER_ALIASES,
)

from prompts import (
    build_reply_prompt,
    build_reply_rescue_prompt,
    build_summary_prompt,
    build_atmosphere_prompt,
)


_LAST_OLLAMA_ERROR = ""
_ACTIVE_MODEL = ""
_CLIENT_HOST = ""
_CLIENT = None


def _truncate_text(text: str, max_len: int) -> str:
    if not text:
        return ""
    return text[:max_len]


def _obj_get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if obj is None:
        return {}
    # pydantic v2
    md = getattr(obj, "model_dump", None)
    if callable(md):
        try:
            data = md()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # pydantic v1
    dc = getattr(obj, "dict", None)
    if callable(dc):
        try:
            data = dc()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    data = getattr(obj, "__dict__", None)
    if isinstance(data, dict):
        return data
    return {}


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

    text = "\n".join(lines)
    return _truncate_text(text, max_chars)


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
        # 新版本一般支持 timeout
        _CLIENT = Client(host=host, timeout=REQUEST_TIMEOUT)  # type: ignore[arg-type]
    except TypeError:
        # 兼容旧版本 SDK：不支持 timeout 参数
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


def _extract_models_from_list_resp(data: Any) -> list[str]:
    models: list[str] = []
    container = None

    if isinstance(data, dict):
        container = data.get("models", [])
    else:
        container = getattr(data, "models", None)
        if container is None and isinstance(data, (list, tuple)):
            container = data

    if container is None:
        container = []

    for item in container:
        if isinstance(item, str):
            name = item.strip()
        else:
            name = str(
                _obj_get(item, "name")
                or _obj_get(item, "model")
                or _obj_get(item, "model_name")
                or ""
            ).strip()
            if not name:
                d = _to_dict(item)
                name = str(d.get("name") or d.get("model") or d.get("model_name") or "").strip()
        if name:
            models.append(name)

    # 去重保序
    seen = set()
    result = []
    for n in models:
        if n in seen:
            continue
        seen.add(n)
        result.append(n)
    return result


def _extract_chat_content(resp: Any) -> str:
    msg = _obj_get(resp, "message")
    content = str(_obj_get(msg, "content", "") or "").strip()
    if content:
        return content

    # 兼容某些返回结构
    content = str(_obj_get(resp, "content", "") or "").strip()
    if content:
        return content

    data = _to_dict(resp)
    if data:
        msg2 = data.get("message", {})
        if isinstance(msg2, dict):
            content = str(msg2.get("content", "") or "").strip()
            if content:
                return content
        content = str(data.get("content", "") or "").strip()
        if content:
            return content

    return ""


def _extract_generate_content(resp: Any) -> str:
    text = str(_obj_get(resp, "response", "") or "").strip()
    if text:
        return text

    data = _to_dict(resp)
    if data:
        text = str(data.get("response", "") or "").strip()
        if text:
            return text
    return ""


def _get_available_models() -> list[str]:
    global _LAST_OLLAMA_ERROR

    client = _get_client()
    if client is None:
        return []

    try:
        data = client.list()
        return _extract_models_from_list_resp(data)
    except Exception as e:
        _LAST_OLLAMA_ERROR = _extract_error_text(e)
        return []


def _build_model_candidates() -> list[str]:
    candidates = []
    if _ACTIVE_MODEL:
        candidates.append(_ACTIVE_MODEL)
    if MODEL_NAME:
        candidates.append(MODEL_NAME)
    candidates.extend(FALLBACK_MODELS or [])
    candidates.extend(_get_available_models())

    seen = set()
    result = []
    for item in candidates:
        name = str(item or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result


def _chat_with_model(client, model: str, prompt: str, num_predict: int = 128) -> str:
    resp = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        keep_alive="20m",
        options={
            "temperature": 0.2,
            "num_predict": num_predict,
        },
    )
    return _extract_chat_content(resp)


def _generate_with_model(client, model: str, prompt: str, num_predict: int = 128) -> str:
    resp = client.generate(
        model=model,
        prompt=prompt,
        stream=False,
        keep_alive="20m",
        options={
            "temperature": 0.2,
            "num_predict": num_predict,
        },
    )
    return _extract_generate_content(resp)


def _call_ollama_with_model(client, model: str, prompt: str, num_predict: int = 128) -> str:
    global _LAST_OLLAMA_ERROR

    try:
        text = _chat_with_model(client, model, prompt, num_predict)
        if text:
            return text
    except ResponseError as e:
        _LAST_OLLAMA_ERROR = _extract_error_text(e)
    except Exception as e:
        _LAST_OLLAMA_ERROR = _extract_error_text(e)

    try:
        text = _generate_with_model(client, model, prompt, num_predict)
        if text:
            return text
    except ResponseError as e:
        _LAST_OLLAMA_ERROR = _extract_error_text(e)
    except Exception as e:
        _LAST_OLLAMA_ERROR = _extract_error_text(e)

    return ""


def _call_ollama(prompt: str, num_predict: int = 128) -> str:
    global _LAST_OLLAMA_ERROR
    global _ACTIVE_MODEL

    _LAST_OLLAMA_ERROR = ""
    client = _get_client()
    if client is None:
        if not _LAST_OLLAMA_ERROR:
            _LAST_OLLAMA_ERROR = "Ollama 客户端初始化失败"
        return ""

    for model in _build_model_candidates():
        text = _call_ollama_with_model(client, model, prompt, num_predict)
        if text:
            _ACTIVE_MODEL = model
            _LAST_OLLAMA_ERROR = ""
            return text

    if not _LAST_OLLAMA_ERROR:
        _LAST_OLLAMA_ERROR = "未找到可用模型，请先执行 ollama pull <model>"
    return ""


def get_ollama_runtime_status() -> dict:
    """
    对外暴露运行时状态，便于 health/self-check 使用。
    """
    available_models = _get_available_models()
    host = _normalize_host(OLLAMA_HOST, OLLAMA_PORT)
    return {
        "sdk_available": Client is not None,
        "host": host,
        "configured_model": MODEL_NAME,
        "fallback_models": list(FALLBACK_MODELS or []),
        "active_model": _ACTIVE_MODEL,
        "available_models": available_models,
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

    aliases = [TRIGGER_NAME] + list(TRIGGER_ALIASES or [])
    for alias in aliases:
        if alias and text.startswith(alias):
            text = text[len(alias):].strip()
            break

    while text[:1] in ["，", ",", "：", ":", " "]:
        text = text[1:].strip()

    return text


def _is_unhelpful_reply(text: str) -> bool:
    reply = str(text or "").strip()
    if not reply:
        return True
    bad_exact = {"信息不足", "不知道", "我不知道", "无法回答", "不清楚"}
    if reply in bad_exact:
        return True
    bad_fragments = ("信息不足", "无法回答", "不清楚", "请再补充", "无法确定")
    return any(x in reply for x in bad_fragments)


def _simple_math_answer(question: str) -> str:
    q = str(question or "").strip().replace("等于几", "").replace("等于多少", "")
    m = re.search(r"(-?\d+)\s*([+\-*/])\s*(-?\d+)", q)
    if not m:
        return ""
    a = int(m.group(1))
    op = m.group(2)
    b = int(m.group(3))
    try:
        if op == "+":
            val = a + b
        elif op == "-":
            val = a - b
        elif op == "*":
            val = a * b
        else:
            if b == 0:
                return "除数不能为0。"
            val = a / b
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        return f"结果是 {val}。"
    except Exception:
        return ""


def _rule_based_answer(question: str) -> str:
    q = str(question or "").strip()
    if not q:
        return ""

    math_ans = _simple_math_answer(q)
    if math_ans:
        return math_ans

    if any(k in q for k in ["你好", "在吗", "嗨"]):
        return "你好，我是lulu。你可以直接问我问题，我会尽量给出可执行步骤。"
    if "mysql" in q.lower() and any(k in q for k in ["启动", "start", "运行"]):
        return "可先执行：sudo systemctl start mysql；再用 mysql -u root -p 登录。"
    if any(k in q for k in ["报错", "错误", "异常", "失败"]):
        return "请贴完整报错和触发步骤，我可以帮你快速定位问题。"

    m = re.match(r"^\s*什么是\s*(.+?)\s*$", q)
    if m:
        topic = m.group(1).strip("？?。!！")
        if topic:
            return f"{topic}通常指某个概念或技术对象。你可以告诉我使用场景，我再给你更准确的解释。"

    if "为什么" in q:
        return "常见原因包括配置不一致、依赖缺失或网络不可达。你可以贴现象和日志，我来帮你逐项排查。"
    if "区别" in q or "不同" in q:
        return "可以从定义、适用场景、优缺点三方面对比。你告诉我具体两个对象，我给你表格化结论。"

    return ""


def _fallback_reply(question: str, max_chars: int = MAX_REPLY_CHARS) -> str:
    q = str(question or "").strip()
    if not q:
        if Client is None:
            return "未安装 Python ollama 库，请先执行 pip install ollama。"
        return "请再具体描述你的问题。"

    rule = _rule_based_answer(q)
    if rule:
        return rule[:max_chars]

    if _LAST_OLLAMA_ERROR:
        short_err = _LAST_OLLAMA_ERROR[:120]
        return f"当前本地AI模型不可用：{short_err}"

    if any(k in q for k in ["怎么", "如何", "怎样"]):
        return "请补充你的目标和当前环境，我会给你步骤化方案。"

    return "我先理解到你的问题了，可以再补充你的目标和场景，我会给出更准确答案。"


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
    if _is_unhelpful_reply(reply):
        rescue_prompt = build_reply_rescue_prompt(question, max_chars=MAX_REPLY_CHARS)
        reply = _call_ollama(rescue_prompt, num_predict=160)

    if _is_unhelpful_reply(reply):
        return _fallback_reply(question, MAX_REPLY_CHARS)

    return reply[:MAX_REPLY_CHARS]


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
