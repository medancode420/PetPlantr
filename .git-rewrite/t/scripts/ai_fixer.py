#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import List, Dict, Any

parser = argparse.ArgumentParser(description="AI Fixer for Lint/Type Issues")
parser.add_argument('--issues', required=True, help="Path to issues.json from config-tuner")
parser.add_argument('--output', required=True, help="Path to output suggestions.md")
parser.add_argument('--top-n', type=int, default=5, help="Limit to top N issues")
parser.add_argument('--api-key', default=os.getenv('XAI_API_KEY'), help="xAI API key (from env if unset)")
parser.add_argument('--model', default='grok-4-0709', help="Grok model (e.g., grok-4-0709)")
args = parser.parse_args()


def get_code_snippet(file_path: str, line: int, ctx: int = 5) -> str:
    if not os.path.exists(file_path):
        return "Code file not found."
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        start = max(0, line - ctx - 1)
        end = min(len(lines), line + ctx)
        body = ''.join(lines[start:end])
        return f"Snippet (lines {start+1}-{end}):\n{body}"
    except Exception:
        return "Failed to read code snippet."


def main() -> None:
    # Load plan (issues) safely
    try:
        with open(args.issues, 'r', encoding='utf-8') as f:
            plan = json.load(f)
    except FileNotFoundError:
        # If issues file missing, provide a helpful placeholder and exit cleanly
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('# AI Suggested Fixes\n\n')
            f.write(f"Issues file not found: {args.issues}.\n")
            f.write('No API call attempted. Ensure the config-tuner plan exists and re-run.\n')
        print(f"Issues file not found: {args.issues}. Placeholder written.")
        return
    except Exception as e:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('# AI Suggested Fixes\n\n')
            f.write(f"Failed to load issues file: {e}\n")
        print(f"Failed to load issues file: {e}. Placeholder written.")
        return

    # Prefer detailed issues with line numbers if present
    all_issues: List[Dict[str, Any]] = []
    if isinstance(plan.get('issues'), list) and plan['issues']:
        for it in plan['issues']:
            try:
                all_issues.append({
                    'path': it.get('path'),
                    'line': int(it.get('line') or 1),
                    'tool': it.get('tool'),
                    'message-id': it.get('message-id'),
                    'message': it.get('message') or '',
                })
            except Exception:
                continue
    else:
        # Fallback: flatten overrides without line numbers
        merged: Dict[str, List[str]] = {}
        merged.update(plan.get('pylint_overrides', {}))
        for k, v in plan.get('mypy_overrides', {}).items():
            merged.setdefault(k, [])
            merged[k].extend(v)
        for file_path, codes in merged.items():
            for code in codes:
                all_issues.append({
                    'path': file_path,
                    'line': 1,
                    'message-id': code,
                    'message': f'Issue code: {code}',
                })

    # Deterministic sort: by file then line number, trim to top-n
    all_issues = sorted(all_issues, key=lambda i: (i.get('path',''), int(i.get('line', 1))))[: args.top_n]

    suggestions: List[str] = []

    # Decide whether to call the API
    use_api = bool(args.api_key)
    if use_api:
        try:
            import requests  # type: ignore
        except Exception:
            print("requests package missing; falling back to placeholder suggestions.")
            use_api = False
    for issue in all_issues:
        snippet = get_code_snippet(issue['path'], issue['line'])
        prompt = (
            "You're a senior Python engineer. Provide a minimal, safe fix.\n"
            f"Tool: {issue.get('tool','unknown')}  Code: {issue['message-id']}\n"
            f"File: {issue['path']}  Line: {issue['line']}\n"
            f"Message: {issue.get('message','')}\n\n"
            "Code to inspect:\n" + snippet + "\n\n"
            "Respond with:\n"
            "1) One-sentence rationale\n"
            "2) Unified diff (fenced as ```diff) applying the minimal change\n"
        )

        if use_api:
            try:
                resp = requests.post(  # type: ignore[name-defined]
                    'https://api.x.ai/v1/chat/completions',
                    headers={'Authorization': f'Bearer {args.api_key}', 'Content-Type': 'application/json'},
                    json={
                        'model': args.model,
                        'messages': [{'role': 'user', 'content': prompt}],
                        'max_tokens': 800,
                        'temperature': 0.3,
                    },
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    if not content:
                        content = "No suggestion returned."
                else:
                    content = f"API call failed ({resp.status_code}): {resp.text[:200]}"
            except Exception as e:
                content = (
                    f"API call error: {e}\n\n"
                    f"Fallback: No API suggestion available. Review {issue['message-id']} at line {issue['line']} in {issue['path']}.\n"
                )
        else:
            # Placeholder rich suggestion including issue details
            content = (
                f"No API key or requests unavailable.\n\n"
                f"Issue: {issue.get('tool','unknown')} {issue['message-id']}\n"
                f"File: {issue['path']}  Line: {issue['line']}\n"
                f"Message: {issue.get('message','')}\n\n"
                "Manual guidance: Consider fixing the reported line, add typing if missing, or refactor the snippet. "
                "Run config-tuner in safe mode to adjust per-file config if needed."
            )

        suggestions.append(
            f"### Suggested Fix for {issue['path']} (Issue: {issue['message-id']})\n\n{content}\n\n---"
        )

    with open(args.output, 'w', encoding='utf-8') as f:
        header = '# AI Suggested Fixes\n\n'
        tail = '\n\nThese are AI-generated suggestions—review before applying!\n'
        if not suggestions:
            f.write(header + 'No issues to suggest fixes for.\n' + tail)
        else:
            f.write(header + '\n\n'.join(suggestions) + tail)

    print(f"Suggestions written to {args.output}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Global fallback: non-blocking placeholder output
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f'# AI Suggested Fixes\n\nError generating suggestions: {e}\n')
            print(f"Non-fatal error: {e}. Placeholder suggestions.md created.")
        except Exception as inner:
            print(f"Non-fatal error and failed to write placeholder: {inner}")
        sys.exit(0)
