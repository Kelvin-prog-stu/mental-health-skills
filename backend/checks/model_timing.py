"""Times one short request to each model in the fallback chain and prints how it finished.

Evidence for the Oct 27 failure (a cut-off reply saved as complete). LIVE: makes one call per
model. The key is read from backend/.env and never printed.

Run from backend/:  .venv\\Scripts\\python.exe checks\\model_timing.py
"""

import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm_client  # noqa: E402
from config import gemini_api_key  # noqa: E402

BODY = {
    "systemInstruction": {"parts": [{"text": "Reply in two sentences."}]},
    "contents": [{"role": "user", "parts": [{"text": "Say something about breathing slowly."}]}],
    "generationConfig": {"temperature": 0, "maxOutputTokens": llm_client.MAX_OUTPUT_TOKENS},
}

key = gemini_api_key()
if key is None:
    sys.exit("No GEMINI_API_KEY in backend/.env; nothing to time.")
print(f"app limit per model: {llm_client.REQUEST_TIMEOUT_SECONDS} s")
for model in llm_client.model_chain():
    started = time.time()
    try:
        r = httpx.post(llm_client.GEMINI_URL.format(model=model),
                       headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=BODY, timeout=40)
        cand = (r.json().get("candidates") or [{}])[0]
        usage = r.json().get("usageMetadata", {})
        print(f"{model:24} HTTP {r.status_code}  {time.time() - started:5.1f} s  finish={cand.get('finishReason')}  "
              f"thinking tokens={usage.get('thoughtsTokenCount', 0)}")
    except httpx.HTTPError as exc:
        print(f"{model:24} {type(exc).__name__} after {time.time() - started:.1f} s")
