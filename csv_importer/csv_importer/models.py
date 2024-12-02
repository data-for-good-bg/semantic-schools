"""
This module defines the database models (or tables) with SQLAlchemy.

It uses the SQLAlchemy Database Metadata classes Table and Column.
It seems the "Database Metadata" is the SQLAlchemy lower level API,
while SQLAlechemy also provides the "ORM declartive form" where tables are
declared as sub-clasess of DeclarativeBase class.

The "Database Metadata" classes were chosen here mainly because I [vitali]
didn't have any knowledge about SQLAlchemy.
"""

from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, ForeignKey, Numeric
)

Models = MetaData()

WikidataId = String(100)
AreaId = String(100)
Longitude = String(15)
Latitude = String(15)

# Describes the adminstrative teritorial unit Region -> Област.
# The ID is auto-inc value implemented in db_actions.py
Region: Table = Table(
    'region',
    Models,
    Column('id', WikidataId, primary_key=True),
    Column('name', String(20)),
    Column('area_id', AreaId),
    Column('longitude', Longitude),
    Column('latitude', Latitude)
)

# Describes the adminstrative teritorial unit Municipality -> Община.
# The ID is auto-inc value implemented in db_actions.py
Municipality: Table = Table(
    'municipality',
    Models,
    Column('id', WikidataId, primary_key=True),
    Column('name', String(20)),
    Column('region_id', ForeignKey('region.id'), nullable=False),
    Column('area_id', AreaId),
    Column('longitude', Longitude),
    Column('latitude', Latitude)
)

# Describes the cities and villages.
# The ID is auto-inc value implemented in db_actions.py
Place: Table = Table(
    'place',
    Models,
    Column('id', WikidataId, primary_key=True),
    Column('name', String(40)),
    Column('municipality_id', ForeignKey('municipality.id'), nullable=False),
    Column('type', String(4)),
    Column('area_id', AreaId),
    Column('longitude', Longitude),
    Column('latitude', Latitude)
)

# Describes the builgarian schools.
# The ID is string value found in the NVO and DZI CSV files. The column
# in different CSV files is known as "Код по АДМИН", "Код" or "Код по НЕИСПОУ"
# and it is assumed to be unique and the same for each school in all CSV files.
#
# The name of the school is the value from the CSV file where certain school
# is found for the first time. On subsequent imports if a school is found
# by its id in the database, the name will not be updated.
School: Table = Table(
    'school',
    Models,
    Column('id', String(10), primary_key=True),
    Column('name', String(150), nullable=False),
    Column('place_id', ForeignKey('place.id'), nullable=False),
    Column('longitude', Longitude),
    Column('latitude', Latitude)
)

# Examination table representation one examination session or "Изпитна сесия".
# An examination session is described
# * with type of the session - 'nvo' or 'dzi'
# * with year - possible values 2024, 2023, etc
# * with grade_level
#   * for NVO possible values are 4, 7 and 10
#   * for DZI the value is always 12
#
# The id is a string in the form '<type>-<year>-<grade_level>'
#
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


# Examination score table supplements the Examination table.
# In this table each record describes the result:
# * of given school - school_id
# * on given subject - this is the unique abbreviation of the subject, check
#   the documentation of SubjectItem class in db_manage.py
# * people - number of attented people on that subject from that school
# * score - the average score of the attendees
# * max_possible_score - describes the max possible score, it could be 6
#   for DZI and 65 or 100 for NVO.
#   TODO: This column belongs to Examination and could be moved there.
#
ExaminationScore: Table = Table(
    'examination_score',
    Models,

    Column('examination_id', ForeignKey('examination.id'), nullable=False, primary_key=True),
    Column('school_id', ForeignKey('school.id'), nullable=False, primary_key=True),

    # subject will be МАТ, БЕЛ,...
    Column('subject', String(10), nullable=False, primary_key=True),

    Column('people', Integer),
    Column('score', Numeric),
    Column('max_possible_score', Numeric)
)

# This table describes all possible Subjects and their different
# abbreviations.
# Check the documentation of SubjectItem class in db_manage.py
Subject: Table = Table(
    'subject',
    Models,

    Column('id', String(10), primary_key=True),
    Column('name', String(120)),
    Column('abbreviations', String(30))
)
