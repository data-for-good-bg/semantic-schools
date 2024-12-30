"""
This module defines the database models (or tables) with SQLAlchemy.

It uses the SQLAlchemy Database Metadata classes Table and Column.
It seems the "Database Metadata" is the SQLAlchemy lower level API,
while SQLAlchemy also provides the "ORM declarative form" where tables are
declared as sub-classes of DeclarativeBase class.

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
EditStampType = String(60)


# This is the name of the column added in most of the tables and it contains
# information for the last edition of the row. In case the update is done
# from Airflow DAG it will contain the DAG RUN_ID, which contains a timestamp.
# In case the edition is then by running the app manually, then the column
# will contain timestamp + the value of USER env var.
EDIT_STAMP = 'edit_stamp'


# Describes the administrative territorial unit Region -> Област.
# The ID is a string which in most of the cases should be the wikidata URI
# of the region subject.
# There's one special case for the Bulgarian schools in foreign countries,
# their region is `Чужбина` for id and name.
#
# There area_id, longitude and latitude are extracted from wikidata.
Region: Table = Table(
    'region',
    Models,
    Column('id', WikidataId, primary_key=True),
    Column('name', String(20)),
    Column('area_id', AreaId),
    Column('longitude', Longitude),
    Column('latitude', Latitude),
    Column(EDIT_STAMP, EditStampType)
)


# Describes the administrative territorial unit Municipality -> Община.
# Check the comments for Region model, all of them are applicable here.
Municipality: Table = Table(
    'municipality',
    Models,
    Column('id', WikidataId, primary_key=True),
    Column('name', String(20)),
    Column('region_id', ForeignKey('region.id'), nullable=False),
    Column('area_id', AreaId),
    Column('longitude', Longitude),
    Column('latitude', Latitude),
    Column(EDIT_STAMP, EditStampType)
)


# Describes the cities and villages.
# Check the comments for Region model, all of them are applicable here.
# The `type` column has two possible values - `село` and `град`.
Place: Table = Table(
    'place',
    Models,
    Column('id', WikidataId, primary_key=True),
    Column('name', String(40)),
    Column('municipality_id', ForeignKey('municipality.id'), nullable=False),
    Column('type', String(4)),
    Column('area_id', AreaId),
    Column('longitude', Longitude),
    Column('latitude', Latitude),
    Column(EDIT_STAMP, EditStampType)
)


# Describes the bulgarian schools.
# The ID is string value found in wikidata or in the NVO and DZI CSV files.
# The wikidata property for bg_school_id is wdt:P9034.
# In the CSV files school_id is known differently - "Код по АДМИН", "Код" or "Код по НЕИСПОУ"
# and it is assumed to be unique and the same for each school in all CSV files.
#
# The name of the school is the value from wikidata or from the CSV file where
# certain school is found for the first time. On subsequent imports if a
# school is found by its id in the database, the name will not be updated.
School: Table = Table(
    'school',
    Models,
    Column('id', String(10), primary_key=True),
    Column('name', String(150), nullable=False),
    Column('place_id', ForeignKey('place.id'), nullable=False),
    Column('longitude', Longitude),
    Column('latitude', Latitude),
    Column('wikidata_id', WikidataId),
    Column(EDIT_STAMP, EditStampType)
)


# Examination table representation one examination session or "Изпитна сесия".
# An examination session is described
# * with type of the session - 'nvo' or 'dzi'
# * with year - possible values 2024, 2023, etc
# * with grade_level
#   * for NVO possible values are 4, 7 and 10
#   * for DZI the value is always 12
# * max_possible_score - describes the max possible score, it could be 6
#   for DZI and 65 or 100 for NVO.

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
    Column('max_possible_score', Numeric),
    Column(EDIT_STAMP, EditStampType)
)


# Examination score table supplements the Examination table.
# In this table each record describes the result:
# * of given school - school_id
# * on given subject - this is the unique abbreviation of the subject, check
#   the documentation of SubjectItem class in db_manage.py
# * people - number of attended people on that subject from that school
# * score - the average score of the attendees
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
    Column(EDIT_STAMP, EditStampType)
)


# This table describes all possible Subjects and their different
# abbreviations.
# Check the documentation of SubjectItem class in db_manage.py
Subject: Table = Table(
    'subject',
    Models,

    Column('id', String(10), primary_key=True),
    Column('name', String(120)),
    Column('abbreviations', String(30)),
    Column(EDIT_STAMP, EditStampType)
)
