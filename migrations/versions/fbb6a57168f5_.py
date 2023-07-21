"""empty message

Revision ID: fbb6a57168f5
Revises: b7374bd8a7c2
Create Date: 2023-07-15 19:48:38.378812

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbb6a57168f5'
down_revision = 'b7374bd8a7c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Amazon', schema=None) as batch_op:
        batch_op.alter_column('isbn',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=13),
               existing_nullable=False,
               existing_server_default=sa.text('nextval(\'"Amazon_isbn_seq"\'::regclass)'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Amazon', schema=None) as batch_op:
        batch_op.alter_column('isbn',
               existing_type=sa.String(length=13),
               type_=sa.INTEGER(),
               existing_nullable=False,
               existing_server_default=sa.text('nextval(\'"Amazon_isbn_seq"\'::regclass)'))

    # ### end Alembic commands ###
