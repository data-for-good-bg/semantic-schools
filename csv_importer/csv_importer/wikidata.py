import re
from SPARQLWrapper import SPARQLWrapper, JSON
from sqlalchemy import Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional
from collections import OrderedDict

from .runtime import getLogger
from .db_actions import insert_or_update_object
from .db import get_db_engine
from .models import Region, Municipality, Place, School


logger = getLogger(__name__)

# NB: Look here for details around wikidata entries for Bulgaria
# https://www.wikidata.org/wiki/Wikidata:WikiProject_Bulgaria/Administrative_Entities

# NB: Use this query to explore all relations for particular subject
#
# SELECT ?property ?propertyLabel ?value ?valueLabel
# WHERE {
#   wd:Q12294213 ?prop ?value .
#   ?property wikibase:directClaim ?prop .  # Get the direct property
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }  # Fetch labels
# }
# ORDER BY ?property

CITY_IN_BULGARIA = 'wd:Q89487741'
VILLAGE_IN_BULGARIA = 'wd:Q15630849'

DISPLAY_PLACE_TYPE = {
    CITY_IN_BULGARIA: 'град',
    VILLAGE_IN_BULGARIA: 'село'
}

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

PLACE_SPARQL = '''
SELECT distinct ?municipality_id ?id ?name ?coordinates ?area_od WHERE {{
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

SCHOOL_QUERY = '''
SELECT distinct ?place_id ?id ?name ?wikidata_id ?coordinates WHERE {
  ?school wdt:P31 wd:Q3914;
          wdt:P9034 ?bgSchoolId;
          wdt:P625 ?coordinates;
         wdt:P131 ?place.

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


# To use SPQRQL query endpoint we need to provide user-agent as it is
# documented here: https://foundation.wikimedia.org/wiki/Policy:User-Agent_policy
#
CONTACT_EMAIL = 'info+semantic-schools@data-for-good.bg'
USER_AGENT = f'User-Agent: semantic-schools/0.1 (https://data-for-good.bg/; {CONTACT_EMAIL}) semantic-schools/0.1'


def _flatten_sparql_json_result(sparql_json_result: dict) -> list[dict]:
    result = []
    for item in sparql_json_result['results']['bindings']:
        flatten_item = {
            binding : binding_value['value']
            for binding, binding_value in item.items()
        }
        result.append(flatten_item)

    return result


def _extract_wikidata_via_sparql(query: str):
    # query = PLACE_SPARQL.format(CITY_IN_BULGARIA)
    # query = PLACE_SPARQL.format(VILLAGE_IN_BULGARIA)
    # query = SCHOOL_QUERY
    logger.info(query)

    sparql = SPARQLWrapper('https://query.wikidata.org/sparql', USER_AGENT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    data = sparql.query().convert()
    flatten = _flatten_sparql_json_result(data)

    return flatten


def _extract_coordinates(point: str) -> tuple[Optional[str], Optional[str]]:
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


def _import_sparql_result(session: Session, sparql: str, model: Table, constant_values: Optional[dict] = None):
    if constant_values is None:
        constant_values = {}

    sparql_result = _extract_wikidata_via_sparql(sparql)
    known = set()
    for result_item in sparql_result:
        if result_item['id'] in known:
            # TODO: explain why we skip objects
            logger.verbose_info('Skipping %s %s', model.name, result_item)
            continue

        known.add(result_item['id'])

        _update_area_id(result_item)
        _update_coordinates(result_item)

        key_values = []
        for col in model.columns:
            value = result_item[col.name] \
                if col.name in result_item \
                else None
            if value is None:
                value = constant_values[col.name] \
                    if col.name in constant_values \
                    else None

            key_values.append( (col, value) )

        od = OrderedDict(key_values)

        try:
            insert_or_update_object(session, model, model.columns['id'], od)
            session.commit()
        except IntegrityError as e:
            values_tuple = tuple(od.values())
            logger.verbose_info('Failed processing %s because of %s', values_tuple, e)
            session.rollback()


def extract_wikidata():

    db = get_db_engine()
    with Session(db) as session:
        # _import_sparql_result(session, REGION_SPARQL, Region)
        # _import_sparql_result(session, MUN_SPARQL, Municipality)
        # for place_type in [CITY_IN_BULGARIA, VILLAGE_IN_BULGARIA]:
        #     _import_sparql_result(session, PLACE_SPARQL.format(place_type), Place, {'type': DISPLAY_PLACE_TYPE[place_type]})

        _import_sparql_result(session, SCHOOL_QUERY, School)

        session.commit()