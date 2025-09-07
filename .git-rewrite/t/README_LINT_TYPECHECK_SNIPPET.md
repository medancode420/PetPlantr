## Lint and Typecheck

Ensure backend code quality with pylint and mypy.

1. Install tools (once):
   - pip install pylint mypy

2. Configs: `.pylintrc` and `mypy.ini` live at repo root.

3. Run checks:

```bash
chmod +x ./run-lint-typecheck.sh
./run-lint-typecheck.sh            # default files, verbose
./run-lint-typecheck.sh -q         # quiet mode
./run-lint-typecheck.sh --no-fail  # do not fail CI/local shell
./run-lint-typecheck.sh -- api_server_minimal.py src/services/mesh_governor.py
```

Tip: If you hit typing issues (e.g., CollectorRegistry), paste the error in a chat and ask for a minimal, typed fix.

CI: Add this script to your pipeline to enforce quality gates before deploys.
