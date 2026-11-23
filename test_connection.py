
import os
import socket
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ["BOT_TOKEN"]
host = "api.telegram.org"

print("=== DNS ===", flush=True)

for family, name in [
    (socket.AF_INET, "IPv4"),
    (socket.AF_INET6, "IPv6"),
]:
    try:
        addresses = socket.getaddrinfo(
            host, 443, family=family,
            type=socket.SOCK_STREAM
        )
        print(name, [a[4][0] for a in addresses], flush=True)
    except Exception as e:
        print(name, repr(e), flush=True)

print("\n=== HTTPS test ===", flush=True)

urls = {
    "Homepage": "https://api.telegram.org/",
    "Invalid token": "https://api.telegram.org/bot000000:INVALID/getMe",
    "Real bot": f"https://api.telegram.org/bot{token}/getMe",
}

with httpx.Client(timeout=15, follow_redirects=False) as client:
    for name, url in urls.items():
        try:
            response = client.get(url)

            print(
                f"{name}: HTTP {response.status_code}",
                flush=True
            )

            if name == "Real bot":
                data = response.json()
                print("Description:", data.get("description"), flush=True)
                print(
                    "Retry after:",
                    data.get("parameters", {}).get("retry_after"),
                    flush=True
                )

        except Exception as e:
            print(
                f"{name}: {type(e).__name__}: {e}",
                flush=True
            )
