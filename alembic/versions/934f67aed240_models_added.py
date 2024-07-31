"""models added

Revision ID: 934f67aed240
Revises: 19a5b38000dd
Create Date: 2024-07-31 21:19:20.851128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '934f67aed240'
down_revision: Union[str, None] = '19a5b38000dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Категории',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('Пользователи',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('Рецепты',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('article', sa.String(), nullable=False),
    sa.Column('ingredients', sa.String(), nullable=False),
    sa.Column('steps', sa.String(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['Категории.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by_id'], ['Пользователи.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Рецепты')
    op.drop_table('Пользователи')
    op.drop_table('Категории')
    # ### end Alembic commands ###