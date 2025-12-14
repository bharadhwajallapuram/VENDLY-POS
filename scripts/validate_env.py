#!/usr/bin/env python
"""
Vendly POS - Production Environment Validation

This script validates all required environment variables before startup.
Run this before docker-compose up to catch missing secrets early.

Usage:
    python scripts/validate_env.py
    python scripts/validate_env.py --env .env.production

Environment Variables Checked:
    - All required secrets (SECRET_KEY, JWT_SECRET)
    - Database configuration
    - API endpoints (CORS, frontend URL)
    - Payment integration (Stripe)
    - Email configuration
    - Monitoring setup
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple


class EnvValidator:
    """Validates production environment configuration"""

    # Required variables that must NOT be empty
    REQUIRED_VARS = {
        "APP_ENV": "production",
        "SECRET_KEY": "Must be 32+ character random string",
        "JWT_SECRET": "Must be 32+ character random string",
        "DATABASE_URL": "PostgreSQL connection string",
        "POSTGRES_USER": "Database username",
        "POSTGRES_PASSWORD": "Database password (32+ chars)",
        "POSTGRES_DB": "Database name",
        "REDIS_URL": "Redis connection string with password",
        "REDIS_PASSWORD": "Redis password",
        "CORS_ORIGINS": "Production domain(s)",
        "NEXT_PUBLIC_API_URL": "Frontend API endpoint",
        "STRIPE_SECRET_KEY": "Stripe API key",
        "GRAFANA_ADMIN_PASSWORD": "Grafana admin password",
        "DOMAIN": "Production domain",
    }

    # Optional but recommended
    OPTIONAL_RECOMMENDED = {
        "SMTP_HOST": "Email SMTP server",
        "SMTP_USER": "Email account",
        "SMTP_PASSWORD": "Email password",
        "STRIPE_PUBLISHABLE_KEY": "Stripe publishable key",
    }

    # Validation rules
    VALIDATIONS = {
        "APP_ENV": lambda x: x == "production",
        "SECRET_KEY": lambda x: len(x) >= 32,
        "JWT_SECRET": lambda x: len(x) >= 32,
        "POSTGRES_PASSWORD": lambda x: len(x) >= 32,
        "REDIS_PASSWORD": lambda x: len(x) >= 32,
        "DATABASE_URL": lambda x: "postgresql://" in x and "@" in x,
        "REDIS_URL": lambda x: "redis://" in x,
        "CORS_ORIGINS": lambda x: "https://" in x or "http://" in x,
        "NEXT_PUBLIC_API_URL": lambda x: "http" in x,
        "STRIPE_SECRET_KEY": lambda x: x.startswith("sk_"),
        "DOMAIN": lambda x: "." in x,
    }

    def __init__(self, env_file: str = ".env.production"):
        self.env_file = env_file
        self.env_vars: Dict[str, str] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def load_env_file(self) -> bool:
        """Load environment variables from file"""
        if not os.path.exists(self.env_file):
            self.errors.append(f"Environment file not found: {self.env_file}")
            return False

        try:
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # Parse KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self.env_vars[key.strip()] = value.strip()
            return True
        except Exception as e:
            self.errors.append(f"Error reading {self.env_file}: {e}")
            return False

    def validate_required(self) -> bool:
        """Check all required variables are set"""
        all_valid = True
        for var_name, description in self.REQUIRED_VARS.items():
            value = self.env_vars.get(var_name, "").strip()

            if not value:
                self.errors.append(
                    f"❌ MISSING: {var_name} ({description})"
                )
                all_valid = False
            elif value.startswith("REQUIRED_"):
                self.errors.append(
                    f"❌ NOT SET: {var_name} = {value} ({description})"
                )
                all_valid = False
            elif var_name in self.VALIDATIONS:
                if not self.VALIDATIONS[var_name](value):
                    self.errors.append(
                        f"❌ INVALID: {var_name} = {value[:30]}... ({description})"
                    )
                    all_valid = False
            else:
                self.info.append(f"✓ {var_name}")

        return all_valid

    def validate_optional(self) -> None:
        """Check recommended optional variables"""
        for var_name, description in self.OPTIONAL_RECOMMENDED.items():
            value = self.env_vars.get(var_name, "").strip()

            if not value or value.startswith("REQUIRED_"):
                self.warnings.append(
                    f"⚠ OPTIONAL: {var_name} not set ({description})"
                )
            else:
                self.info.append(f"✓ {var_name} (optional)")

    def validate_security(self) -> bool:
        """Check security-specific constraints"""
        all_valid = True

        # Check for common weak passwords
        weak_patterns = ["password", "123456", "admin", "test", "demo"]
        for var_name in ["SECRET_KEY", "JWT_SECRET", "POSTGRES_PASSWORD", "REDIS_PASSWORD"]:
            value = self.env_vars.get(var_name, "").lower()
            if any(weak in value for weak in weak_patterns):
                self.errors.append(
                    f"❌ WEAK: {var_name} appears to contain weak pattern"
                )
                all_valid = False

        # Check CORS doesn't include localhost in production
        cors = self.env_vars.get("CORS_ORIGINS", "")
        if "localhost" in cors.lower():
            self.errors.append(
                "❌ LOCALHOST: CORS_ORIGINS should not include localhost in production"
            )
            all_valid = False

        # Check production domain doesn't have typos
        domain = self.env_vars.get("DOMAIN", "")
        if domain.count(".") < 1:
            self.errors.append(
                f"❌ INVALID_DOMAIN: {domain} doesn't look like a valid domain"
            )
            all_valid = False

        # Check Stripe keys are production keys in production
        stripe_key = self.env_vars.get("STRIPE_SECRET_KEY", "")
        if stripe_key.startswith("sk_test_"):
            self.errors.append(
                "❌ TEST_STRIPE: Using test Stripe key in production (sk_test_)"
            )
            all_valid = False

        return all_valid

    def validate_connections(self) -> None:
        """Check connection strings are well-formed"""
        # Database URL validation
        db_url = self.env_vars.get("DATABASE_URL", "")
        if db_url and "postgresql://" in db_url:
            if "@" not in db_url or ":" not in db_url.split("@")[0]:
                self.errors.append(
                    "❌ DATABASE_URL format invalid: must be postgresql://user:pass@host:port/db"
                )

        # Redis URL validation
        redis_url = self.env_vars.get("REDIS_URL", "")
        if redis_url and "redis://" in redis_url:
            if "@" not in redis_url:
                self.errors.append(
                    "❌ REDIS_URL format invalid: must include password (redis://:password@host)"
                )

    def print_report(self) -> None:
        """Print validation report"""
        print("\n" + "=" * 70)
        print(" VENDLY POS - ENVIRONMENT VALIDATION REPORT")
        print("=" * 70 + "\n")

        if self.info:
            print("✓ VALID SETTINGS:")
            for msg in self.info[:10]:  # Show first 10
                print(f"  {msg}")
            if len(self.info) > 10:
                print(f"  ... and {len(self.info) - 10} more valid settings")
            print()

        if self.warnings:
            print("⚠ WARNINGS (optional):")
            for msg in self.warnings:
                print(f"  {msg}")
            print()

        if self.errors:
            print("❌ ERRORS (must fix before production):")
            for i, msg in enumerate(self.errors, 1):
                print(f"  {i}. {msg}")
            print()
            print("=" * 70)
            print("PRODUCTION DEPLOYMENT BLOCKED - Fix errors above")
            print("=" * 70 + "\n")
        else:
            print("=" * 70)
            print("✓ ALL VALIDATIONS PASSED - Ready for production!")
            print("=" * 70 + "\n")
            print("Next steps:")
            print("  1. Review all settings above")
            print("  2. Start with: docker-compose up -d")
            print("  3. Monitor: docker-compose logs -f backend")
            print("  4. Health check: curl https://yourdomain.com/health\n")

    def validate(self) -> bool:
        """Run all validations"""
        print(f"\nValidating environment file: {self.env_file}\n")

        if not self.load_env_file():
            self.print_report()
            return False

        req_valid = self.validate_required()
        self.validate_optional()
        sec_valid = self.validate_security()
        self.validate_connections()

        self.print_report()

        return req_valid and sec_valid


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Vendly POS production environment"
    )
    parser.add_argument(
        "--env",
        default=".env.production",
        help="Path to environment file (default: .env.production)",
    )

    args = parser.parse_args()

    validator = EnvValidator(args.env)
    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
