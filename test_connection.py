import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ["BOT_TOKEN"]

url = f"https://api.telegram.org/bot{token}/getMe"

print("Testing Telegram Bot API...", flush=True)

response = httpx.get(
    f"https://api.telegram.org/bot{token}/getMe",
    timeout=30
)

print("HTTP status:", response.status_code)
print("API success:", response.json().get("ok"))