import httpx
import asyncio
from typing import Optional, Dict, Any

class MCPHTTPTool:
    def __init__(self, user_agent: str = "MCPBot/1.0"):
        self.user_agent = user_agent

    async def fetch_text(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str,str]] = None, timeout: int = 20) -> str:
        headers_local = {"User-Agent": self.user_agent}
        if headers:
            headers_local.update(headers)
        async with httpx.AsyncClient(timeout=timeout, headers=headers_local) as client:
            for attempt in range(3):
                try:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    return resp.text
                except httpx.HTTPStatusError as e:
                    status = getattr(e, 'response', None)
                    code = status.status_code if status is not None else None
                    if code in (429, 502, 503, 504):
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise
                except Exception:
                    await asyncio.sleep(2 ** attempt)
            raise Exception("Max retries exceeded for fetch_text")