from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)


urls_table = Table(
    'url',
    MetaData(),
    Column('id', Integer, primary_key=True, autoincrement=True, index=True),
    Column('url', String(600), nullable=False, unique=True),
    Column('title', Text, onupdate=True),
    Column('parent', Text, nullable=False),
    Column('html', Text),
)

urls_unique_constraint = f'{urls_table.name}_url_key'
