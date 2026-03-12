from flask import Flask, request, jsonify

from config import (
    SERVICE_HOST,
    SERVICE_PORT,
    DEFAULT_EMOTION,
    EMOTION_CONFIG,
)

from ollama_client import (
    generate_reply,
    summarize_file,
    analyze_atmosphere,
)

app = Flask(__name__)
app.json.ensure_ascii = False


def _ok(resp_type: str, **kwargs):
    data = {
        "type": resp_type,
        "status": 0,
    }
    data.update(kwargs)
    return jsonify(data), 200


def _fail(resp_type: str, error: str, http_code: int = 400):
    return jsonify({
        "type": resp_type,
        "status": 1,
        "error": error
    }), http_code


def _get_json_data(resp_type: str):
    data = request.get_json(force=True, silent=False)
    if not isinstance(data, dict):
        return None, _fail(resp_type, "请求体必须是 JSON 对象")
    return data, None


def _validate_scene_message(data: dict, resp_type: str):
    """
    严格区分：
    - message = 私聊
    - groupmessage = 群聊
    二者互斥
    """
    has_message = "message" in data and str(data.get("message")).strip()
    has_groupmessage = "groupmessage" in data and str(data.get("groupmessage")).strip()

    if has_message and has_groupmessage:
        return None, None, _fail(resp_type, "不能同时传入message和groupmessage参数")

    if not has_message and not has_groupmessage:
        return None, None, _fail(resp_type, "必须传入message（私聊）或groupmessage（群聊）参数")

    if has_message:
        return "私聊", str(data.get("message")).strip(), None

    return "群聊", str(data.get("groupmessage")).strip(), None


def _validate_recent_messages(data: dict, resp_type: str):
    recent_messages = data.get("recent_messages", [])
    if recent_messages is None:
        recent_messages = []

    if not isinstance(recent_messages, list):
        return None, _fail(resp_type, "recent_messages 必须是数组")

    return recent_messages, None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "type": "health",
        "status": 0,
        "message": "assistant service is running"
    })


@app.route("/ai/reply", methods=["POST"])
def ai_reply():
    resp_type = "ai_reply"
    try:
        data, err = _get_json_data(resp_type)
        if err:
            return err

        scene, current_text, err = _validate_scene_message(data, resp_type)
        if err:
            return err

        recent_messages, err = _validate_recent_messages(data, resp_type)
        if err:
            return err

        reply = generate_reply(
            scene=scene,
            current_text=current_text,
            recent_messages=recent_messages,
        )
        return _ok(resp_type, reply=reply)

    except Exception as e:
        return _fail(resp_type, f"reply 接口异常：{str(e)}", 500)


@app.route("/ai/summarize", methods=["POST"])
def ai_summarize():
    resp_type = "ai_summary"
    try:
        data, err = _get_json_data(resp_type)
        if err:
            return err

        scene, _, err = _validate_scene_message(data, resp_type)
        if err:
            return err

        filename = str(data.get("filename") or "未知文件").strip()

        content = data.get("content", "")
        if content is None:
            content = ""
        content = str(content).strip()

        if not content:
            return _fail(resp_type, "content 不能为空")

        summary = summarize_file(
            scene=scene,
            filename=filename,
            content=content,
        )
        return _ok(resp_type, summary=summary)

    except Exception as e:
        return _fail(resp_type, f"summarize 接口异常：{str(e)}", 500)


@app.route("/ai/atmosphere", methods=["POST"])
def ai_atmosphere():
    resp_type = "ai_atmosphere"
    try:
        data, err = _get_json_data(resp_type)
        if err:
            return err

        groupname = str(data.get("groupname") or "").strip()
        if not groupname:
            return _fail(resp_type, "atmosphere 仅支持群聊，必须传入groupname参数")

        recent_messages, err = _validate_recent_messages(data, resp_type)
        if err:
            return err

        if not recent_messages:
            emotion = DEFAULT_EMOTION
            return _ok(
                resp_type,
                emotion=emotion,
                label=EMOTION_CONFIG[emotion]["label"],
                color=EMOTION_CONFIG[emotion]["color"],
            )

        result = analyze_atmosphere(recent_messages)
        return _ok(
            resp_type,
            emotion=result["emotion"],
            label=result["label"],
            color=result["color"],
        )

    except Exception as e:
        return _fail(resp_type, f"atmosphere 接口异常：{str(e)}", 500)


if __name__ == "__main__":
    app.run(host=SERVICE_HOST, port=SERVICE_PORT, debug=False)

