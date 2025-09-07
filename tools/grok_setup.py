#!/usr/bin/env python3
"""
Grok-powered interactive bootstrap (placeholder).
Future: integrate LangChain to ask a few questions & scaffold env.
"""
import os
import sys

DEFAULT_DIR = os.environ.get("PROJECT_DIR", os.path.expanduser("~/PetPlantr"))


def main():
    target = DEFAULT_DIR
    if len(sys.argv) > 1:
        target = sys.argv[1]
    os.makedirs(target, exist_ok=True)
    print(f"[grok-setup] Initialized directory: {target}")
    print("Next: integrate LangChain agent here to gather config and write .env")


if __name__ == "__main__":
    main()
