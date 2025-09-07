#!/usr/bin/env python3
"""
PetPlantr Production Toggle Configuration
Manages environment switching between development and production
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

class ProductionToggle:
    """Production environment toggle management"""

    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)

        self.environments = {
            'development': {
                'stripe_publishable_key': 'pk_test_...',
                'stripe_secret_key': 'sk_test_...',
                'eventbridge_bus': 'petplantr-dev-events',
                'api_endpoint': 'http://localhost:8000',
                'database_url': 'postgresql://localhost/petplantr_dev',
                'redis_url': 'redis://localhost:6379',
                'environment': 'development'
            },
            'staging': {
                'stripe_publishable_key': 'pk_test_...',
                'stripe_secret_key': 'sk_test_...',
                'eventbridge_bus': 'petplantr-staging-events',
                'api_endpoint': 'https://staging-api.petplantr.com',
                'database_url': 'postgresql://staging-db.petplantr.com/petplantr_staging',
                'redis_url': 'redis://staging-redis.petplantr.com:6379',
                'environment': 'staging'
            },
            'production': {
                'stripe_publishable_key': os.getenv('STRIPE_PROD_PUBLISHABLE_KEY', 'pk_live_...'),
                'stripe_secret_key': os.getenv('STRIPE_PROD_SECRET_KEY', 'sk_live_...'),
                'eventbridge_bus': 'petplantr-stripe-events',
                'api_endpoint': 'https://api.petplantr.com',
                'database_url': os.getenv('PROD_DATABASE_URL', 'postgresql://prod-db.petplantr.com/petplantr_prod'),
                'redis_url': os.getenv('PROD_REDIS_URL', 'redis://prod-redis.petplantr.com:6379'),
                'environment': 'production'
            }
        }

    def get_current_environment(self) -> str:
        """Get current environment from environment variable"""
        return os.getenv('PETPLANTR_ENV', 'development')

    def get_config(self, environment: str = None) -> Dict[str, Any]:
        """Get configuration for specified environment"""
        if environment is None:
            environment = self.get_current_environment()

        if environment not in self.environments:
            raise ValueError(f"Unknown environment: {environment}")

        return self.environments[environment]

    def switch_environment(self, target_env: str) -> bool:
        """Switch to target environment"""
        if target_env not in self.environments:
            print(f"❌ Unknown environment: {target_env}")
            return False

        print(f"🔄 Switching to {target_env} environment...")

        # Update environment variable
        os.environ['PETPLANTR_ENV'] = target_env

        # Save to .env file for persistence
        env_file = Path('.env')
        current_content = env_file.read_text() if env_file.exists() else ""

        # Update or add PETPLANTR_ENV
        lines = current_content.split('\n')
        env_updated = False

        for i, line in enumerate(lines):
            if line.startswith('PETPLANTR_ENV='):
                lines[i] = f'PETPLANTR_ENV={target_env}'
                env_updated = True
                break

        if not env_updated:
            lines.append(f'PETPLANTR_ENV={target_env}')

        env_file.write_text('\n'.join(lines))

        print(f"✅ Switched to {target_env} environment")
        return True

    def validate_production_readiness(self) -> Dict[str, Any]:
        """Validate production environment readiness"""
        print("🔍 Validating production readiness...")

        config = self.get_config('production')
        issues = []
        warnings = []

        # Check required environment variables
        required_vars = [
            'STRIPE_PROD_SECRET_KEY',
            'STRIPE_PROD_PUBLISHABLE_KEY',
            'PROD_DATABASE_URL',
            'PROD_REDIS_URL'
        ]

        for var in required_vars:
            value = os.getenv(var)
            if not value or value.endswith('...'):
                issues.append(f"Missing or placeholder value for {var}")

        # Check Stripe keys format
        stripe_secret = os.getenv('STRIPE_PROD_SECRET_KEY', '')
        if stripe_secret and not stripe_secret.startswith('sk_live_'):
            warnings.append("Stripe secret key doesn't appear to be a live key")

        stripe_publishable = os.getenv('STRIPE_PROD_PUBLISHABLE_KEY', '')
        if stripe_publishable and not stripe_publishable.startswith('pk_live_'):
            warnings.append("Stripe publishable key doesn't appear to be a live key")

        # Check database URL
        db_url = os.getenv('PROD_DATABASE_URL', '')
        if db_url and 'localhost' in db_url:
            issues.append("Production database URL contains localhost")

        # Check Redis URL
        redis_url = os.getenv('PROD_REDIS_URL', '')
        if redis_url and 'localhost' in redis_url:
            issues.append("Production Redis URL contains localhost")

        result = {
            'ready': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'config': config
        }

        if result['ready']:
            print("✅ Production environment is ready!")
        else:
            print("❌ Production environment has issues:")
            for issue in issues:
                print(f"   - {issue}")

        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   - {warning}")

        return result

    def create_production_env_file(self) -> None:
        """Create production environment file template"""
        template = """# PetPlantr Production Environment Variables
# Copy this file to .env and fill in actual values

# Environment
PETPLANTR_ENV=production

# Stripe Production Keys
STRIPE_PROD_PUBLISHABLE_KEY=pk_live_your_publishable_key_here
STRIPE_PROD_SECRET_KEY=sk_live_your_secret_key_here

# Database
PROD_DATABASE_URL=postgresql://username:password@prod-db.petplantr.com:5432/petplantr_prod

# Redis
PROD_REDIS_URL=redis://prod-redis.petplantr.com:6379

# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# API
PROD_API_ENDPOINT=https://api.petplantr.com

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
DATADOG_API_KEY=your-datadog-api-key

# Security
JWT_SECRET_KEY=your-super-secure-jwt-secret-key
ENCRYPTION_KEY=your-32-character-encryption-key

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
"""

        env_template_path = self.config_dir / 'production.env.template'
        env_template_path.write_text(template)

        print(f"📄 Production environment template created: {env_template_path}")

    def backup_current_config(self) -> None:
        """Backup current configuration"""
        backup_dir = self.config_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = '2025-09-05'
        backup_file = backup_dir / f'config_backup_{timestamp}.json'

        current_config = {
            'environment': self.get_current_environment(),
            'config': self.get_config(),
            'env_vars': dict(os.environ)
        }

        with open(backup_file, 'w') as f:
            json.dump(current_config, f, indent=2, default=str)

        print(f"💾 Configuration backed up to: {backup_file}")

def main():
    """Main function for production toggle management"""
    print("🔧 PetPlantr Production Toggle Configuration")
    print("=" * 50)

    toggle = ProductionToggle()

    # Show current environment
    current_env = toggle.get_current_environment()
    print(f"Current environment: {current_env}")

    # Validate production readiness
    if current_env == 'production':
        validation = toggle.validate_production_readiness()
    else:
        print("\\n🔍 Validating production readiness...")
        validation = toggle.validate_production_readiness()

    # Create production template
    toggle.create_production_env_file()

    # Backup current config
    toggle.backup_current_config()

    print("\\n📋 Available commands:")
    print("  python production_toggle.py switch production    # Switch to production")
    print("  python production_toggle.py switch development  # Switch to development")
    print("  python production_toggle.py validate            # Validate production readiness")
    print("  python production_toggle.py backup              # Backup current config")

    # Handle command line arguments
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'switch' and len(sys.argv) > 2:
            target = sys.argv[2]
            toggle.switch_environment(target)
        elif command == 'validate':
            toggle.validate_production_readiness()
        elif command == 'backup':
            toggle.backup_current_config()
        else:
            print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
