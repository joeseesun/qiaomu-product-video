#!/usr/bin/env python3
"""Record a real terminal session (asciicast v2) for CLI / TUI products. Stdlib only (POSIX pty).

    python3 record_terminal.py --out assets/demo.cast [--type "mytool sync --all"] [--cols 96 --rows 26] -- mytool sync --all

--type prints a prompt and "types" the command (with human-ish rhythm) before running it, so the
film shows the command being entered; the output that follows is the command's real output with
its real timing. Replay it in a shot with src/kit/terminal.js (parseCast / drawTerminal), optionally
compressing idle gaps. Never record secrets: use a scratch environment and review the .cast file.

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import json
import os
import pty
import random
import select
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--type", help="command text to show as typed before running")
    ap.add_argument("--prompt", default="\x1b[32m❯\x1b[0m ")
    ap.add_argument("--cols", type=int, default=96)
    ap.add_argument("--rows", type=int, default=26)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        ap.error("give the command after --")

    events: list[list] = []
    clock = 0.0
    rng = random.Random(7)
    if args.type is not None:
        events.append([0.0, "o", args.prompt])
        clock = 0.35
        for ch in args.type:
            clock += rng.uniform(0.045, 0.11)
            events.append([round(clock, 4), "o", ch])
        clock += 0.3
        events.append([round(clock, 4), "o", "\r\n"])

    env = dict(os.environ, TERM="xterm-256color", COLUMNS=str(args.cols), LINES=str(args.rows))
    pid, fd = pty.fork()
    if pid == 0:
        os.execvpe(cmd[0], cmd, env)
    start = time.monotonic()
    buf = b""
    while True:
        if time.monotonic() - start > args.timeout:
            os.kill(pid, 9)
            break
        r, _, _ = select.select([fd], [], [], 0.05)
        if fd in r:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            try:
                text = buf.decode("utf-8")
                buf = b""
            except UnicodeDecodeError:
                continue
            events.append([round(clock + time.monotonic() - start, 4), "o", text])
        else:
            done, _ = os.waitpid(pid, os.WNOHANG)
            if done:
                break
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
    header = {"version": 2, "width": args.cols, "height": args.rows, "timestamp": int(time.time()),
              "env": {"TERM": "xterm-256color"}, "title": " ".join(cmd)}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(header) + "\n" + "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n", encoding="utf-8")
    print(json.dumps({"cast": str(out), "events": len(events), "seconds": events[-1][0] if events else 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
