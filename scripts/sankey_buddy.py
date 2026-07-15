#!/usr/bin/env python3
"""Portable SankeyBuddy client: upload, SVG save, and resilient PNG export."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
LOCAL_MANIFEST = SKILL_DIR / "manifest.json"
CONFIG_DIR = Path(
    os.environ.get("SANKEY_BUDDY_CONFIG_DIR", Path.home() / ".config" / "sankey-buddy")
)
CACHE_DIR = Path(
    os.environ.get("SANKEY_BUDDY_CACHE_DIR", Path.home() / ".cache" / "sankey-buddy")
)
PENDING_UPDATE = CACHE_DIR / "pending-update.json"
SUPPORTED_EXTENSIONS = {
    ".pdf", ".html", ".htm", ".csv", ".tsv", ".xls", ".xlsx",
    ".doc", ".docx", ".txt", ".md",
}
MAX_FILE_BYTES = 20 * 1024 * 1024


class SankeyBuddyError(RuntimeError):
    pass


def emit(stage: str, zh: str, en: str, **extra: Any) -> None:
    payload = {"type": "progress", "stage": stage, "message": zh, "message_en": en}
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SankeyBuddyError(f"Expected a JSON object: {path}")
    return value


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def install_id() -> str:
    path = CONFIG_DIR / "install-id"
    try:
        value = path.read_text(encoding="utf-8").strip()
        uuid.UUID(value)
        return value
    except (OSError, ValueError):
        value = str(uuid.uuid4())
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value + "\n", encoding="utf-8")
        except OSError:
            pass
        return value


def detect_platform(manifest: dict[str, Any], explicit: str | None) -> str:
    configured = explicit or os.environ.get("SANKEY_BUDDY_PLATFORM")
    if configured:
        return configured.strip().lower()
    if os.environ.get("CLAUDECODE") == "1":
        return "claude"
    if any(os.environ.get(name) for name in ("CODEX_THREAD_ID", "CODEX_CI", "CODEX_HOME")):
        return "codex"
    if any(name.startswith(("WORKBUDDY_", "CODEBUDDY_")) for name in os.environ):
        return "workbuddy"
    return str(manifest.get("channel") or "direct").strip().lower()


def version_tuple(value: str) -> tuple[int, int, int]:
    core = value.split("-", 1)[0].split("+", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        return (0, 0, 0)
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def request_json(request: urllib.request.Request, timeout: int) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = {"error": body}
        code = detail.get("code", f"HTTP_{exc.code}")
        message = detail.get("error", body)
        raise SankeyBuddyError(f"{code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise SankeyBuddyError(f"NETWORK_ERROR: {exc.reason}") from exc
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SankeyBuddyError("INVALID_SERVER_RESPONSE: expected JSON") from exc
    if not isinstance(value, dict):
        raise SankeyBuddyError("INVALID_SERVER_RESPONSE: expected an object")
    return value


def client_headers(manifest: dict[str, Any], platform: str) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": f"SankeyBuddy/{manifest['version']}",
        "X-SankeyBuddy-Version": str(manifest["version"]),
        "X-SankeyBuddy-Platform": platform,
        "X-SankeyBuddy-Channel": str(manifest.get("channel") or "direct"),
        "X-SankeyBuddy-Install-ID": install_id(),
        "X-SankeyBuddy-Protocol": str(manifest.get("protocol_version", 1)),
    }
    api_key = os.environ.get("SANKEY_BUDDY_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def check_version(
    api_base: str, manifest: dict[str, Any], platform: str, timeout: int
) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        {"current_version": manifest["version"], "platform": platform}
    )
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/api/skill/manifest?{query}",
        headers=client_headers(manifest, platform),
    )
    try:
        remote = request_json(request, timeout)
    except SankeyBuddyError as exc:
        emit(
            "service-check-unavailable",
            "暂时无法读取服务状态，将继续处理当前任务",
            "The service status is unavailable; continuing with the current task",
            warning=str(exc),
        )
        return {
            "skill": "sankey-buddy-skill",
            "latest_version": manifest["version"],
            "minimum_supported_version": manifest["version"],
            "protocol_version": manifest.get("protocol_version", 1),
            "update": {
                "available": False,
                "required": False,
                "policy": manifest.get("update_policy", "notify"),
                "managed_by_platform": platform in {"workbuddy", "skillhub", "clawhub"},
                "url": None,
                "sha256": None,
            },
            "warning": str(exc),
        }
    update = remote.get("update") if isinstance(remote.get("update"), dict) else {}
    if update.get("available"):
        emit(
            "update-available",
            f"发现新版本 {remote.get('latest_version')}",
            f"Version {remote.get('latest_version')} is available",
            required=bool(update.get("required")),
            policy=update.get("policy"),
        )
    return remote


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_archive_member(info: zipfile.ZipInfo) -> bool:
    path = PurePosixPath(info.filename)
    if path.is_absolute() or ".." in path.parts:
        return False
    unix_mode = (info.external_attr >> 16) & 0o170000
    return unix_mode != 0o120000


def stage_update(remote: dict[str, Any]) -> bool:
    update = remote.get("update") if isinstance(remote.get("update"), dict) else {}
    url = update.get("url")
    expected_sha = str(update.get("sha256") or "").lower()
    version = str(remote.get("latest_version") or "")
    if not url or len(expected_sha) != 64 or not version:
        emit(
            "update-unavailable",
            "新版本尚未提供可验证的安装包，请通过原平台更新",
            "No verified update archive is available; update through the source platform",
        )
        return False
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    archive = CACHE_DIR / f"sankey-buddy-{version}.zip"
    emit("update-download", "正在下载可校验的版本包", "Downloading verified update archive")
    request = urllib.request.Request(str(url), headers={"User-Agent": "SankeyBuddy-Updater"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)
    except (OSError, urllib.error.URLError) as exc:
        raise SankeyBuddyError(f"UPDATE_DOWNLOAD_FAILED: {exc}") from exc
    actual_sha = sha256_file(archive)
    if actual_sha != expected_sha:
        archive.unlink(missing_ok=True)
        raise SankeyBuddyError("UPDATE_HASH_MISMATCH: downloaded archive was rejected")
    save_json(PENDING_UPDATE, {"version": version, "archive": str(archive), "sha256": actual_sha})
    emit(
        "update-staged",
        "升级包已验证，将在下次调用前生效",
        "The verified update will take effect before the next invocation",
        version=version,
    )
    return True


def apply_pending_update() -> bool:
    if not PENDING_UPDATE.exists() or os.environ.get("SANKEY_BUDDY_UPDATED") == "1":
        return False
    pending = load_json(PENDING_UPDATE)
    archive = Path(str(pending.get("archive", "")))
    expected_sha = str(pending.get("sha256", ""))
    if not archive.is_file() or sha256_file(archive) != expected_sha:
        PENDING_UPDATE.unlink(missing_ok=True)
        raise SankeyBuddyError("PENDING_UPDATE_INVALID: archive missing or changed")
    emit("update-apply", "正在应用已验证的升级", "Applying verified SankeyBuddy update")
    installed_manifest = load_json(LOCAL_MANIFEST)
    installed_channel = str(installed_manifest.get("channel") or "direct")
    parent = SKILL_DIR.parent
    with tempfile.TemporaryDirectory(prefix="sankey-buddy-update-", dir=parent) as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(archive) as bundle:
            if not all(safe_archive_member(info) for info in bundle.infolist()):
                raise SankeyBuddyError("UNSAFE_UPDATE_ARCHIVE: path or symlink rejected")
            bundle.extractall(extract_root)
        candidates = [path.parent for path in extract_root.rglob("SKILL.md")]
        candidates = [path for path in candidates if (path / "manifest.json").is_file()]
        if len(candidates) != 1:
            raise SankeyBuddyError("INVALID_UPDATE_ARCHIVE: expected one skill directory")
        candidate = candidates[0]
        new_manifest = load_json(candidate / "manifest.json")
        if new_manifest.get("name") != "sankey-buddy-skill":
            raise SankeyBuddyError("INVALID_UPDATE_ARCHIVE: wrong skill name")
        backup = parent / f".sankey-buddy-backup-{int(time.time())}"
        os.replace(SKILL_DIR, backup)
        try:
            shutil.copytree(candidate, SKILL_DIR)
            applied_manifest_path = SKILL_DIR / "manifest.json"
            applied_manifest = load_json(applied_manifest_path)
            applied_manifest["channel"] = installed_channel
            save_json(applied_manifest_path, applied_manifest)
        except Exception:
            if SKILL_DIR.exists():
                shutil.rmtree(SKILL_DIR)
            os.replace(backup, SKILL_DIR)
            raise
    PENDING_UPDATE.unlink(missing_ok=True)
    archive.unlink(missing_ok=True)
    emit("update-applied", "升级完成，正在重新载入", "Update applied; reloading client")
    os.environ["SANKEY_BUDDY_UPDATED"] = "1"
    os.execv(sys.executable, [sys.executable, str(SKILL_DIR / "scripts" / "sankey_buddy.py"), *sys.argv[1:]])
    return True


def multipart_body(fields: dict[str, str], file_path: Path) -> tuple[bytes, str]:
    boundary = f"----SankeyBuddy{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            value.encode("utf-8"),
            b"\r\n",
        ])
    safe_name = file_path.name.replace('"', "_")
    chunks.extend([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="report"; filename="{safe_name}"\r\n'.encode("utf-8"),
        b"Content-Type: application/octet-stream\r\n\r\n",
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    return b"".join(chunks), boundary


def upload_report(
    api_base: str,
    manifest: dict[str, Any],
    platform: str,
    file_path: Path,
    language: str,
    unit: str,
    timeout: int,
) -> dict[str, Any]:
    emit("upload", "正在上传财报", "Uploading the financial report", filename=file_path.name)
    emit(
        "extract-validate",
        "服务将提取财务数据并执行资金守恒与图表质量校验，通常需要 1–3 分钟",
        "Extracting financial data and validating conservation and chart quality; this usually takes 1–3 minutes",
    )
    body, boundary = multipart_body({"language": language, "unit": unit}, file_path)
    headers = client_headers(manifest, platform)
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/api/generate/upload",
        data=body,
        headers=headers,
        method="POST",
    )
    return request_json(request, timeout)


def chrome_path(explicit: str | None) -> str | None:
    local_app_data = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("PROGRAMFILES")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
    candidates = [
        explicit,
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        str(Path(local_app_data) / "Google/Chrome/Application/chrome.exe")
        if local_app_data else None,
        str(Path(program_files) / "Google/Chrome/Application/chrome.exe")
        if program_files else None,
        str(Path(program_files_x86) / "Google/Chrome/Application/chrome.exe")
        if program_files_x86 else None,
        str(Path(program_files) / "Microsoft/Edge/Application/msedge.exe")
        if program_files else None,
    ]
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "microsoft-edge"):
        candidates.append(shutil.which(name))
    return next((str(value) for value in candidates if value and Path(value).is_file()), None)


def svg_dimensions(svg: str) -> tuple[int, int]:
    match = re.search(r'viewBox=["\']\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)', svg)
    if not match:
        return (1600, 1000)
    return (
        max(1, min(8192, round(float(match.group(1))))),
        max(1, min(8192, round(float(match.group(2))))),
    )


def render_png(svg: str, png_path: Path, chrome: str | None, timeout: int) -> str:
    executable = chrome_path(chrome)
    if not executable:
        raise SankeyBuddyError(
            "PNG_RENDERER_NOT_FOUND: install Chrome/Chromium or pass --chrome PATH"
        )
    width, height = svg_dimensions(svg)
    html = (
        "<!doctype html><meta charset='utf-8'><style>"
        f"html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:#fff}}"
        f"svg{{display:block;width:{width}px;height:{height}px}}</style>" + svg
    )
    with tempfile.TemporaryDirectory(prefix="sankey-buddy-png-") as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "chart.html"
        profile_path = tmp_path / "chrome-profile"
        html_path.write_text(html, encoding="utf-8")
        command = [
            executable,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            f"--user-data-dir={profile_path}",
            f"--window-size={width},{height}",
            "--force-device-scale-factor=1",
            "--virtual-time-budget=3000",
            f"--screenshot={png_path}",
            html_path.resolve().as_uri(),
        ]
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        deadline = time.monotonic() + timeout
        stable_size: int | None = None
        stable_since = 0.0
        try:
            while time.monotonic() < deadline:
                if png_path.exists() and png_path.stat().st_size > 0:
                    size = png_path.stat().st_size
                    if size == stable_size:
                        if time.monotonic() - stable_since >= 0.5:
                            break
                    else:
                        stable_size = size
                        stable_since = time.monotonic()
                if process.poll() is not None and not png_path.exists():
                    raise SankeyBuddyError(
                        f"PNG_RENDER_FAILED: Chrome exited with {process.returncode}"
                    )
                time.sleep(0.15)
            else:
                raise SankeyBuddyError(
                    f"PNG_RENDER_FAILED: screenshot was not stable within {timeout}s"
                )
        finally:
            if process.poll() is None:
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
    if png_path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise SankeyBuddyError("PNG_RENDER_FAILED: invalid PNG output")
    return "local"


def render_png_server(
    api_base: str,
    manifest: dict[str, Any],
    platform: str,
    document: Any,
    png_path: Path,
    timeout: int,
) -> str:
    if not isinstance(document, dict):
        raise SankeyBuddyError("INVALID_SERVER_RESPONSE: chart document is missing")
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/api/render/png",
        data=json.dumps(document, ensure_ascii=False).encode("utf-8"),
        headers={
            **client_headers(manifest, platform),
            "Accept": "image/png",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            png = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SankeyBuddyError(f"SERVER_PNG_FAILED: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SankeyBuddyError(f"SERVER_PNG_FAILED: {exc.reason}") from exc
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise SankeyBuddyError("SERVER_PNG_FAILED: invalid PNG output")
    temporary = png_path.with_suffix(png_path.suffix + ".tmp")
    temporary.write_bytes(png)
    os.replace(temporary, png_path)
    return "server"


def safe_stem(path: Path) -> str:
    value = "-".join(path.stem.strip().split())
    return "".join(character for character in value if character.isalnum() or character in "-_ ") or "sankey-buddy"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload a financial report and export verified SVG and PNG Sankey charts."
    )
    parser.add_argument("file", nargs="?", help="financial report file")
    parser.add_argument("--out-dir", default=".", help="output directory")
    parser.add_argument("--name", help="output basename")
    parser.add_argument("--language", choices=["auto", "zh", "en"], default="auto")
    parser.add_argument("--unit", choices=["auto", "B", "亿"], default="auto")
    parser.add_argument("--platform", help="runtime agent platform override")
    parser.add_argument("--api-base", help="SankeyBuddy service base URL")
    parser.add_argument("--chrome", help="Chrome/Chromium executable")
    parser.add_argument("--api-timeout", type=int, default=600)
    parser.add_argument("--png-timeout", type=int, default=45)
    return parser.parse_args()


def main() -> None:
    try:
        apply_pending_update()
    except (OSError, SankeyBuddyError) as exc:
        emit(
            "update-skipped",
            "当前环境无法应用升级，将继续使用现有版本",
            "The update could not be applied in this environment; continuing with the installed release",
            warning=str(exc),
        )
    args = parse_args()
    manifest = load_json(LOCAL_MANIFEST)
    platform = detect_platform(manifest, args.platform)
    api_base = (
        args.api_base
        or os.environ.get("SANKEY_BUDDY_API_BASE")
        or str(manifest.get("api_base"))
    ).rstrip("/")
    remote = check_version(api_base, manifest, platform, min(args.api_timeout, 30))
    update = remote.get("update") if isinstance(remote.get("update"), dict) else {}
    policy = str(update.get("policy") or manifest.get("update_policy") or "notify")
    if update.get("available") and policy in {"next-run", "auto"}:
        try:
            staged = stage_update(remote)
            if staged and policy == "auto":
                apply_pending_update()
        except (OSError, SankeyBuddyError) as exc:
            emit(
                "update-skipped",
                "当前环境无法准备升级，将继续处理当前任务",
                "The update could not be prepared in this environment; continuing with the current task",
                warning=str(exc),
            )
    if not args.file:
        raise SankeyBuddyError("MISSING_FILE: pass a financial report file")
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        raise SankeyBuddyError(f"FILE_NOT_FOUND: {source}")
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise SankeyBuddyError(f"UNSUPPORTED_FILE_TYPE: {source.suffix or '(none)'}")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise SankeyBuddyError("FILE_TOO_LARGE: maximum size is 20 MB")
    result = upload_report(
        api_base, manifest, platform, source, args.language, args.unit, args.api_timeout
    )
    svg = result.get("svg")
    if not isinstance(svg, str) or "<svg" not in svg:
        raise SankeyBuddyError("INVALID_SERVER_RESPONSE: SVG is missing")
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.name or safe_stem(source)
    svg_path = out_dir / f"{stem}.svg"
    png_path = out_dir / f"{stem}.png"
    svg_path.write_text(svg, encoding="utf-8")
    emit("svg-saved", "SVG 已生成", "SVG created", path=str(svg_path))
    executable = chrome_path(args.chrome)
    if executable:
        emit("png-local", "正在本地生成 PNG", "Rendering PNG locally")
        try:
            renderer = render_png(svg, png_path, executable, args.png_timeout)
        except SankeyBuddyError as exc:
            emit(
                "png-server-fallback",
                "本地生成失败，正在切换服务端生成 PNG",
                "Local rendering failed; switching to hosted PNG generation",
                warning=str(exc),
            )
            renderer = render_png_server(
                api_base,
                manifest,
                platform,
                result.get("document"),
                png_path,
                args.api_timeout,
            )
    else:
        emit(
            "png-server-fallback",
            "本地未检测到 PNG 生成环境，正在使用服务端生成",
            "No local PNG renderer was detected; using hosted generation",
        )
        renderer = render_png_server(
            api_base,
            manifest,
            platform,
            result.get("document"),
            png_path,
            args.api_timeout,
        )
    emit("complete", "SVG 和 PNG 已生成", "SVG and PNG are ready")
    output = {
        "ok": True,
        "skill": "SankeyBuddy",
        "platform": platform,
        "channel": str(manifest.get("channel") or "direct"),
        "outputs": {"svg": str(svg_path), "png": str(png_path)},
        "png_renderer": renderer,
        "stats": result.get("stats", {}),
        "warnings": result.get("warnings", []),
        "request_id": (result.get("meta") or {}).get("request_id"),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SankeyBuddyError as exc:
        emit("error", f"SankeyBuddy 失败：{exc}", f"SankeyBuddy failed: {exc}")
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
