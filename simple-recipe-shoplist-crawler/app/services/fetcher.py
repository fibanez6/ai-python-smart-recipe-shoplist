import httpx


async def fetch(url: str) -> str:
    print(f"[fetcher] fetching: {url}")
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        text = r.text
        print(f"[fetcher] fetched {len(text)} chars, status={r.status_code}")
        return text
