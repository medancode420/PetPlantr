#!/usr/bin/env python3
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import configparser
try:
    import tomli
    import tomli_w
    import yaml
except ImportError:
    print("Install missing dependencies: pip install tomli tomli-w pyyaml")
    sys.exit(1)

parser = argparse.ArgumentParser(description="Config Optimizer CLI")
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--apply', action='store_true')
parser.add_argument('-y', action='store_true', help="Skip confirmation prompt")
parser.add_argument('--git-stage', action='store_true')
parser.add_argument('--plan-file', type=str)
parser.add_argument('--max-files', type=int, default=0, help="Limit to top N files by issue count")
parser.add_argument('--json', action='store_true', help="Output in JSON format")
parser.add_argument('--timeout', type=int, default=60, help='Per-tool timeout in seconds (default 60)')
parser.add_argument('--pylint-jobs', type=int, default=1, help='Jobs for pylint (default 1)')
parser.add_argument('--safe-mode', action='store_true', help='Only suggest safe/non-critical overrides')
parser.add_argument('--allow-pylint-prefixes', nargs='+', default=['C','W'], help="Allowed pylint prefixes in safe-mode (e.g., C W)")
parser.add_argument('--allow-mypy-codes', nargs='+', default=['no-untyped-def','no-untyped-call'], help="Allowed mypy codes in safe-mode")
parser.add_argument('paths', nargs='*', default=['.'], help="Paths to scan (default: current dir)")
args = parser.parse_args()


def check_tool(tool):
    try:
        subprocess.run([tool, '--version'], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def expand_paths(paths):
    expanded_files = set()
    for path in paths:
        if os.path.isdir(path):
            expanded_files.update(glob.glob(os.path.join(path, '**/*.py'), recursive=True))
        elif os.path.isfile(path) and path.endswith('.py'):
            expanded_files.add(path)
    return sorted(expanded_files)


def run_pylint(paths):
    if not check_tool('pylint'):
        return [], "pylint not installed. Install with: pip install pylint"
    print("Running pylint on files... (press Ctrl+C to interrupt)")
    expanded_files = expand_paths(paths)
    if not expanded_files:
        return [], "No Python files found in paths"
    cmd = ['pylint', '--output-format=json', f'--jobs={args.pylint_jobs}'] + list(expanded_files)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=args.timeout)
        if result.returncode != 0 and not result.stdout.strip():
            return [], "pylint ran but found no issues or errored"
        try:
            return json.loads(result.stdout), None
        except json.JSONDecodeError:
            return [], "pylint output not valid JSON"
    except subprocess.TimeoutExpired:
        return [], f"pylint timed out after {args.timeout} seconds—try narrower paths or manual run"
    except KeyboardInterrupt:
        print("\nPylint interrupted by user.")
        sys.exit(1)
    except Exception as e:
        return [], f"pylint failed: {str(e)}"


def run_mypy(paths):
    if not check_tool('mypy'):
        return [], "mypy not installed. Install with: pip install mypy"
    print("Running mypy on files... (press Ctrl+C to interrupt)")
    expanded_files = expand_paths(paths)
    if not expanded_files:
        return [], "No Python files found in paths"
    cmd = ['mypy', '--show-error-codes'] + list(expanded_files)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=args.timeout)
        issues = []
        pattern = re.compile(r'^(?P<path>[^:]+):(?P<line>\d+): (?P<severity>\w+): (?P<message>.*) \[(?P<code>[-_a-zA-Z0-9]+)\]$')
        for line in result.stdout.splitlines():
            match = pattern.match(line.strip())
            if match:
                issues.append({
                    'path': match.group('path'),
                    'line': int(match.group('line')),
                    'message': match.group('message'),
                    'message-id': match.group('code'),
                    'severity': match.group('severity')
                })
        return issues, None
    except subprocess.TimeoutExpired:
        return [], f"mypy timed out after {args.timeout} seconds—try narrower paths or manual run"
    except KeyboardInterrupt:
        print("\nMypy interrupted by user.")
        sys.exit(1)
    except Exception as e:
        return [], f"mypy failed: {str(e)}"


def generate_overrides(issues, tool):
    """Build per-file overrides, optionally filtering by safe-mode rules."""
    overrides = {}
    for issue in issues:
        file = issue.get('path') if isinstance(issue, dict) else issue['path']
        code = issue.get('message-id') if isinstance(issue, dict) else issue['message-id']
        if not file or not code:
            continue
        if args.safe_mode:
            if tool == 'pylint':
                if not any(str(code).startswith(p) for p in args.allow_pylint_prefixes):
                    continue
            elif tool == 'mypy':
                if code not in set(args.allow_mypy_codes):
                    continue
        overrides.setdefault(file, set()).add(code)
    return {f: sorted(list(codes)) for f, codes in overrides.items()}


# Run scans
pylint_issues, pylint_warn = run_pylint(args.paths)
mypy_issues, mypy_warn = run_mypy(args.paths)

