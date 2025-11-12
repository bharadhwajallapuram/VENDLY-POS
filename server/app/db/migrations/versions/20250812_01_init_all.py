from alembic import op
import sqlalchemy as sa

revision = "20250812_02"
down_revision = "20250812_01"
branch_labels = None
depends_on = None

role_enum = sa.Enum("clerk","manager","admin", name="user_role")

def upgrade():
    role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("role", role_enum, nullable=False, server_default="clerk"))
    # optional: promote first user created to admin later via app logic


def downgrade():
    op.drop_column("users", "role")
    role_enum.drop(op.get_bind(), checkfirst=True)