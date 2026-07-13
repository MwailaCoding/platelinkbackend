import os
import re

search_dir = r"c:\Users\HP\OneDrive\Desktop\platelink\app"
matches = []

# Regex to find @router.get, @router.post, etc.
route_re = re.compile(r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']*)["\']')

for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        m = route_re.search(line)
                        if m:
                            matches.append((path, line_num, m.group(1), m.group(2)))
            except Exception:
                pass

print("ALL API ENDPOINTS FOUND:")
print("-" * 100)
for path, line, method, route in sorted(matches, key=lambda x: (x[0], x[3])):
    rel_path = os.path.relpath(path, search_dir)
    print(f"{rel_path}:{line} | {method.upper()} {route}")
