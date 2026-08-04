"""
Database Configuration
=======================
Sets up the SQLAlchemy engine, session factory, and declarative Base
that every model in the app will inherit from.

The connection string is read from a DATABASE_URL environment variable
(loaded from a local .env file). If DATABASE_URL is not set, it falls
back to a local SQLite file so the project still runs with zero setup.

To use Supabase (Postgres), put your Supabase connection string in a
.env file at the project root:

    DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.YOUR-PROJECT-REF.supabase.co:5432/postgres

Get this string from: Supabase Dashboard -> your project -> Project
Settings -> Database -> Connection string -> URI tab.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load variables from a .env file in the project root (if present)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskflow.db")

# check_same_thread is a SQLite-only quirk — only pass it when using SQLite.
# Postgres/Supabase connections don't need (or accept) this argument.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,   # test each connection before using it; silently
                           # replaces one that Supabase's pooler already closed
    pool_recycle=300,     # proactively recycle connections every 5 minutes,
                           # before Supabase's pooler has a chance to drop them
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

