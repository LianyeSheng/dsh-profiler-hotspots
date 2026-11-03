#!/usr/bin/env python3
"""Run one command as a GitHub App, scoped to LianyeSheng/dsh-profiler."""
import argparse
import base64
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = "LianyeSheng/dsh-profiler"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def dotenv_config(root):
    """Read only App configuration; never evaluate shell code or expand values."""
    path = root / ".env"
    if not path.exists():
        return {}
    result = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, value = line.partition("=")
        name = name.strip()
        if name not in ("AGENT_GH_APP_ID", "AGENT_GH_APP_KEY"):
            continue
        try:
            parts = shlex.split(value, comments=True, posix=True)
        except ValueError:
            raise ValueError(f"Invalid .env syntax at line {number}") from None
        if not separator or len(parts) > 1:
            raise ValueError(f"Invalid .env syntax at line {number}; quote values containing spaces")
        result[name] = parts[0] if parts else ""
    return result


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def jwt(app_id, key):
    now = int(time.time())
    header = b64(b'{"alg":"RS256","typ":"JWT"}')
    payload = b64(json.dumps({"iss": app_id, "iat": now - 60,
                              "exp": now + 540}).encode())
    unsigned = header + b"." + payload
    signed = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(key)],
        input=unsigned, capture_output=True, check=True).stdout
    return (unsigned + b"." + b64(signed)).decode()


def api(path, token, body=None):
    request = urllib.request.Request(
        "https://api.github.com" + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2026-03-10",
                 "User-Agent": "se-tools-agent-auth",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def git_env(env, name, email):
    env = env.copy()
    settings = [
        ("credential.helper", ""),
        ("credential.helper", "!gh auth git-credential"),
        (f"url.https://github.com/{REPO}.git.insteadOf",
         f"git@github.com:{REPO}.git"),
        (f"url.https://github.com/{REPO}.git.insteadOf",
         f"ssh://git@github.com/{REPO}.git"),
        ("user.name", name), ("user.email", email),
    ]
    count = int(env.get("GIT_CONFIG_COUNT", "0"))
    for key, value in settings:
        env[f"GIT_CONFIG_KEY_{count}"] = key
        env[f"GIT_CONFIG_VALUE_{count}"] = value
        count += 1
    env["GIT_CONFIG_COUNT"] = str(count)
    for role in ("AUTHOR", "COMMITTER"):
        env[f"GIT_{role}_NAME"] = name
        env[f"GIT_{role}_EMAIL"] = email
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-id")
    parser.add_argument("--key")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="-- command args; omit to check authentication")
    args = parser.parse_args()
    # Run before reading local secrets or making authentication requests.
    guard = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts/verify-no-env.py")],
        cwd=PROJECT_ROOT)
    if guard.returncode:
        return guard.returncode
    try:
        config = dotenv_config(PROJECT_ROOT)
    except ValueError as error:
        parser.error(str(error))
    if args.app_id is None:
        args.app_id = os.environ.get("AGENT_GH_APP_ID", config.get("AGENT_GH_APP_ID"))
    if args.key is None:
        args.key = os.environ.get("AGENT_GH_APP_KEY", config.get("AGENT_GH_APP_KEY"))
    if not args.app_id or not args.key:
        parser.error("set AGENT_GH_APP_ID and AGENT_GH_APP_KEY in project .env or environment, or use --app-id/--key")
    key = Path(args.key).expanduser()
    if not key.is_absolute():
        key = PROJECT_ROOT / key
    key = key.resolve(strict=True)
    if key.stat().st_mode & 0o077:
        parser.error("private key must not be accessible to group/others; chmod 600 it")
    app_jwt = jwt(args.app_id, key)
    app = api("/app", app_jwt)
    installation = api(f"/repos/{REPO}/installation", app_jwt)
    token_data = api(f"/app/installations/{installation['id']}/access_tokens",
                     app_jwt, {"repositories": [REPO.split('/')[1]]})
    token = token_data["token"]
    # The bot user ID differs from the App ID.
    try:
        login = app["slug"] + "[bot]"
        bot = api("/users/" + urllib.parse.quote(login, safe=""), token)
        email = f"{bot['id']}+{login}@users.noreply.github.com"
        command = args.command
        if command[:1] == ["--"]:
            command = command[1:]
        if not command:
            repo = api(f"/repos/{REPO}", token)
            print(json.dumps({"bot": login, "email": email,
                              "repository": repo["full_name"],
                              "installation_id": installation["id"],
                              "permissions": token_data.get("permissions"),
                              "expires_at": token_data["expires_at"]}, indent=2))
            return 0
        env = git_env(os.environ, login, email)
        env.update(GH_TOKEN=token, GITHUB_TOKEN=token,
                   GH_HOST="github.com", GH_REPO=REPO)
        # Isolate gh config, including pre-existing host credentials and aliases.
        with tempfile.TemporaryDirectory(prefix="gh-app-") as config:
            env["GH_CONFIG_DIR"] = config
            return subprocess.run(command, env=env).returncode
    finally:
        # Revoke the per-command token; failures must not mask command results.
        request = urllib.request.Request(
            "https://api.github.com/installation/token", method="DELETE",
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "User-Agent": "se-tools-agent-auth"})
        try:
            with urllib.request.urlopen(request, timeout=10):
                pass
        except (urllib.error.URLError, TimeoutError):
            print("Token revocation failed; token expires automatically.", file=sys.stderr)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as error:
        sys.exit(f"GitHub API returned HTTP {error.code}: {error.reason}")
    except (OSError, subprocess.CalledProcessError, urllib.error.URLError) as error:
        sys.exit(f"Authentication/command failed ({type(error).__name__}); check key, tools and network.")
