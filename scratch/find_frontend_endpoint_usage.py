import os

frontend_dir = r"c:\Users\HP\OneDrive\Desktop\platelink\platelink-frontend\apps\customer\src"
for root, dirs, files in os.walk(frontend_dir):
    dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".turbo")]
    for file in files:
        if file.endswith((".ts", ".tsx")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "STK_PUSH" in content:
                        print(f"Found in {path}")
                        for i, line in enumerate(content.split("\n")):
                            if "STK_PUSH" in line:
                                print(f"  Line {i+1}: {line}")
            except Exception as e:
                pass
