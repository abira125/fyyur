"""empty message

Revision ID: d5d13980c58f
Revises: d81af075e397
Create Date: 2020-09-19 15:18:42.127138

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5d13980c58f'
down_revision = 'd81af075e397'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'show', 'venue', ['venue_id'], ['id'])
    op.create_foreign_key(None, 'show', 'artist', ['artist_id'], ['id'])
    op.drop_column('show', 'id')
    op.drop_column('show', 'start_time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('show', sa.Column('start_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.add_column('show', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'show', type_='foreignkey')
    op.drop_constraint(None, 'show', type_='foreignkey')
    # ### end Alembic commands ###
