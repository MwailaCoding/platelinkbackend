with open("platelink-frontend/apps/admin/src/components/Staff/StaffForm.tsx", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ["role", "table", "shift", "kitchen"]):
        print(f"L{idx+1}: {line.strip()}")
