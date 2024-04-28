from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, ForeignKey, Identity
)

Models = MetaData()

Region: Table = Table(
    'region',
    Models,
    Column('id', Integer, Identity()),
    Column('name', String(20))
)

Municipality: Table = Table(
    'municipality',
    Models,
    Column('id', Integer, Identity()),
    Column('name', String(20)),
    Column('region_id', ForeignKey('region.id'), nullable=False)
)

Place: Table = Table(
    'place',
    Models,
    Column('id', Integer, Identity()),
    Column('name', String(20)),
    Column('municipality_id', ForeignKey('municipality.id'), nullable=False)
)

School: Table = Table(
    'school',
    Models,
    Column('id', String(10), primary_key=True),
    Column('name', String(30), nullable=False),
    Column('place_id', ForeignKey('place.id'), nullable=False)
)
