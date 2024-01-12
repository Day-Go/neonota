import configparser
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load the configuration file
config = configparser.ConfigParser()
files_read = config.read('config.ini')
if not files_read:
    raise FileNotFoundError("Could not read config.ini file")

# Extract the PostgreSQL connection URL
postgresql_url = config['database']['url']

# Create a SQLAlchemy engine
engine = create_engine(postgresql_url)

# Define the Base class using the declarative system
Base = declarative_base()

# Create a sessionmaker
Session = sessionmaker(bind=engine)

# Function to create tables
def create_tables():
    from models import Base
    Base.metadata.create_all(engine)

