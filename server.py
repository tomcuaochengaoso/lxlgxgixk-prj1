"""Run PATRON locally without exposing the AI key in the browser.

The default adapter uses the OpenAI Chat Completions-compatible API. This is
supported by OpenAI, OpenRouter, Groq, DeepSeek and many other providers.
Set AI_PROVIDER=anthropic for the native Anthropic Messages API.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Tiny .env reader so the project has no third-party dependencies."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()


class ApiError(Exception):
    pass


def config(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def require_config() -> tuple[str, str, str, str]:
    provider = config("AI_PROVIDER", "openai_compatible").lower()
    base_url = config("AI_BASE_URL")
    api_key = config("AI_API_KEY")
    model = config("AI_MODEL")
    if not all((base_url, api_key, model)):
        raise ApiError("Chua cau hinh AI. Hay tao file .env tu .env.example va dien AI_BASE_URL, AI_API_KEY, AI_MODEL.")
    if provider not in {"openai_compatible", "anthropic"}:
        raise ApiError("AI_PROVIDER chi nhan openai_compatible hoac anthropic.")
    return provider, base_url.rstrip("/"), api_key, model


def request_json(url: str, headers: dict[str, str], body: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ApiError(f"AI API tra ve HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"Khong ket noi duoc toi AI API: {exc.reason}") from exc


def text_from_openai(data: dict) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ApiError("AI API tra ve dinh dang khong ho tro: " + json.dumps(data)[:300]) from exc
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(item.get("text", "") for item in content if isinstance(item, dict)).strip()
    raise ApiError("AI API khong tra ve noi dung text.")


def text_from_anthropic(data: dict) -> str:
    return "\n".join(
        block.get("text", "") for block in data.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text"
    ).strip()


def chat(prompt: str, search: bool = False) -> str:
    provider, base_url, api_key, model = require_config()
    if provider == "anthropic":
        body = {"model": model, "max_tokens": 3000 if search else 1000,
                "messages": [{"role": "user", "content": prompt}]}
        if search:
            body["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
        data = request_json(
            f"{base_url}/v1/messages",
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"}, body,
        )
        text = text_from_anthropic(data)
    elif search:
        # Generic compatible APIs do not share one standard for web search.
        if config("AI_SEARCH_MODE", "off").lower() != "openai_responses":
            raise ApiError(
                "Web search chua duoc cau hinh. Dung OpenAI thi dat AI_SEARCH_MODE=openai_responses; "
                "dung Claude thi dat AI_PROVIDER=anthropic. Cac API compatible khac can co cong cu search rieng."
            )
        responses_url = (
            base_url.rsplit("/", 1)[0] + "/responses"
            if base_url.endswith("/v1") else f"{base_url}/responses"
        )
        data = request_json(
            responses_url,
            {"Authorization": f"Bearer {api_key}"},
            {"model": model, "input": prompt, "tools": [{"type": "web_search_preview"}]},
        )
        text = data.get("output_text", "").strip()
    else:
        data = request_json(
            f"{base_url}/chat/completions",
            {"Authorization": f"Bearer {api_key}"},
            {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1000},
        )
        text = text_from_openai(data)
    if not text:
        raise ApiError("AI khong tra ve text. Thu doi model hoac kiem tra cau hinh API.")
    return text


class AppHandler(SimpleHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path not in {"/api/chat", "/api/search"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            prompt = payload.get("prompt", "")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ApiError("Prompt khong hop le.")
            self.send_json(HTTPStatus.OK, {"text": chat(prompt, search=self.path == "/api/search")})
        except (json.JSONDecodeError, ApiError) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:  # Do not send stack traces or keys to the browser.
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Server error: {exc}"})

    def send_json(self, status: HTTPStatus, body: dict) -> None:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args: object) -> None:
        print("[PATRON] " + (fmt % args))


if __name__ == "__main__":
    os.chdir(ROOT)
    port = int(config("PORT", "8000"))
    print(f"PATRON dang chay tai http://127.0.0.1:{port}")
    print("Nhan Ctrl+C de dung server.")
    ThreadingHTTPServer(("127.0.0.1", port), AppHandler).serve_forever()
