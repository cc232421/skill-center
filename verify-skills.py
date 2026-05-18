#!/usr/bin/env python3
"""
verify-skills.py — Validate all skill.json files in the skills/ directory.

Checks:
  1. Valid JSON
  2. Required fields: name, description, version, keywords
  3. Recommended fields: triggers, compatibility, license, entry
  4. name matches directory slug

Exit codes:
  0 = all pass
  1 = one or more failures
"""

import json
import glob
import sys
import os

REQUIRED = ["name", "description", "version", "keywords"]
RECOMMENDED = ["triggers", "compatibility", "license", "entry"]


def verify_skill_json(path: str) -> list[str]:
    errors = []
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    # Required fields
    for field in REQUIRED:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Recommended fields
    for field in RECOMMENDED:
        if field not in data:
            errors.append(f"Missing recommended field: {field}")

    # Name matches directory slug
    directory = os.path.basename(os.path.dirname(path))
    if data.get("name") and data["name"] != directory:
        errors.append(
            f"Name mismatch: skill.json name='{data['name']}' but directory='{directory}'"
        )

    return errors


def main():
    skill_files = sorted(glob.glob("skills/*/skill.json"))
    if not skill_files:
        print("No skill.json files found in skills/")
        sys.exit(1)

    total_errors = 0
    total_warnings = 0

    for path in skill_files:
        errors = verify_skill_json(path)
        skill_name = os.path.basename(os.path.dirname(path))
        if errors:
            print(f"\n❌ {skill_name}/skill.json")
            for e in errors:
                print(f"   {e}")
                if "required" in e.lower():
                    total_errors += 1
                else:
                    total_warnings += 1
        else:
            print(f"✅ {skill_name}/skill.json")

    print(f"\n---")
    print(f"Skills checked: {len(skill_files)}")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
