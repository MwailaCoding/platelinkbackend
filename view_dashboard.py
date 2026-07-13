with open("platelink-frontend/apps/admin/src/app/(dashboard)/dashboard/page.tsx", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ["sales", "order", "table", "stock", "chart"]):
        print(f"L{idx+1}: {line.strip()}")
