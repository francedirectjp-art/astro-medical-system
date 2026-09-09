# -*- coding: utf-8 -*-
"""MyASP MCP の最小クライアント（自動鑑定書ワーカー用）

nexus-os/infra/scripts/myasp_event_status.py の実績あるパターンを移植。
環境変数 MYASP_API_KEY / MYASP_SERVER_URL を使う。
"""
import json
import os
import urllib.request

MCP_URL = "https://ai.myasp.jp/py-api/mcp"
DEFAULT_SERVER_URL = "https://frdirect-asp.com"


class MyASP:
    def __init__(self, api_key=None, server_url=None):
        api_key = api_key or os.environ.get("MYASP_API_KEY", "")
        server_url = server_url or os.environ.get("MYASP_SERVER_URL") or DEFAULT_SERVER_URL
        if not api_key:
            raise RuntimeError("MYASP_API_KEY が未設定")
        self.h = {"Content-Type": "application/json",
                  "Accept": "application/json, text/event-stream",
                  "X-MyASP-Server-URL": server_url,
                  "X-MyASP-API-Key": api_key}
        self.sid = None

    def _post(self, payload):
        h = dict(self.h)
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers=h)
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.headers.get("mcp-session-id"), r.read().decode()

    def connect(self):
        sid, _ = self._post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                             "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                        "clientInfo": {"name": "grand-vision-auto-reading",
                                                       "version": "1.0"}}})
        self.sid = sid
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return self

    def call(self, name, args):
        _, raw = self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                             "params": {"name": name, "arguments": args}})
        datas = [l[6:] for l in raw.splitlines() if l.startswith("data: ")]
        if datas:  # SSE(複数dataラインは結合)
            raw = "".join(datas)
        d = json.loads(raw)
        if "error" in d:
            raise RuntimeError(str(d["error"])[:300])
        content = d["result"]["content"][0]["text"]
        if d["result"].get("isError"):
            raise RuntimeError(content[:300])
        inner = json.loads(content)
        body = inner.get("result", inner)
        return json.loads(body) if isinstance(body, str) else body
