"""One-time DB initialization: create tables + enable secure RLS on Supabase.
Run: python init_db.py

Security model: the backend connects as the Postgres owner role (via the
transaction pooler), which BYPASSES RLS. We ENABLE RLS with NO policies so the
public anon/publishable API key cannot read/write any data. Only the backend
(holding the DB password in .env) can access the data.
"""
import asyncio
from sqlalchemy import text
from database import engine
from models import metadata

RLS_TABLES = ['bookings', 'payment_transactions', 'settings', 'site_content']


async def main():
    async with engine.begin() as conn:
        # Create tables (idempotent)
        await conn.run_sync(metadata.create_all)
        # Enable RLS (deny-all for anon/public API; owner role bypasses RLS)
        for t in RLS_TABLES:
            await conn.execute(text(f'ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;'))
        print('Tables created and RLS enabled on:', ', '.join(RLS_TABLES))
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
