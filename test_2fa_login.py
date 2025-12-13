"""Test 2FA login flow"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, UTC, timedelta
import secrets
import pyotp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db import models as m
from app.services.two_factor_auth import TwoFactorAuthService
from app.services.auth import create_access_token

# Setup DB
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Simulate login flow
print("=== Simulating 2FA Login Flow ===\n")

# Step 1: User logs in with credentials
print("Step 1: User logs in with email/password")
user = db.query(m.User).filter(m.User.email == "admin@vendly.com").first()
print(f"  User found: {user.email}")

# Step 2: Check if 2FA is enabled
print("\nStep 2: Check if 2FA is enabled")
tfa = db.query(m.TwoFactorAuth).filter(m.TwoFactorAuth.user_id == user.id).first()
if tfa and tfa.is_enabled:
    print(f"  2FA is ENABLED for user")
    print(f"  Generating temporary token...")
    temp_token = secrets.token_urlsafe(32)
    print(f"  Temp token: {temp_token[:30]}...")
    
    # Step 3: Generate TOTP code
    print("\nStep 3: User enters TOTP code from authenticator")
    totp = pyotp.TOTP(tfa.secret)
    current_token = totp.now()
    print(f"  Current TOTP: {current_token}")
    
    # Step 4: Verify TOTP
    print("\nStep 4: Verify TOTP code")
    is_valid = TwoFactorAuthService.verify_token(tfa.secret, current_token)
    print(f"  Token valid: {is_valid}")
    
    # Step 5: Generate access token
    if is_valid:
        print("\nStep 5: Generate access token")
        access_token = create_access_token(data={"sub": str(user.id)})
        print(f"  Access token: {access_token[:30]}...")
        print(f"  Token expires in: {settings.ACCESS_TTL_MIN * 60} seconds")
        print("\n✓ 2FA login successful!")
    else:
        print("\n✗ Token verification failed!")
else:
    print("  2FA is NOT enabled")

db.close()
