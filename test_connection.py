import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ["BOT_TOKEN"]

url = f"https://api.telegram.org/bot{token}/getMe"

print("Testing Telegram Bot API...", flush=True)

try:
    response = httpx.get(url, timeout=30)

    print("HTTP status:", response.status_code, flush=True)
    print("Response:", response.text, flush=True)

except Exception as e:
    print("Error:", type(e).__name__, str(e), flush=True)