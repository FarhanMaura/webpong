import json, os

SLANG_FILES = ["slang_dict.json", "kamusnormalisasi.json", "slang_dict_baru.json"]
IGNORED_FILE = "ignored_words.json"

def load_json_file(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json_file(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def load_all_dicts():
    merged = {}
    for fpath in SLANG_FILES:
        merged.update(load_json_file(fpath))
    return merged

def auto_correct_text(text):
    all_dict = load_all_dicts()
    ignored = load_json_file(IGNORED_FILE)

    words = text.split()
    corrected_words = []
    unknown_words = []

    for w in words:
        w_clean = w.lower().strip(".,!?")
        if w_clean in ignored:
            corrected_words.append(f"<span class='baku'>{w}</span>")
        elif w_clean in all_dict:
            corrected_words.append(f"<span class='baku'>{all_dict[w_clean]}</span>")
        elif w_clean in all_dict.values():
            corrected_words.append(f"<span class='baku'>{w}</span>")
        else:
            corrected_words.append(f"<span class='tidak-baku'>{w}</span>")
            unknown_words.append(w_clean)

    highlighted = " ".join(corrected_words)
    return highlighted, list(set(unknown_words))

def save_new_word(slang, baku):
    data = load_json_file(SLANG_FILES[-1])
    data[slang.lower()] = baku.lower()
    save_json_file(SLANG_FILES[-1], data)

def mark_word_as_ignored(word):
    ignored = load_json_file(IGNORED_FILE)
    ignored[word.lower()] = True
    save_json_file(IGNORED_FILE, ignored)