pylint_overrides = generate_overrides(pylint_issues, 'pylint')
mypy_overrides = generate_overrides(mypy_issues, 'mypy')

warnings = []
if pylint_warn:
    warnings.append(pylint_warn)
if mypy_warn:
    warnings.append(mypy_warn)
if not pylint_issues and not mypy_issues and not warnings:
    warnings.append("No issues detected.")

issues = []
# Include only issues that pass safe-mode filters by intersecting with overrides
allowed_pyl = { (f, c) for f, codes in pylint_overrides.items() for c in codes }
allowed_mypy = { (f, c) for f, codes in mypy_overrides.items() for c in codes }
for item in pylint_issues:
    try:
        path = item.get('path') or item.get('filename')
        code = item.get('message-id')
        line = int(item.get('line') or 1)
        msg = item.get('message') or ''
        if path and code and (path, code) in allowed_pyl:
            issues.append({'tool': 'pylint', 'path': path, 'line': line, 'message-id': code, 'message': msg})
    except Exception:
        pass
for item in mypy_issues:
    try:
        path = item.get('path')
        code = item.get('message-id')
        line = int(item.get('line') or 1)
        msg = item.get('message') or ''
        if path and code and (path, code) in allowed_mypy:
            issues.append({'tool': 'mypy', 'path': path, 'line': line, 'message-id': code, 'message': msg})
    except Exception:
        pass

plan = {
    'files': sorted(list(set(list(pylint_overrides.keys()) + list(mypy_overrides.keys())))),
    'pylint_overrides': pylint_overrides,
    'mypy_overrides': mypy_overrides,
    'issues': issues,
    'warnings': warnings
}

# Limit to max_files if specified
if args.max_files > 0:
    file_issue_counts = {f: len(pylint_overrides.get(f, [])) + len(mypy_overrides.get(f, [])) for f in plan['files']}
    sorted_files = [k for k, _ in sorted(file_issue_counts.items(), key=lambda kv: kv[1], reverse=True)[:args.max_files]]
    plan['files'] = sorted_files
    plan['pylint_overrides'] = {f: v for f, v in pylint_overrides.items() if f in sorted_files}
    plan['mypy_overrides'] = {f: v for f, v in mypy_overrides.items() if f in sorted_files}

if args.json:
    print(json.dumps(plan, indent=2))
else:
    print("files:", plan['files'])
    print("warnings:", plan['warnings'])

if args.plan_file:
    with open(args.plan_file, 'w') as f:
        yaml.dump(plan, f)
    print(f"Wrote plan to {args.plan_file}")

if args.apply and plan['files']:
    if not args.y and input("Apply changes? (y/n): ").lower() != 'y':
        print("Aborted.")
        sys.exit(0)

    def apply_pylint_overrides(overrides, rcfile='.pylintrc'):
        if os.path.exists(rcfile):
            shutil.copy(rcfile, f'{rcfile}.bak')
        else:
            with open(rcfile, 'w') as f:
                f.write('[MASTER]\n')
        config = configparser.ConfigParser()
        config.read(rcfile)
        for file_path, disables in overrides.items():
            section = f'pylint.file:{file_path}'
            config[section] = {'disable': ','.join(disables)}
        with open(rcfile, 'w') as f:
            config.write(f)

    def apply_mypy_overrides(overrides, config_file='pyproject.toml'):
        if os.path.exists(config_file):
            with open(config_file, 'rb') as f:
                config = tomli.load(f)
            shutil.copy(config_file, f'{config_file}.bak')
            if 'tool' not in config:
                config['tool'] = {}
            if 'mypy' not in config['tool']:
                config['tool']['mypy'] = {}
            if 'overrides' not in config['tool']['mypy']:
                config['tool']['mypy']['overrides'] = []
            for file_path, codes in overrides.items():
                config['tool']['mypy']['overrides'].append({
                    'module': file_path.replace('/', '.').rstrip('.py'),
                    'ignore_errors': True
                })
            with open(config_file, 'wb') as f:
                tomli_w.dump(config, f)
        else:
            ini_file = 'mypy.ini'
            if os.path.exists(ini_file):
                shutil.copy(ini_file, f'{ini_file}.bak')
            config = configparser.ConfigParser()
            config.read(ini_file)
            for file_path, codes in overrides.items():
                module = file_path.replace('/', '.').rstrip('.py')
                section = f'mypy-{module}'
                config[section] = {'ignore_errors': 'True'}
            with open(ini_file, 'w') as f:
                config.write(f)

    apply_pylint_overrides(plan['pylint_overrides'])
    apply_mypy_overrides(plan['mypy_overrides'])

    if args.git_stage:
        files_to_stage = [f for f in ['.pylintrc', 'pyproject.toml', 'mypy.ini'] if os.path.exists(f)]
        if files_to_stage:
            subprocess.run(['git', 'add'] + files_to_stage)
        print("Staged config changes to git.")

    print("Changes applied.")
elif args.apply:
    print("Nothing to apply; plan is empty.")
