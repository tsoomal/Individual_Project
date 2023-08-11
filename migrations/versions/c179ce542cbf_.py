"""empty message

Revision ID: c179ce542cbf
Revises: e3b06634ab95
Create Date: 2023-08-07 19:38:24.466248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c179ce542cbf'
down_revision = 'e3b06634ab95'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Amazon',
    sa.Column('book_name', sa.String(length=200), nullable=False),
    sa.Column('amazon_link', sa.String(length=200), nullable=False),
    sa.Column('isbn', sa.String(length=13), nullable=False),
    sa.Column('edition_format', sa.String(length=40), nullable=False),
    sa.Column('new_product_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('new_delivery_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('new_total_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('used_product_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('used_delivery_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('used_total_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.PrimaryKeyConstraint('isbn')
    )
    op.create_table('Ebay',
    sa.Column('book_name', sa.String(length=200), nullable=False),
    sa.Column('ebay_link', sa.String(length=200), nullable=False),
    sa.Column('isbn', sa.String(length=13), nullable=False),
    sa.Column('edition_format', sa.String(length=40), nullable=False),
    sa.Column('new_product_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('new_delivery_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('new_total_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('historical_new_total_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('used_product_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('used_delivery_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('used_total_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.Column('historical_used_total_price', sa.ARRAY(sa.Numeric(precision=5, scale=2)), nullable=False),
    sa.PrimaryKeyConstraint('isbn')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Ebay')
    op.drop_table('Amazon')
    # ### end Alembic commands ###