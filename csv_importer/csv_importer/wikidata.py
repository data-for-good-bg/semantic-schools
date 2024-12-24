import os
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from sqlalchemy import Table
from sqlalchemy.orm import Session
from typing import Optional
from collections import OrderedDict, defaultdict
from cache_decorator import Cache

from .runtime import getLogger
from .db_actions import insert_or_update_object, ImportAction
from .db import get_db_engine
from .db_models import Region, Municipality, Place, School, EDIT_STAMP


logger = getLogger(__name__)


SUPPORTED_IMPORT_WIKIDATA_TYPES = ('regions', 'muns', 'places', 'schools')


def _ensure_cache_dir():
    value = None
    for name in ['HOME', 'TMP', 'TMPDIR']:
        value = os.environ.get(name)
        if value:
            break
    else:
        value = '/tmp'

    cache_dir = os.path.join(value, '.cache', 'data-for-good', 'semantic_schools', 'wikidata')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)

    return cache_dir


_CACHE_DIR = _ensure_cache_dir()


# To use wikidata query endpoint we need to provide user-agent as it is
# documented here: https://foundation.wikimedia.org/wiki/Policy:User-Agent_policy
#
# Additionally the results from queries made against wikidata are cached on
# the file system for a day.
CONTACT_EMAIL = 'info+semantic-schools@data-for-good.bg'
USER_AGENT = f'User-Agent: semantic-schools/0.1 (https://data-for-good.bg/; {CONTACT_EMAIL}) semantic-schools/0.1'


# NB: Look here for details around wikidata entries for Bulgaria
# https://www.wikidata.org/wiki/Wikidata:WikiProject_Bulgaria/Administrative_Entities

# NB: Use this query to explore all properties for particular subject.
#
# SELECT ?property ?propertyLabel ?value ?valueLabel
# WHERE {
#   wd:Q12294213 ?prop ?value .
#   ?property wikibase:directClaim ?prop .  # Get the direct property
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }  # Fetch labels
# }
# ORDER BY ?property


# NB:
# The SPARQL queries below are processed by the function _import_sparql_result.
# Its documentation explains the convention about the naming of the columns
# in the SPARQL queries.

REGION_SPARQL = '''
SELECT distinct ?id ?name ?coordinates ?area_id WHERE {

  ?region wdt:P31 wd:Q209824;
    wdt:P625 ?coordinates.
  OPTIONAL { ?region wdt:P982 ?area_id. }.

  BIND(?region AS ?id).

  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "bg".
    ?region rdfs:label ?name.
  }
}
order by ?name
'''

MUN_SPARQL = '''
SELECT distinct ?region_id ?id ?name ?coordinates ?area_id  WHERE {

  ?mun wdt:P31 wd:Q1906268;
       wdt:P131 ?region;
       wdt:P625 ?coordinates.

  OPTIONAL { ?mun wdt:P982 ?area_id. }.

  ?region wdt:P31 wd:Q209824.

  BIND(?mun as ?id).
  BIND(?region as ?region_id).

  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "bg".
    ?mun rdfs:label ?name.
    ?region rdfs:label ?regionLabel.
  }
}
order by ?regionLabel ?munLabel
'''


# These constants are used to build SPARQL query for extracting cities and
# villages via the PLACE_SPARQL query.

CITY_IN_BULGARIA = 'wd:Q89487741'
VILLAGE_IN_BULGARIA = 'wd:Q15630849'

DISPLAY_PLACE_TYPE = {
    CITY_IN_BULGARIA: 'град',
    VILLAGE_IN_BULGARIA: 'село'
}


PLACE_SPARQL = '''
SELECT distinct ?municipality_id ?id ?name ?coordinates ?area_id WHERE {{
  ?place wdt:P31 {0};
   wdt:P131 ?mun;
   wdt:P625 ?coordinates.

  OPTIONAL {{ ?place wdt:P982 ?area_id. }}.

  ?mun wdt:P31 wd:Q1906268;
       wdt:P131 ?region.

  BIND(?place as ?id).
  BIND(?mun as ?municipality_id).


  SERVICE wikibase:label {{
    bd:serviceParam wikibase:language "bg".
    ?place rdfs:label ?name.
    ?mun rdfs:label ?munLabel.

  }}
}}
order by ?munLabel ?name
'''

