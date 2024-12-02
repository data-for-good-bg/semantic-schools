import requests
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal

from .runtime import getLogger
from .db_actions import insert_region, insert_mun, insert_place
from .db import get_db_engine


logger = getLogger(__name__)

# https://www.wikidata.org/wiki/Wikidata:WikiProject_Bulgaria/Administrative_Entities


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
SELECT distinct ?region ?regionLabel ?coordinates ?areaId WHERE {

  ?region wdt:P31 wd:Q209824;
    wdt:P625 ?coordinates.
  OPTIONAL { ?region wdt:P982 ?areaId. }.

  SERVICE wikibase:label { bd:serviceParam wikibase:language "bg". }
}
order by ?regionLabel
'''

MUN_SPARQL = '''
SELECT distinct ?region ?mun ?munLabel ?coordinates ?areaId  WHERE {

  ?mun wdt:P31 wd:Q1906268;
       wdt:P131 ?region;
       wdt:P625 ?coordinates.

  OPTIONAL { ?mun wdt:P982 ?areaId. }.

  ?region wdt:P31 wd:Q209824.

  SERVICE wikibase:label { bd:serviceParam wikibase:language "bg". }
}
order by ?munLabel
'''

PLACE_SPARQL = '''
SELECT distinct ?place ?placeLabel ?munLabel ?mun ?coordinates ?areaId WHERE {{
  ?place wdt:P31 {0};
   wdt:P131 ?mun;
   wdt:P625 ?coordinates.

  OPTIONAL {{ ?place wdt:P982 ?areaId. }}.

  ?mun wdt:P31 wd:Q1906268;
       wdt:P131 ?region.

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "bg". }}
}}
order by ?munLabel ?placeLabel
'''

SCHOOL_QUERY = '''
SELECT distinct ?place ?placeLabel ?school ?schoolLabel ?bgSchoolIdLabel ?coordinates WHERE {
  ?school wdt:P31 wd:Q3914;
          wdt:P9034 ?bgSchoolId;
          wdt:P625 ?coordinates;
         wdt:P131 ?place.

  ?place wdt:P31 ?placeType.

  FILTER(?placeType in (wd:Q89487741, wd:Q15630849)).

  SERVICE wikibase:label { bd:serviceParam wikibase:language "bg". }
}
order by ?placeLabel ?schoolLabel
'''


# To use SPQRQL query endpoint we need to provide user-agent as it is
# documented here: https://foundation.wikimedia.org/wiki/Policy:User-Agent_policy
#
CONTACT_EMAIL = 'info+semantic-schools@data-for-good.bg'
USER_AGENT = f'User-Agent: semantic-schools/0.1 (https://data-for-good.bg/; {CONTACT_EMAIL}) semantic-schools/0.1'


def _extract_wikidata_via_requests():
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    query = PLACE_SPARQL.format(CITY_IN_BULGARIA)
    logger.info(query)

    data = requests.get(url, params={'query': query, 'format': 'json'}).text
    print(data)


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


def _extract_arae_id(wikidata_row: dict) -> str:
    if 'areaId' in wikidata_row and wikidata_row['areaId']:
        return f'https://musicbrainz.org/area/{wikidata_row["areaId"]}'
    else:
        return ''


def _import_regions(session: Session):
    regions = _extract_wikidata_via_sparql(REGION_SPARQL)
    for region in regions:
        area_id = _extract_arae_id(region)
        coordinates = _extract_coordinates(region['coordinates'])
        insert_region(session, region['region'], region['regionLabel'], area_id, *coordinates)


def _import_municipalities(session: Session):
    muns = _extract_wikidata_via_sparql(MUN_SPARQL)
    known_muns = set()
    for mun in muns:
        if mun['mun'] in known_muns:
            logger.verbose_info('skipping muncipliaty %s', mun)
            # some municiaplities has two relations for coordinates, so in the result
            # we get two rows for them. We work only with the first row here, the other
            # rows are ignored. I don't think there's a clear way to do this with SPARQL
            continue

        area_id = _extract_arae_id(mun)
        coordinates = _extract_coordinates(mun['coordinates'])

        insert_mun(session, mun['mun'], mun['region'], mun['munLabel'], area_id, *coordinates)
        known_muns.add(mun['mun'])


def _import_places(session: Session, place_type: str):
    places = _extract_wikidata_via_sparql(PLACE_SPARQL.format(place_type))
    known_place = set()
    for place in places:
        if place['place'] in known_place:
            logger.verbose_info('skipping place %s', place)
            # some places has two relations for coordinates, so in the result
            # we get two rows for them. We work only with the first row here, the other
            # rows are ignored. I don't think there's a clear way to do this with SPARQL
            continue

        area_id = _extract_arae_id(place)
        coordinates = _extract_coordinates(place['coordinates'])

        insert_place(session, place['place'], place['mun'],
                     place['placeLabel'], DISPLAY_PLACE_TYPE[place_type],
                     area_id, *coordinates)
        known_place.add(place['place'])


def extract_wikidata():

    db = get_db_engine()
    with Session(db) as session:
        # _import_regions(session)
        # _import_municipalities(session)
        _import_places(session, CITY_IN_BULGARIA)
        _import_places(session, VILLAGE_IN_BULGARIA)
        session.commit()