# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""scheduler

Revision ID: a7089f396110
Revises: 5c5f07c6f2fa
Create Date: 2019-11-27 12:04:36.037667

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a7089f396110'
down_revision = '5c5f07c6f2fa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trial', sa.Column('time_ended', sa.DateTime(),
                                     nullable=True))
    op.add_column('trial',
                  sa.Column('time_started', sa.DateTime(), nullable=True))
    op.drop_column('trial', 'time_created')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'trial',
        sa.Column('time_created',
                  postgresql.TIMESTAMP(),
                  server_default=sa.text('now()'),
                  autoincrement=False,
                  nullable=True))
    op.drop_column('trial', 'time_started')
    op.drop_column('trial', 'time_ended')
    # ### end Alembic commands ###