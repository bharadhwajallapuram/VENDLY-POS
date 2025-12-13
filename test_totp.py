import pyotp
import time
from datetime import datetime, UTC

# Test TOTP with same secret used in the QR code
secret = "RZH2MDXXETQWQFH4DRP3IKJSWPQBZZU"
totp = pyotp.TOTP(secret)

# Get current and adjacent tokens
now_token = totp.now()
print(f"Current token: {now_token}")
print(f"Current time: {datetime.now(UTC)}")

# Test verification with different windows
print("\nVerification tests:")
for window in [0, 1, 2, 5]:
    result = totp.verify(now_token, valid_window=window)
    print(f"  Window {window}: {result}")

# Get the provisioning URI
uri = totp.provisioning_uri(name='admin@vendly.com', issuer_name='Vendly POS')
print(f"\nProvisioning URI: {uri}")

# Also test with a token entered 5 seconds ago (user lag)
print("\n--- Testing time drift scenarios ---")
time_drift_tokens = {}
for offset in [-35, -30, -5, 0, 5, 30, 35]:
    # Calculate what token would be valid at that time
    test_time = int(time.time()) + offset
    token_at_time = pyotp.TOTP(secret).at(test_time)
    time_drift_tokens[offset] = token_at_time
    
    # Test with window=1 (current default)
    result = totp.verify(token_at_time, valid_window=1)
    print(f"Token from {offset:3d} seconds: {token_at_time} -> Valid(window=1): {result}")
