import os
import re

search_dir = r"c:\Users\HP\OneDrive\Desktop\platelink\platelink-frontend"
matches = []

for root, dirs, files in os.walk(search_dir):
    if "node_modules" in dirs:
        dirs.remove("node_modules")
    if ".next" in dirs:
        dirs.remove(".next")
    for file in files:
        if file.endswith((".ts", ".tsx", ".js", ".jsx")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Find api.put(...)
                    for m in re.finditer(r'api\.put\([^)]*\)', content):
                        matches.append((path, m.group(0)))
            except Exception:
                pass

print("ALL API.PUT CALLS:")
print("-" * 100)
for path, call in matches:
    rel_path = os.path.relpath(path, search_dir)
    print(f"{rel_path} | {call}")
