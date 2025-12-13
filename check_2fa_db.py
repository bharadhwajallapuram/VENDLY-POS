from app.db import models as m
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Check if 2FA exists for user 1
tfa = db.query(m.TwoFactorAuth).filter(m.TwoFactorAuth.user_id == 1).first()
if tfa:
    print(f'2FA found for user 1:')
    print(f'  Secret: {tfa.secret}')
    print(f'  Is Enabled: {tfa.is_enabled}')
    backup_code_count = len(tfa.backup_codes.split(",")) if tfa.backup_codes else 0
    print(f'  Backup codes count: {backup_code_count}')
else:
    print('No 2FA record found for user 1')

# Check if user exists
user = db.query(m.User).filter(m.User.id == 1).first()
if user:
    print(f'\nUser 1 found: {user.email}')
else:
    print('User 1 not found')

db.close()
