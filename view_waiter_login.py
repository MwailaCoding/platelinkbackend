with open("platelink-frontend/apps/waiter/src/app/login/page.tsx", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ["scan", "qr", "tag", "nfc"]):
        print(f"L{idx+1}: {line.strip()}")