# NB: This query is similar to the above one, but extracts cities or villages
#     through an additional relation, district.
#     This query was used to because gr. Bankya does not belong directly to
#     municipality and some schools failed to import.
#     It turned out that gr. Bankya is the only exception, so it is handled
#     specially, see below.
#
# DISTRICT_PLACE_SPARQL = '''
# SELECT distinct ?municipality_id ?id ?name ?coordinates ?area_id WHERE {{
#   ?place wdt:P31 {0};
#    wdt:P131 ?district;
#    wdt:P625 ?coordinates.

#   OPTIONAL {{ ?place wdt:P982 ?area_id. }}.

#   ?district wdt:P31 wd:Q7553685;
#             wdt:P131 ?mun.

#   ?mun wdt:P31 wd:Q1906268;
#        wdt:P131 ?region.

#   BIND(?place as ?id).
#   BIND(?mun as ?municipality_id).


#   SERVICE wikibase:label {{
#     bd:serviceParam wikibase:language "bg".
#     ?place rdfs:label ?name.
#     ?mun rdfs:label ?munLabel.

#   }}
# }}
# order by ?munLabel ?name
# '''


SCHOOL_QUERY = '''
SELECT distinct ?place_id ?id ?name ?wikidata_id ?coordinates WHERE {
  ?school wdt:P31 wd:Q3914;
          wdt:P9034 ?bgSchoolId;
         wdt:P131 ?place.

  OPTIONAL { ?school wdt:P625 ?coordinates. }

  ?place wdt:P31 ?placeType.

  BIND(?place as ?place_id).
  BIND(?school as ?wikidata_id).

  FILTER(?placeType in (wd:Q89487741, wd:Q15630849)).

  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "bg".
    ?school rdfs:label ?name.
    ?place rdfs:label ?placeLabel.
    ?bgSchoolId rdfs:label ?id.
  }
}
order by ?placeLabel ?id ?name
'''


def _flatten_sparql_json_result(sparql_json_result: dict) -> list[dict]:
    result = []
    for item in sparql_json_result['results']['bindings']:
        flatten_item = {
            binding : binding_value['value']
            for binding, binding_value in item.items()
        }
        result.append(flatten_item)

    return result


