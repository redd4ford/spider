from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Text
)


urls_table = Table(
    'url',
    MetaData(),
    Column('id', Integer, primary_key=True, autoincrement=True, index=True),
    Column('url', String, nullable=False, unique=True),
    Column('title', Text, onupdate=True),
    Column('parent', String, nullable=False),
    Column('html', Text),
)

urls_unique_constraint = f'{urls_table.name}_url_key'
