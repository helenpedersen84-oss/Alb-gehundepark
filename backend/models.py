from sqlalchemy import (
    MetaData, Table, Column, String, Integer, Numeric, Text, DateTime, func,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

bookings = Table(
    'bookings', metadata,
    Column('id', String(64), primary_key=True),
    Column('date', String(20), nullable=False, index=True),
    Column('hour', Integer, nullable=False),
    Column('name', Text, nullable=False),
    Column('email', Text, nullable=False),
    Column('phone', Text),
    Column('dogs', Integer, nullable=False, default=1),
    Column('amount', Numeric, nullable=False),
    Column('currency', String(8), nullable=False, default='dkk'),
    Column('status', String(16), nullable=False, default='locked'),
    Column('session_id', String(255)),
    Column('expires_at', DateTime(timezone=True)),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

payment_transactions = Table(
    'payment_transactions', metadata,
    Column('id', String(64), primary_key=True),
    Column('session_id', String(255), unique=True, index=True),
    Column('booking_id', String(64), index=True),
    Column('amount', Numeric),
    Column('currency', String(8)),
    Column('payment_status', String(32)),
    Column('status', String(32)),
    Column('meta', JSONB),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Column('updated_at', DateTime(timezone=True), server_default=func.now()),
)

settings = Table(
    'settings', metadata,
    Column('id', String(32), primary_key=True),
    Column('single_visit_price', Numeric),
    Column('extra_dog_price', Numeric),
    Column('ten_trip_price', Numeric),
    Column('currency', String(8)),
    Column('updated_at', DateTime(timezone=True), server_default=func.now()),
)

site_content = Table(
    'site_content', metadata,
    Column('id', String(32), primary_key=True),
    Column('hero', JSONB),
    Column('about', JSONB),
    Column('contact', JSONB),
    Column('updated_at', DateTime(timezone=True), server_default=func.now()),
)
