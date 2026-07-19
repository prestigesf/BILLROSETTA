"""Hackathon demo: branded banner + pytest run for screen recording."""
import subprocess
import sys
from datetime import datetime

# ANSI colors — BillRosetta palette
PURPLE = "\033[38;5;135m"
GREEN = "\033[38;5;83m"
BLACK_BG = "\033[48;5;16m"
BOLD = "\033[1m"
DIM = "\033[2m"
R = "\033[0m"

BANNER = rf"""{BLACK_BG}{PURPLE}{BOLD}
  ____  _ _ _ ____                _   _
 | __ )(_) | |  _ \ ___  ___  ___| |_| |_ __ _
 |  _ \| | | | |_) / _ \/ __|/ _ \ __| __/ _` |
 | |_) | | | |  _ < (_) \__ \  __/ |_| || (_| |
 |____/|_|_|_|_| \_\___/|___/\___|\__|\__\__,_|
{R}{BLACK_BG}{GREEN}          M O S S   +   B R I G H T   D A T A {R}
"""

INFO = f"""{BOLD}Hackathon:{R} Moss + Bright Data
{BOLD}Project:{R}   BillRosetta Moss Bridge
{BOLD}Owner:{R}     PrestigeSF · Nicholle Simon
{BOLD}Repo:{R}      https://github.com/prestigesf/BILLROSETTA
{BOLD}Date:{R}      {datetime.now().strftime('%B %d, %Y')}
{DIM}Stack: FastAPI + MCP (Moss) + Bright Data Web Unlocker + pytest{R}
"""

def line(char="═"):
    print(f"{PURPLE}{char * 62}{R}")

print(BANNER)
line()
print(INFO)
line()
print(f"{GREEN}{BOLD}▶ Running full test suite...{R}\n")

result = subprocess.run(
    [sys.executable, "-m", "pytest", "-v", "--tb=short"],
)

print()
line()
if result.returncode == 0:
    print(f"{GREEN}{BOLD}✔ ALL TESTS PASSED — BillRosetta Moss Bridge is hackathon-ready.{R}")
else:
    print(f"\033[91m{BOLD}✘ Tests failed (exit {result.returncode}){R}")
line()
sys.exit(result.returncode)
