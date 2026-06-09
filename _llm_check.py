import asyncio
from orchestration.config import get_settings
from orchestration.llm import build_llm_client

s = get_settings()
c = build_llm_client(s)
print("provider =", s.llm_provider)
print("model    =", s.llm_model)
print("client   =", type(c).__name__)
out = asyncio.run(
    c.complete_json(
        "Sadece gecerli JSON dondur, baska metin yazma.",
        'Asagidaki JSONu aynen dondur: {"ok": true, "kaynak": "anthropic"}',
    )
)
print("response =", out)
