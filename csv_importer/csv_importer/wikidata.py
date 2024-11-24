import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from sqlalchemy.orm import Session

from .runtime import getLogger
from .db_actions import insert_region, insert_mun
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

REGION_SPARQL = '''
SELECT distinct ?region ?regionLabel WHERE {

  ?region wdt:P31 wd:Q209824.

  SERVICE wikibase:label { bd:serviceParam wikibase:language "bg". }
}
order by ?regionLabel
'''

MUN_SPARQL = '''
SELECT distinct ?region ?mun ?munLabel WHERE {

  ?mun wdt:P31 wd:Q1906268;
       wdt:P131 ?region.

  ?region wdt:P31 wd:Q209824.

  SERVICE wikibase:label { bd:serviceParam wikibase:language "bg". }
}
order by ?munLabel
'''

PLACE_SPARQL = '''
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT distinct ?region ?regionLabel ?mun ?munLabel ?place ?placeLabel ?coordinates WHERE {{
  ?place wdt:P31 {0};
   wdt:P131 ?mun;
   wdt:P625 ?coordinates.

  ?mun wdt:P31 wd:Q1906268;
       wdt:P131 ?region.

  ?region wdt:P31 wd:Q209824.

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "bg". }}
}}
order by ?regionLabel ?munLabel ?placeLabel
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


def _import_regions(session: Session):
    regions = _extract_wikidata_via_sparql(REGION_SPARQL)
    for region in regions:
        insert_region(session, region['region'], region['regionLabel'])


def _import_municipalities(session: Session):
    muns = _extract_wikidata_via_sparql(MUN_SPARQL)
    for mun in muns:
        insert_mun(session, mun['region'], mun['mun'], mun['munLabel'])


def extract_wikidata():

    db = get_db_engine()
    with Session(db) as session:
        # _import_regions(session)
        _import_municipalities(session)

        session.commit()