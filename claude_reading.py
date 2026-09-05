#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一気通貫鑑定 Blueprint
Narrative Astrologer (Evolution Ver.) の Gem 指示文を Claude API で実行する。
多ターン（章ごと進行）＋ストリーミング(SSE)。会話履歴はクライアントが保持し、
このエンドポイントはステートレスに動作する。
"""
import os
import json
from flask import Blueprint, request, Response, stream_with_context, jsonify
from anthropic import Anthropic

claude_reading = Blueprint('claude_reading', __name__)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Gem バージョン → (指示文ファイル, max_tokens)
# v1: Evolution Ver.（約12,000字・二部構成） / v2: 第2版（約20,000字・6ブロック自動進行）
_GEMS = {
    'v1': (os.path.join(_BASE_DIR, 'gem_narrative_astrologer.md'),
           int(os.environ.get('READING_MAX_TOKENS', '4000'))),
    'v2': (os.path.join(_BASE_DIR, 'gem_narrative_astrologer_v2.md'),
           int(os.environ.get('READING_MAX_TOKENS_V2', '12000'))),
}
DEFAULT_MODEL = os.environ.get('READING_MODEL', 'claude-sonnet-4-6')
MAX_TOKENS = _GEMS['v1'][1]

# 許可モデル（任意モデル注入を防ぐ）。既定は検証済みの Sonnet 4.6。
ALLOWED_MODELS = {
    'claude-sonnet-4-6',
    'claude-opus-4-8',
    'claude-haiku-4-5-20251001',
}


def _load_gem(version='v1'):
    path, _ = _GEMS.get(version, _GEMS['v1'])
    with open(path, encoding='utf-8') as f:
        return f.read()


@claude_reading.route('/api/reading/health', methods=['GET'])
def reading_health():
    """UIが鑑定機能の利用可否を確認するための軽量エンドポイント。"""
    return jsonify({
        'success': True,
        'configured': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'default_model': DEFAULT_MODEL,
        'gems': {v: os.path.exists(p) for v, (p, _) in _GEMS.items()},
        'gem_loaded': os.path.exists(_GEMS['v1'][0]),
    })


@claude_reading.route('/api/reading/stream', methods=['POST'])
def reading_stream():
    """
    Request (JSON):
      {
        "messages": [{"role":"user","content":"<チャートテキスト>"}, ...],
        "model": "claude-sonnet-4-6"   # 任意
      }
    Response: text/event-stream
      data: {"t": "<部分テキスト>"}
      ...
      data: {"done": true}
      （エラー時） data: {"error": "..."}
    """
    data = request.get_json(force=True, silent=True) or {}
    model = data.get('model') or DEFAULT_MODEL
    if model not in ALLOWED_MODELS:
        model = DEFAULT_MODEL
    gem_version = data.get('gem') if data.get('gem') in _GEMS else 'v1'
    max_tokens = _GEMS[gem_version][1]

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'success': False,
                        'error': 'ANTHROPIC_API_KEY が未設定です'}), 503

    messages = []
    for m in (data.get('messages') or []):
        role = m.get('role')
        content = m.get('content')
        if role in ('user', 'assistant') and isinstance(content, str) and content.strip():
            messages.append({'role': role, 'content': content})
    if not messages or messages[0]['role'] != 'user':
        return jsonify({'success': False,
                        'error': '最初のメッセージは user である必要があります'}), 400

    try:
        gem = _load_gem(gem_version)
    except OSError as e:
        return jsonify({'success': False, 'error': f'gem 読込失敗: {e}'}), 500

    client = Anthropic(api_key=api_key)

    def sse(obj):
        return 'data: ' + json.dumps(obj, ensure_ascii=False) + '\n\n'

    def generate():
        try:
            with client.messages.stream(model=model, max_tokens=max_tokens,
                                        system=gem, messages=messages) as stream:
                for text in stream.text_stream:
                    yield sse({'t': text})
            yield sse({'done': True})
        except Exception as e:  # noqa: BLE001 - クライアントへエラーを通知
            yield sse({'error': str(e)})

    return Response(stream_with_context(generate()),
                   mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                            'X-Accel-Buffering': 'no',
                            'Connection': 'keep-alive'})
