"""Health probe — exits 0 if the bot process is running."""

import os
import sys
from pathlib import Path

PID_FILE = Path("/tmp/bot.pid")


def main() -> None:
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        sys.exit(1)


if __name__ == "__main__":
    main()
