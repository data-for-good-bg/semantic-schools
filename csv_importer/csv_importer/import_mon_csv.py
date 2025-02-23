import pandas as pd

from collections import OrderedDict, defaultdict

from sqlalchemy.orm import Session

from .runtime import getLogger
from .db import get_db_engine
from .db_actions import insert_or_update_object
from .db_models import SchoolType


logger = getLogger(__name__)


# Mapping of Bulgarian column names to English
COLUMN_MAP = {
    'код по неиспуо': 'school_id',
    'пълно наименование на институция': 'name',
    'вид на институция': 'institution_type',
    'детайлен вид на институция': 'institution_type_detailed',
    'вид на институцията според финнсирането': 'funding_type',
    'финансира се от': 'funded_by',
    'наименование на адрес на осъществяване на дейността': 'activity_address',
    'тип на сградата': 'building_type',
    'код от кадастъра': 'cadastre_code',
    'географски координати (ширина)': 'latitude',
    'географски координати (дължина)': 'longitude',
    'област': 'region',
    'община': 'municipality',
    'населено място': 'place',
    'адрес': 'address'
}


def _import_school_type(session: Session, data: pd.DataFrame) -> None:
    counts = defaultdict(int)
    for _, row in data.iterrows():
        result = insert_or_update_object(
            session,
            SchoolType,
            id_col=[SchoolType.c.name, SchoolType.c.details],
            values=OrderedDict([
                (SchoolType.c.name, row['institution_type']),
                (SchoolType.c.details, row['institution_type_detailed'])
            ])
        )
        counts[result] += 1

    logger.info('Imported school types: %s', counts)


def import_mon_csv(csv_file: str) -> None:
    """
    Imports a MON CSV file.
    """

    data = pd.read_csv(csv_file)
    data.columns = data.columns.str.lower()
    data = data.rename(columns=COLUMN_MAP)

    # Trim whitespace from all string columns
    for column in data.select_dtypes(include=['object']).columns:
        data[column] = data[column].str.strip()

    # Filter out kindergartens
    initial_count = len(data)
    data = data[data['institution_type'] != 'детска градина']
    logger.verbose_info(f'Filtered out {initial_count - len(data)} kindergarten entries')

    # Extract unique institution types
    type_columns = ['institution_type', 'institution_type_detailed']
    unique_types = data[type_columns].drop_duplicates().copy()
    logger.verbose_info(f'Found {len(unique_types)} unique institution types')

    db = get_db_engine()
    with Session(db) as session:
        _import_school_type(session, unique_types)
        session.commit()