@Cache(
    cache_path='/'.join(['{cache_dir}','{function_name}-{_hash}.json']),
    validity_duration='1d',
    cache_dir=_CACHE_DIR
)
def _extract_wikidata_via_sparql(query: str):
    logger.info(query)

    sparql = SPARQLWrapper('https://query.wikidata.org/sparql', USER_AGENT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    data = sparql.query().convert()
    flatten = _flatten_sparql_json_result(data)

    return flatten


def _extract_coordinates(point: str) -> tuple[Optional[str], Optional[str]]:
    """
    Pareses coordinates from string like `Point(24.666666666 43.416666666)`
    to two string values representing the coordinates.
    """
    # Point(24.666666666 43.416666666)
    # Longitude, Latitude
    coordinates_re = r'Point\(([0-9]+\.[0-9]+) ([0-9]+\.[0-9]+)\)'
    m = re.match(coordinates_re, point)
    if m:
        g = list(m.groups())
        return (g[0], g[1])
    else:
        return (None, None)


def _update_coordinates(wikidata_item: dict):
    """
    If the dictionary contains `coordinates` element it will replace it
    with `longitude` and `latitude` elements parsed by _extract_coordinates
    function.
    """
    if 'coordinates' in wikidata_item:
        longitude = None
        latitude = None
        if wikidata_item['coordinates']:
            longitude, latitude = _extract_coordinates(wikidata_item['coordinates'])

        wikidata_item.pop('coordinates')
        wikidata_item['longitude'] = longitude
        wikidata_item['latitude'] = latitude


def _update_area_id(wikidata_item: dict):
    if 'area_id' in wikidata_item:
        if wikidata_item['area_id']:
            full_area_id = f'https://musicbrainz.org/area/{wikidata_item["area_id"]}'
            wikidata_item['area_id'] = full_area_id


def _import_sparql_result(session: Session, sparql: str, model: Table, constant_values: Optional[dict] = None) -> dict[ImportAction, int]:
    """
    This function runs a SPARQL query and for each result item it will
    insert or update record in the table specified via the model param.

    The following conventions are implemented here:
    * The target table should have column named `id`
    * The function will use the columns from the SPARQL query which names
      match a column from the target table.
      So for the Region table with columns (id, name, area_id) the SPARQL
      query should have the same set of columns.
    * There is special support for:
      * geographical coordinates which represent latitude and longitude:
        The column extracted as property of `wdt:P625` type should be named
        `coordinates`. The function will parse its value `Point(...., ......)`
        and replace it with two other columns - `longitude` and `latitude`.
        The target table should have columns named like this.
      * area_id - if SPARQL query contains column `area_id` and the value is not
        empty, then the value will be converted to URI to musicbrainz.org


    Parameters:
      session: SQLAlchemy session which will execute the DB operations
      sparql: The SPARQL query
      mode: The SQLAlchemy Table object representing the target table
      constant_values: An optional dictionary with values that should be
      added to all records.

    Returns:
      A dictionary providing information for the number of performed operations
      (insert, update, error, already-existing),
    """
    counts = defaultdict(int)
    if constant_values is None:
        constant_values = {}

    sparql_result = _extract_wikidata_via_sparql(sparql)
    known = set()
    for result_item in sparql_result:
        if result_item['id'] in known:
            # All wikidata queries may return multiple records with the same ID
            # This might be caused by different reasons. In some cases
            # a region/place/municipality has multiple instances of Coordinates
            # property. In other cases multiple schools with the same bg_school_id.
            #
            # In all these cases what we do is to use the first record from
            # the query result and skip the other.
            logger.warning('Skipping %s %s', model.name, result_item)
            counts[ImportAction.Skipped] += 1
            continue

        known.add(result_item['id'])

        _update_area_id(result_item)
        _update_coordinates(result_item)

        key_values = []
        for col in model.columns:
            if col.name == EDIT_STAMP:
                continue

            value = result_item[col.name] \
                if col.name in result_item \
                else None
            if value is None:
                value = constant_values[col.name] \
                    if col.name in constant_values \
                    else None

            key_values.append( (col, value) )

        od = OrderedDict(key_values)

        action = insert_or_update_object(session, model, model.columns['id'], od)
        counts[action] += 1

    return counts


def import_from_wikidata(to_import = SUPPORTED_IMPORT_WIKIDATA_TYPES):
    """
    Imports information for regions, municipalities, places (cities and villages)
    and schools from wikidata into the relational DB.
    """

    counters = dict()

    db = get_db_engine()
    with Session(db) as session:
        if 'regions' in to_import:
            counters[Region.name] = _import_sparql_result(session, REGION_SPARQL, Region)

        if 'muns' in to_import:
            counters[Municipality.name] = _import_sparql_result(session, MUN_SPARQL, Municipality)

        if 'places' in to_import:
            for place_type in [CITY_IN_BULGARIA, VILLAGE_IN_BULGARIA]:
                counters[Place.name+'-' + DISPLAY_PLACE_TYPE[place_type]] = _import_sparql_result(session, PLACE_SPARQL.format(place_type), Place, {'type': DISPLAY_PLACE_TYPE[place_type]})

            # # Bankya is handled specially, because it is the only city in Bulgaria
            # # which does not belong (P:131) to a municipality of Bulgaria. So
            # # because of this it is not imported as all other cities and viligies
            insert_or_update_object(session, Place, Place.c.id, OrderedDict([
                (Place.c.id, 'http://www.wikidata.org/entity/Q806817'),
                (Place.c.name, 'Банкя'),
                (Place.c.municipality_id, 'http://www.wikidata.org/entity/Q4442915'),
                (Place.c.type, 'град'),
                (Place.c.area_id, None),
                (Place.c.longitude, '23.147239'),
                (Place.c.latitude, '42.706945')
            ]))

        if 'schools' in to_import:
            counters[School.name] = _import_sparql_result(session, SCHOOL_QUERY, School)

        session.commit()

    logger.info('Summary of operations per model')

    for model_name, counts in counters.items():
        cnt_items = [f'{op_type}: {op_cnt}' for op_type, op_cnt in counts.items()]
        cnts_str = ', '.join(cnt_items)
        msg = f'Operation counts for "{model_name}" --- {cnts_str}'
        logger.info(msg)
