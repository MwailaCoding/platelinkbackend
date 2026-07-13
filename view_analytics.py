with open("platelink-frontend/apps/admin/src/app/(dashboard)/analytics/page.tsx", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ["popular", "heatmap", "export", "performance", "waiter", "sales", "pdf"]):
        print(f"L{idx+1}: {line.strip()}")
