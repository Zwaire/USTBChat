#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用 Python ollama 库测试本地 Qwen 模型连通性。

示例：
python3 AI_assistant/mylocal/ollama_connect_test.py
python3 AI_assistant/mylocal/ollama_connect_test.py --model qwen2.5:7b --count 5
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time

try:
    from ollama import Client
except Exception:
    Client = None  # type: ignore


def _info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _ok(msg: str) -> None:
    print(f"[ OK ] {msg}")


def _err(msg: str) -> None:
    print(f"[ERROR] {msg}")


def _build_host(host: str, port: int) -> str:
    host = str(host or "").strip()
    if not host:
        host = "127.0.0.1"

    if host.startswith("http://") or host.startswith("https://"):
        if re.search(r":\d+$", host.split("//", 1)[-1]):
            return host.rstrip("/")
        return f"{host.rstrip('/')}:{port}"

    return f"http://{host}:{port}"


def _extract_model_names(resp) -> list[str]:
    if isinstance(resp, dict):
        items = resp.get("models", [])
    else:
        items = getattr(resp, "models", [])

    names = []
    for item in items or []:
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("model") or "").strip()
        else:
            name = str(getattr(item, "name", None) or getattr(item, "model", None) or "").strip()
        if name:
            names.append(name)
    return names


def _extract_reply(resp) -> str:
    if isinstance(resp, dict):
        return str(resp.get("message", {}).get("content", "")).strip()

    message = getattr(resp, "message", None)
    if message is None:
        return ""

    return str(getattr(message, "content", "") or "").strip()


def run_test(host: str, port: int, model: str, timeout: int, count: int, interval: float, prompt: str) -> int:
    if Client is None:
        _err("未安装 Python ollama 库。请先执行：pip install ollama")
        return 10

    endpoint = _build_host(host, port)
    _info(f"Ollama endpoint: {endpoint}")
    _info(f"目标模型: {model}")

    try:
        client = Client(host=endpoint, timeout=timeout)  # type: ignore[arg-type]
    except TypeError:
        try:
            client = Client(host=endpoint)  # type: ignore[arg-type]
        except Exception as e:
            _err(f"创建 Ollama 客户端失败: {e}")
            return 1
    except Exception as e:
        _err(f"创建 Ollama 客户端失败: {e}")
        return 1

    try:
        model_list = client.list()
        local_models = _extract_model_names(model_list)
    except Exception as e:
        _err(f"无法连接 Ollama 或读取模型列表失败: {e}")
        return 2

    if model not in local_models:
        _err(f"本地未找到模型：{model}")
        _info(f"请先执行：ollama pull {model}")
        if local_models:
            _info("当前本地模型：")
            for idx, name in enumerate(local_models[:10], start=1):
                print(f"      {idx}. {name}")
        return 3

    failures = 0
    for i in range(1, count + 1):
        content = f"{prompt}（第{i}轮）"
        t0 = time.time()
        try:
            resp = client.chat(
                model=model,
                messages=[{"role": "user", "content": content}],
                stream=False,
                keep_alive="20m",
                options={"temperature": 0.2, "num_predict": 80},
            )
            reply = _extract_reply(resp)
            if not reply:
                raise RuntimeError("模型返回为空")
            cost = int((time.time() - t0) * 1000)
            _ok(f"第{i}/{count}轮成功，耗时 {cost} ms，回复: {reply[:120]}")
        except Exception as e:
            failures += 1
            _err(f"第{i}/{count}轮失败: {e}")

        if i < count and interval > 0:
            time.sleep(interval)

    if failures == 0:
        _ok("测试通过：本地 Qwen 模型可连接并持续通信。")
        return 0

    _err(f"测试完成：{failures}/{count} 轮失败。")
    return 5


def main() -> int:
    parser = argparse.ArgumentParser(description="测试本地 Qwen 模型连通性与持续通信")
    parser.add_argument("--host", default=os.environ.get("USTBCHAT_OLLAMA_HOST", "127.0.0.1"), help="Ollama 主机")
    parser.add_argument("--port", type=int, default=int(os.environ.get("USTBCHAT_OLLAMA_PORT", "11434")), help="Ollama 端口")
    parser.add_argument("--model", default=os.environ.get("USTBCHAT_OLLAMA_MODEL", "qwen2.5:1.5b"), help="模型名")
    parser.add_argument("--timeout", type=int, default=25, help="请求超时（秒）")
    parser.add_argument("--count", type=int, default=3, help="持续通信轮数")
    parser.add_argument("--interval", type=float, default=1.0, help="轮次间隔（秒）")
    parser.add_argument("--prompt", default="你好，请回复“连接成功”", help="测试提示词")
    args = parser.parse_args()

    if args.count <= 0:
        _err("--count 必须 > 0")
        return 9
    if args.port <= 0 or args.port > 65535:
        _err("--port 必须在 1~65535")
        return 9

    return run_test(
        host=args.host,
        port=args.port,
        model=args.model,
        timeout=args.timeout,
        count=args.count,
        interval=args.interval,
        prompt=args.prompt,
    )


if __name__ == "__main__":
    sys.exit(main())
