PREFIX school: <https://schools.ontotext.com/data/resource/school/>
PREFIX sf: <http://www.opengis.net/ont/sf#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX schema: <http://schema.org/>
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX place: <https://schools.ontotext.com/data/resource/place/>
INSERT {
    GRAPH school: {
        ?SCHOOL a :School ;
                :hasPoint ?POINT ;
                :wikidata_entity ?wd ;
                :link_wiki_bg ?bgwiki ;
                :link_website ?url ;
                :has_image ?img ;
                :place ?PLACE_ID ;

        .
        ?POINT a sf:Point ; geo:asWKT ?coords ;
    }
} WHERE {
    service <https://query.wikidata.org/sparql> {
        ?wd wdt:P9034 ?id ; wdt:P131 ?place .
        optional {?wd wdt:P625 ?coords }
        optional {?wd wdt:P18 ?img }
        optional {?wd wdt:P856 ?url }
        optional {?bgwiki schema:about ?wd ; schema:isPartOf <https://bg.wikipedia.org/> . }

    }
    BIND(strafter(str(?place),str(wd:)) as ?x_id)
    BIND(uri(concat(str(place:),?x_id)) as ?PLACE_ID)
    bind(uri(concat(str(school:),?id)) as ?SCHOOL)
    bind(uri(concat(str(school:),?id,"/point")) as ?POINT)
}