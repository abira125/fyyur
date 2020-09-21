"""empty message

Revision ID: a30b7cdc449f
Revises: b6eb51f7207c
Create Date: 2020-09-20 15:50:05.839338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a30b7cdc449f'
down_revision = 'b6eb51f7207c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('show_venue_id_fkey', 'show', type_='foreignkey')
    op.drop_constraint('show_artist_id_fkey', 'show', type_='foreignkey')
    op.create_foreign_key(None, 'show', 'venue', ['venue_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'show', 'artist', ['artist_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'show', type_='foreignkey')
    op.drop_constraint(None, 'show', type_='foreignkey')
    op.create_foreign_key('show_artist_id_fkey', 'show', 'artist', ['artist_id'], ['id'])
    op.create_foreign_key('show_venue_id_fkey', 'show', 'venue', ['venue_id'], ['id'])
    # ### end Alembic commands ###
