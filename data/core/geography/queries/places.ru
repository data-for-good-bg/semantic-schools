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
        ?PLACE_ID a schema:City ;
                  rdfs:label ?label, ?label_bg ;
                  :hasPoint ?PLACE_ID_POINT ;
                  geo:sfWithin ?PARENT ;
                  .
        ?PLACE_ID_POINT a sf:Point ;
                        geo:asWKT ?COORDS ;
                        .
    }
}
WHERE {
    service <https://query.wikidata.org/sparql> {
        {
            select ?x (sample(?coords) as ?COORDS) {
                ?x wdt:P31/wdt:P279 wd:Q95993392 .
                optional {
                    ?x wdt:P625 ?coords
                }
            } group by ?x
        }
        ?x wdt:P131 ?parent .
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