import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
stopping = False


def stop_children(*processes):
    for process in processes:
        if process and process.poll() is None:
            process.terminate()
    for process in processes:
        if process and process.poll() is None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def request_shutdown(_signum, _frame):
    global stopping
    stopping = True


def main():
    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    port = os.getenv('PORT', '8000')
    web = subprocess.Popen(
        [
            sys.executable, '-m', 'gunicorn', 'config.wsgi:application',
            '--chdir', str(ROOT / 'backend'),
            '--bind', f'0.0.0.0:{port}',
        ],
        cwd=ROOT,
    )
    bot = None
    restart_at = 0.0
    if not os.getenv('BOT_TOKEN'):
        print('BOT_TOKEN is missing; Telegram bot cannot start.', flush=True)
    else:
        bot = subprocess.Popen([sys.executable, str(ROOT / 'bot' / 'main.py')], cwd=ROOT)

    while not stopping:
        if web.poll() is not None:
            print(f'Web service exited with code {web.returncode}.', flush=True)
            break
        if bot is not None and bot.poll() is not None:
            print(f'Telegram bot exited with code {bot.returncode}; retrying in 5 seconds.', flush=True)
            bot = None
            restart_at = time.monotonic() + 5
        if bot is None and time.monotonic() >= restart_at and os.getenv('BOT_TOKEN'):
            bot = subprocess.Popen([sys.executable, str(ROOT / 'bot' / 'main.py')], cwd=ROOT)
        time.sleep(1)

    stop_children(bot, web)
    return 0 if stopping else web.returncode or 0


if __name__ == '__main__':
    raise SystemExit(main())
