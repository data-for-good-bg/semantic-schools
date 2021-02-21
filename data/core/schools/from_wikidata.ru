INSERT {
    GRAPH school:geo {
        ?SCHOOL :hasPoint ?POINT ;
        		:wikidata_entity ?wd ;
        		:link_wiki_bg ?bgwiki ;
        		:link_website ?url ;
        		:has_image ?img ;

        .
    	?POINT a sf:Point ; geo:asWKT ?coords ;
	}
} WHERE {
    service <https://query.wikidata.org/sparql> {
        ?wd wdt:P9034 ?id .
        optional {?wd wdt:P625 ?coords }
        optional {?wd wdt:P18 ?img }
        optional {?wd wdt:P856 ?url }
        optional {?bgwiki schema:about ?wd ; schema:isPartOf <https://bg.wikipedia.org/> . }

    }
    bind(uri(concat(str(school:),?id)) as ?SCHOOL)
    bind(uri(concat(str(school:),?id,"/point")) as ?POINT)
}