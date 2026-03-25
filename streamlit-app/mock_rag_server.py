"""
モック RAG サーバー

RAGサーバーが未実装の段階でアプリを動作確認するための開発用スクリプト。
クエリ内容にかかわらず固定のサンプルレスポンスを返す。

使い方:
    python mock_rag_server.py [--port PORT]

デフォルトポート: 9000 (.env の RAG_API_URL と合わせること)
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

MOCK_RESPONSE = {
    "objects": [
        {
            "obj_id": "person_01",
            "category": "person",
            "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"pose": "standing", "orientation": "upright"},
        },
        {
            "obj_id": "cup_01",
            "category": "cup",
            "first_seen_frame": 3,
            "first_seen_timestamp": "2024-01-15T10:23:45.100Z",
            "attributes": {
                "color": "red",
                "material": "ceramic",
                "position": "on_desk",
                "size": "small",
                "state": "filled",
            },
        },
        {
            "obj_id": "table_01",
            "category": "table",
            "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"material": "wooden", "size": "large"},
        },
    ],
    "events": [
        {
            "event_id": "evt_001",
            "frame": 5,
            "timestamp": "2024-01-15T10:23:45.167Z",
            "action": "pick_up",
            "agent": "person_01",
            "target": "cup_01",
            "source": "table_01",
            "destination": None,
        },
        {
            "event_id": "evt_002",
            "frame": 10,
            "timestamp": "2024-01-15T10:23:45.333Z",
            "action": "place_on",
            "agent": "person_01",
            "target": "cup_01",
            "source": None,
            "destination": "shelf_01",
        },
    ],
}


class RAGHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/query":
            self._send(404, {"error": f"Not found: {self.path}"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
            query = payload.get("query", "")
        except json.JSONDecodeError:
            self._send(400, {"error": "Invalid JSON"})
            return

        print(f"  query: {query!r}")
        self._send(200, MOCK_RESPONSE)

    def _send(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[mock-rag] {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="Mock RAG server for development")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), RAGHandler)
    print(f"Mock RAG server listening on http://0.0.0.0:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
