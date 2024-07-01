from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, ForeignKey, Identity, Double
)

Models = MetaData()

Region: Table = Table(
    'region',
    Models,
    Column('id', Integer, primary_key=True),
    Column('name', String(20))
)

Municipality: Table = Table(
    'municipality',
    Models,
    Column('id', Integer, primary_key=True),
    Column('name', String(20)),
    Column('region_id', ForeignKey('region.id'), nullable=False)
)

Place: Table = Table(
    'place',
    Models,
    Column('id', Integer, primary_key=True),
    Column('name', String(40)),
    Column('municipality_id', ForeignKey('municipality.id'), nullable=False)
)

School: Table = Table(
    'school',
    Models,
    Column('id', String(10), primary_key=True),
    Column('name', String(150), nullable=False),
    Column('place_id', ForeignKey('place.id'), nullable=False)
)

Examination: Table = Table(
    'examination',
    Models,
    # id will be in the form: nvo-4-2022
    Column('id', String(15), primary_key=True),

    # type will be НВО or ДЗИ
    Column('type', String(5)),
    Column('year', Integer),
    Column('grade_level', Integer),
)

ExaminationScore: Table = Table(
    'examination_score',
    Models,

    Column('examination_id', ForeignKey('examination.id'), nullable=False, primary_key=True),
    Column('school_id', ForeignKey('school.id'), nullable=False, primary_key=True),

    # subject will be МАТ, БЕЛ,...
    Column('subject', String(10), nullable=False, primary_key=True),

    # subject specifier will be B1-1, B2, ...
    Column('subject_specifier', String(10), nullable=False, primary_key=True),

    Column('people', Integer),
    Column('score', Double),
    Column('max_possible_score', Double)
)
