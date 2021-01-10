INSERT {
    GRAPH school:geo {
        ?SCHOOL :hasPoint ?POINT .
    	?POINT a sf:Point ; geo:asWKT ?coords ;
	}
} WHERE {
    service <https://query.wikidata.org/sparql> {
        ?wd wdt:P9034 ?id .
        optional {?wd wdt:P625 ?coords }
    }
    bind(uri(concat(str(school:),?id)) as ?SCHOOL)
    bind(uri(concat(str(school:),?id,"/point")) as ?POINT)
}
