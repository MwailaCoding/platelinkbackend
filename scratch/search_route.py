import os

search_dir = r"c:\Users\HP\OneDrive\Desktop\platelink\app"
query = "/restaurants"

matches = []
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if query in content:
                        matches.append(path)
            except Exception:
                pass

print(f"Found {len(matches)} python files containing '{query}':")
for m in matches:
    print(m)
