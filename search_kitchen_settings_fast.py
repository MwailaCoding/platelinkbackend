import os

keywords = ["kitchen", "sound", "prep", "station", "alerts"]
for root, dirs, files in os.walk("platelink-frontend/apps/admin"):
    # skip node_modules, .next, etc.
    if "node_modules" in root or ".next" in root or ".turbo" in root:
        continue
    for file in files:
        if file.endswith((".tsx", ".ts")):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
            found = [kw for kw in keywords if kw in content]
            if "kitchen" in found or "sound" in found or "station" in found:
                print(f"Found in {path}: {found}")
