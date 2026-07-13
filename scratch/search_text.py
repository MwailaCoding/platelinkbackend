import os

search_dir = r"c:\Users\HP\OneDrive\Desktop\platelink\platelink-frontend"
query = "Java House"

matches = []
for root, dirs, files in os.walk(search_dir):
    if "node_modules" in dirs:
        dirs.remove("node_modules")
    if ".next" in dirs:
        dirs.remove(".next")
    if ".git" in dirs:
        dirs.remove(".git")
    for file in files:
        if file.endswith((".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".md")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if query in content:
                        matches.append(path)
            except Exception:
                pass

print(f"Found {len(matches)} files containing '{query}':")
for m in matches:
    print(m)
