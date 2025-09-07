# Ensure third-party pytest plugins from the global environment do not auto-load.
# This prevents import errors from plugins like pytest-postgresql that require libpq/psycopg.
import os
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
