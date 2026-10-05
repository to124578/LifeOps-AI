import os, httpx
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GEMINI_API_KEY", "").strip()
print("Key mili:", bool(key), "| shuru ke 4 letters:", key[:4])

r = httpx.get("https://generativelanguage.googleapis.com/v1beta/models",
              headers={"x-goog-api-key": key}, timeout=30)
print("Model list status:", r.status_code)
if r.status_code != 200:
    print(r.text[:300]); raise SystemExit

names = [m["name"].replace("models/", "") for m in r.json()["models"]
         if "generateContent" in m.get("supportedGenerationMethods", [])
         and "flash" in m["name"]]
for n in names:
    t = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{n}:generateContent",
                   headers={"x-goog-api-key": key},
                   json={"contents": [{"parts": [{"text": "say hi"}]}]}, timeout=30)
    print(n, "->", t.status_code)
    if t.status_code == 200:
        print("\nYE NAAM USE KARO:  GEMINI_MODEL=" + n)
        break