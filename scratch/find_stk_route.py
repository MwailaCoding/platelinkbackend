import os

backend_dir = r"c:\Users\HP\OneDrive\Desktop\platelink\app"
for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "/mpesa/stk-push" in content:
                        print(f"Found in {path}")
                        # Print lines containing the string
                        for i, line in enumerate(content.split("\n")):
                            if "/mpesa/stk-push" in line:
                                print(f"  Line {i+1}: {line}")
            except Exception as e:
                pass
