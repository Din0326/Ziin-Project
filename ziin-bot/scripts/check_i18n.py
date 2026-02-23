from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = ROOT / "data" / "i18n"
EN_PATH = I18N_DIR / "en.json"
ZH_PATH = I18N_DIR / "zh_tw.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    en = load_json(EN_PATH)
    zh = load_json(ZH_PATH)

    en_keys = set(en.keys())
    zh_keys = set(zh.keys())

    only_en = sorted(en_keys - zh_keys)
    only_zh = sorted(zh_keys - en_keys)

    print(f"en.json keys: {len(en_keys)}")
    print(f"zh_tw.json keys: {len(zh_keys)}")

    if only_en:
        print("\nMissing in zh_tw.json:")
        for key in only_en:
            print(f"  - {key}")

    if only_zh:
        print("\nMissing in en.json:")
        for key in only_zh:
            print(f"  - {key}")

    if only_en or only_zh:
        return 1

    print("\nOK: i18n keys are in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
