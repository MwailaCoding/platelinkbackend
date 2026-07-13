with open("platelink-frontend/apps/admin/src/app/(dashboard)/settings/page.tsx", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if "kitchen" in line.lower() or "prep" in line.lower() or "sound" in line.lower():
        print(f"L{idx+1}: {line.strip()}")
