import json
import os

input_folder = "webz_json"
output_folder = "data/articles"

os.makedirs(output_folder, exist_ok=True)

count = len(os.listdir(output_folder))

for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        filepath = os.path.join(input_folder, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                continue

            text = data.get("text", "")
            source = data.get("thread", {}).get("site", "UNKNOWN")
            sentiment = data.get("sentiment", "UNKNOWN")
            categories = ", ".join(data.get("categories", []))

            if not text.strip():
                continue

            with open(f"{output_folder}/article_{count}.txt", "w", encoding="utf-8") as out:
                out.write(f"SOURCE: {source}\n")
                out.write(f"SENTIMENT: {sentiment}\n")
                out.write(f"CATEGORIES: {categories}\n\n")
                out.write(text)

            count += 1

print(f"Converted {count} total articles.")