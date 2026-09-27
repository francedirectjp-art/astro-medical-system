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
            # ★2026-09-26: read() 一発だと Railway 上で応答が途中で切れることがあり、
            #   壊れたJSON ("Unterminated string") になっていた。最後まで読み切る。
            buf = bytearray()
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                buf.extend(chunk)
            return r.headers.get("mcp-session-id"), bytes(buf).decode("utf-8", "replace")

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
        # SSE は 1イベント = 1 data 行。進捗通知などが混ざることがあるので、
        # 1行ずつ読んで「応答(result か error を持つもの)」を拾う。
        # ★2026-09-26: 全部を連結していたため、行が増えると壊れたJSONになり
        #   "Unterminated string" で落ちていた (件数の多いシナリオで発生)。
        lines = [l[6:] for l in raw.splitlines() if l.startswith("data: ")]
        cands = []
        for l in lines:
            try:
                cands.append(json.loads(l))
            except Exception:  # noqa: BLE001
                continue
        if not cands:
            try:
                cands.append(json.loads("".join(lines) if lines else raw))
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(f"MyASP の応答を読めませんでした: {e}") from e
        d = next((c for c in cands
                  if isinstance(c, dict) and ("result" in c or "error" in c)), None)
        if d is None:
            raise RuntimeError("MyASP の応答に result がありませんでした")
        if "error" in d:
            raise RuntimeError(str(d["error"])[:300])
        content = d["result"]["content"][0]["text"]
        if d["result"].get("isError"):
            raise RuntimeError(content[:300])
        inner = json.loads(content)
        body = inner.get("result", inner)
        return json.loads(body) if isinstance(body, str) else body
