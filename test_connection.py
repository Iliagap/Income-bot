import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ["BOT_TOKEN"]

try:
    response = httpx.get(
        f"https://api.telegram.org/bot{token}/getMe",
        timeout=30
    )

    print("HTTP status:", response.status_code, flush=True)

    data = response.json()

    print("Description:", data.get("description"), flush=True)
    print(
        "Retry after:",
        data.get("parameters", {}).get("retry_after"),
        flush=True
    )

except httpx.RequestError as error:
    print("Network error:", repr(error), flush=True)
except ValueError:
    print("Unexpected non-JSON response", flush=True)