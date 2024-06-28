import httpx

http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0),
    follow_redirects=True
)
