import pandas as pd

def load(path):
    if path.endswith("llm-generated/phishing.csv"):
        # unquoted file: text is everything before the last comma
        lines = open(path, encoding="utf-8").read().splitlines()[1:]
        return pd.DataFrame({"text": [l.rsplit(",", 1)[0] for l in lines if l.strip()]})
    d = pd.read_csv(path)
    if "subject" in d:
        d["text"] = d["subject"].fillna("") + " " + d["body"].fillna("")
    return d

files = [
    "dataset/human-generated/phishing.csv",
    "dataset/human-generated/legit.csv",
    "dataset/llm-generated/phishing.csv",
    "dataset/llm-generated/legit.csv",
]

for f in files:
    d = load(f)
    print(f)
    print("  rows:               ", len(d))
    print("  identical rows:     ", d.duplicated().sum())
    print("  identical text:     ", d["text"].duplicated().sum())
    print("  unique text:        ", d["text"].nunique())
    print()