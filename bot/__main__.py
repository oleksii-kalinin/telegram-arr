import os
from pathlib import Path

from bot.main import main

PID_FILE = Path("/tmp/bot.pid")
PID_FILE.write_text(str(os.getpid()))

main()
