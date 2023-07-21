"""empty message

Revision ID: 2048ebba9b87
Revises: 78c1a000d3cd
Create Date: 2023-07-15 23:07:37.502337

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2048ebba9b87'
down_revision = '78c1a000d3cd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Amazon', schema=None) as batch_op:
        batch_op.alter_column('product_price',
               existing_type=sa.NUMERIC(precision=2, scale=0),
               type_=sa.Numeric(precision=5, scale=2),
               existing_nullable=False)
        batch_op.alter_column('delivery_price',
               existing_type=sa.NUMERIC(precision=2, scale=0),
               type_=sa.Numeric(precision=5, scale=2),
               existing_nullable=False)
        batch_op.alter_column('total_price',
               existing_type=sa.NUMERIC(precision=2, scale=0),
               type_=sa.Numeric(precision=5, scale=2),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Amazon', schema=None) as batch_op:
        batch_op.alter_column('total_price',
               existing_type=sa.Numeric(precision=5, scale=2),
               type_=sa.NUMERIC(precision=2, scale=0),
               existing_nullable=False)
        batch_op.alter_column('delivery_price',
               existing_type=sa.Numeric(precision=5, scale=2),
               type_=sa.NUMERIC(precision=2, scale=0),
               existing_nullable=False)
        batch_op.alter_column('product_price',
               existing_type=sa.Numeric(precision=5, scale=2),
               type_=sa.NUMERIC(precision=2, scale=0),
               existing_nullable=False)

    # ### end Alembic commands ###