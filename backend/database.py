from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    # "postgresql://postgres:postgres@postgres:5432/smart_retail_db"
#    "postgresql://postgres:password@localhost:5432/retail_db"
"postgresql://ravitiwari@localhost:5432/retail_db"
)
#DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/smart_retail_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()