from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .updates import repository_root


HOST_NAMES = ("claude", "codex", "gemini")
DEFAULT_HOST = "claude"
HOST_INSTALL_ROOTS = {
    "claude": (".claude", "skills"),
    "codex": (".codex", "skills"),
    "gemini": (".gemini", "commands"),
}


def infer_host(repo_root: Path, home: Path | None = None) -> str:
    resolved_repo_root = repo_root.resolve()
    resolved_home = (home or Path.home()).expanduser().resolve()

    for host, parts in HOST_INSTALL_ROOTS.items():
        install_root = resolved_home.joinpath(*parts)
        try:
            resolved_repo_root.relative_to(install_root)
        except ValueError:
            continue
        return host

    return DEFAULT_HOST


def editable_install_command(
    repo_root: Path,
    *,
    executable: str | None = None,
    in_virtualenv: bool | None = None,
) -> list[str]:
    command = [executable or sys.executable, "-m", "pip", "install"]
    if in_virtualenv is None:
        in_virtualenv = bool(os.environ.get("VIRTUAL_ENV"))
    if not in_virtualenv:
        command.append("--user")
    command.extend(["-e", str(repo_root)])
    return command


def host_install_command(host: str, *, executable: str | None = None) -> list[str]:
    if host not in HOST_NAMES:
        raise ValueError(f"Unsupported host: {host}")
    return [executable or sys.executable, "-m", "the_big_learn", host, "install", "--force"]


def _run(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m the_big_learn.bootstrap",
        description="Bootstrap the current checkout for a supported host.",
    )
    parser.add_argument(
        "host",
        nargs="?",
        choices=("auto", "all", *HOST_NAMES),
        default="auto",
        help="Host to install. Defaults to auto, which infers the host from the checkout path and falls back to Claude.",
    )
    args = parser.parse_args(argv)

    repo_root = repository_root()
    selected_hosts = list(HOST_NAMES) if args.host == "all" else [infer_host(repo_root) if args.host == "auto" else args.host]

    print(f"Bootstrapping The Big Learn from {repo_root}")
    if args.host == "auto":
        print(f"Inferred host: {selected_hosts[0]}")

    _run(editable_install_command(repo_root))

    for host in selected_hosts:
        _run(host_install_command(host))

    print("Bootstrap complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
