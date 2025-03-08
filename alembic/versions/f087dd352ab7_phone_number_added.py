"""phone number added

Revision ID: f087dd352ab7
Revises: 
Create Date: 2025-02-19 15:32:30.193380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f087dd352ab7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True)) # bu kısmda User tablosuna phone_number adında sütun ekledim..!


def downgrade() -> None:
    # op.drop_column('users', 'phone_number') # bu kısımda sütun silmek istersem yapmam gerekenlerdir. Önce sütununu silmek istediğim tablonun adını verdim sonra da sütunun adını verdim..!
    pass   # çok fazla kullanılmaz..!