#!/usr/bin/env python3
"""
grok-setup.py: Quick-start CLI to bootstrap PetPlantr with Grok.

Features:
- Ensures venv + deps via scripts/install_dependencies.sh
- Creates a .env if missing and injects GROK_API_KEY (if provided)
- Optionally launches start-petplantr.sh with validation

Usage examples:
  python grok-setup.py --api-key $GROK_API_KEY --validate
  python grok-setup.py --dir "$HOME/PetPlantr" --production
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str], cwd: Path | None = None, check: bool = True) -> int:
	print(f"[grok-setup] $ {' '.join(cmd)}")
	return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check).returncode


def ensure_env_file(project_dir: Path, api_key: str | None) -> None:
	env_path = project_dir / ".env"
	if not env_path.exists():
		tmpl = project_dir / ".env.template"
		if tmpl.exists():
			env_path.write_text(tmpl.read_text())
		else:
			env_path.write_text("")
	if api_key:
		# Append or replace GROK_API_KEY entry
		content = env_path.read_text()
		lines = [l for l in content.splitlines() if not l.startswith("GROK_API_KEY=")]
		lines.append(f"GROK_API_KEY={api_key}")
		env_path.write_text("\n".join(lines) + "\n")
		print(f"[grok-setup] Wrote GROK_API_KEY to {env_path}")


def main() -> int:
	parser = argparse.ArgumentParser(description="Bootstrap PetPlantr with Grok")
	parser.add_argument("--dir", dest="project_dir", default=str(Path.cwd()), help="Project directory")
	parser.add_argument("--api-key", dest="api_key", default=None, help="Grok API key to inject into .env")
	parser.add_argument("--production", action="store_true", help="Launch with gunicorn/uvicorn workers")
	parser.add_argument("--validate", action="store_true", help="Validate health and Grok endpoint after launch")
	parser.add_argument("--no-launch", action="store_true", help="Only prepare env, do not launch")
	args = parser.parse_args()

	project = Path(args.project_dir).expanduser().resolve()
	project.mkdir(parents=True, exist_ok=True)
	print(f"[grok-setup] Project: {project}")

	# Ensure dependencies
	sh([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], cwd=project)
	install_script = project / "scripts" / "install_dependencies.sh"
	if install_script.exists():
		sh(["bash", str(install_script)], cwd=project)
	else:
		# Fallback minimal deps
		sh([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "requests"], cwd=project)

	# .env update
	ensure_env_file(project, args.api_key)

	if args.no_launch:
		print("[grok-setup] Environment prepared (no launch)")
		return 0

	# Launch
	start = project / "start-petplantr.sh"
	if not start.exists():
		print("[grok-setup] ERROR: start-petplantr.sh not found in project directory")
		return 2
	os.chmod(start, 0o755)
	cmd = [str(start)]
	if args.production:
		cmd.append("--production")
	if args.validate:
		cmd.append("--validate")
	if args.api_key:
		cmd.extend(["--api-key", args.api_key])
	return sh(cmd, cwd=project)


if __name__ == "__main__":
	raise SystemExit(main())
