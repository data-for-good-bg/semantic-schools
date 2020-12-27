PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX place: <http://edu.ontotext.com/resource/place/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX schema: <http://schema.org/>
PREFIX : <http://edu.ontotext.com/resource/ontology/>
PREFIX sf: <http://www.opengis.net/ont/sf#>
INSERT {
    GRAPH place: {
        ?PLACE_ID a ?myt ;
                  rdfs:label ?label, ?label_bg ;
                  :hasPoint ?PLACE_ID_POINT ;
                  geo:sfWithin ?PARENT ;
                  :osmID ?osm_id ;
                  .
        ?PLACE_ID_POINT a sf:Point ;
                        geo:asWKT ?COORDS ;
                        .
    }
}
WHERE {
    VALUES (?wdt ?myt) {
        (wd:Q1906268 :Municipality)
        (wd:Q209824 :Region)
        (wd:Q7553685 :District)
    }
    service <https://query.wikidata.org/sparql> {
        ?x wdt:P31 ?wdt ;
           wdt:P131 ?parent .
        optional{
            ?x wdt:P625 ?COORDS
        }
        optional{
            ?x wdt:P402 ?osm_id
        }
        SERVICE wikibase:label {
            bd:serviceParam wikibase:language "en".
            ?x rdfs:label ?label .
        }
        SERVICE wikibase:label {
            bd:serviceParam wikibase:language "bg".
            ?x rdfs:label ?label_bg .
        }
    }
    BIND(strafter(str(?x),str(wd:)) as ?x_id)
    BIND(strafter(str(?parent),str(wd:)) as ?parent_id)
    BIND(uri(concat(str(place:),?x_id)) as ?PLACE_ID)
    BIND(uri(concat(str(place:),?x_id,"/point")) as ?PLACE_ID_POINT)
    BIND(uri(concat(str(place:),?parent_id)) as ?PARENT)
}