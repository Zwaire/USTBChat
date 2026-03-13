import requests
import re

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
    TRIGGER_ALIASES,
)

from prompts import (
    build_reply_prompt,
    build_reply_rescue_prompt,
    build_summary_prompt,
    build_atmosphere_prompt,
)


_LAST_OLLAMA_ERROR = ""


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
    return str(item.get("message") or item.get("groupmessage") or "").strip()


def _extract_username(item: dict) -> str:
    """
    recent_messages 每项兼容以下字段：
    - username
    - sender_name
    """
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


def _call_ollama(prompt: str, num_predict: int = 128) -> str:
    global _LAST_OLLAMA_ERROR
    _LAST_OLLAMA_ERROR = ""

    # 先尝试 /api/chat（新式接口）
    try:
        url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "keep_alive": -1,
            "options": {
                "temperature": 0.2,
                "num_predict": num_predict,
            },
        }
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        if resp.ok:
            data = resp.json()
            text = str(data.get("message", {}).get("content", "")).strip()
            if text:
                return text
        else:
            _LAST_OLLAMA_ERROR = f"chat_http_{resp.status_code}"
    except Exception as e:
        _LAST_OLLAMA_ERROR = str(e)

    # 兼容旧版本：回退 /api/generate
    try:
        url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "keep_alive": -1,
            "options": {
                "temperature": 0.2,
                "num_predict": num_predict,
            },
        }
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        if resp.ok:
            data = resp.json()
            text = str(data.get("response", "")).strip()
            if text:
                _LAST_OLLAMA_ERROR = ""
                return text
        else:
            _LAST_OLLAMA_ERROR = f"generate_http_{resp.status_code}"
    except Exception as e:
        _LAST_OLLAMA_ERROR = str(e)

    return ""


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
        if alias:
            text = text.replace(alias, "").strip()

    # 简单清理常见符号
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

    if any(k in q for k in ["加好友", "添加好友"]):
        return "在主界面点“加好友”，输入对方UID并确认即可。"

    if any(k in q for k in ["建群", "创建群", "发起群聊"]):
        return "在主界面点“建群聊”，选择成员后确认；要加机器人就勾选“添加智能助手lulu”。"

    if "怎么运行" in q or ("运行" in q and "项目" in q):
        return "先启动数据库和 server_main.py，再启动 AI 服务，最后运行 client_main.py。"

    if any(k in q for k in ["报错", "错误", "异常", "失败"]):
        return "请贴完整报错和触发步骤，我可以帮你快速定位问题。"

    return ""


def _fallback_reply(question: str, max_chars: int = MAX_REPLY_CHARS) -> str:
    q = str(question or "").strip()
    if not q:
        return "请再具体描述你的问题。"
    rule = _rule_based_answer(q)
    if rule:
        return rule[:max_chars]
    if _LAST_OLLAMA_ERROR:
        return "当前模型未就绪，请先启动或检查Ollama服务与模型配置。"
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
