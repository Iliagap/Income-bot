
import socket
import httpx

host = "api.telegram.org"

print("DNS results:", flush=True)

try:
    for result in socket.getaddrinfo(
        host, 443, type=socket.SOCK_STREAM
    ):
        print(result[4], flush=True)
except Exception as e:
    print("DNS error:", repr(e), flush=True)

print("\nTesting HTTPS...", flush=True)

try:
    with httpx.Client(timeout=15) as client:
        response = client.get(
            "https://api.telegram.org"
        )
        print(
            "HTTP status:",
            response.status_code,
            flush=True
        )
except Exception as e:
    print(
        "Connection error:",
        type(e).__name__,
        repr(e),
        flush=True
    )
