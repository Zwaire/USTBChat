import requests

class AIServiceClient:
    def __init__(self, base_url="http://192.168.182.128:5001", timeout=90):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            return resp.json()
        except Exception as e:
            return {
                "status": 1,
                "error": f"AI服务请求失败: {str(e)}"
            }

    def reply_private(self, username, friendname, message, recent_messages):
        payload = {
            "type": "ai_reply",
            "username": username,
            "friendname": friendname,
            "message": message,
            "recent_messages": recent_messages
        }
        return self._post("/ai/reply", payload)

    def reply_group(self, username, groupname, groupmessage, recent_messages):
        payload = {
            "type": "ai_reply",
            "username": username,
            "groupname": groupname,
            "groupmessage": groupmessage,
            "recent_messages": recent_messages
        }
        return self._post("/ai/reply", payload)

    def summarize_private(self, username, friendname, message, filename, content):
        payload = {
            "type": "ai_summary",
            "username": username,
            "friendname": friendname,
            "message": message,
            "filename": filename,
            "content": content
        }
        return self._post("/ai/summarize", payload)

    def summarize_group(self, username, groupname, groupmessage, filename, content):
        payload = {
            "type": "ai_summary",
            "username": username,
            "groupname": groupname,
            "groupmessage": groupmessage,
            "filename": filename,
            "content": content
        }
        return self._post("/ai/summarize", payload)

    def analyze_atmosphere(self, groupname, recent_messages):
        payload = {
            "type": "ai_atmosphere",
            "groupname": groupname,
            "recent_messages": recent_messages
        }
        return self._post("/ai/atmosphere", payload)
