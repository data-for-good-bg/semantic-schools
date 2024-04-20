### Generiic percentile calculating query
### !!! Assumes qb:Dataset uri is same as dataset context
### Finish when gdb 90sec. timeout is removed

PREFIX subject: <https://schools.ontotext.com/data/resource/subject/>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#INSERT {
#    GRAPH ?G {
#    ?o1 :rank_percentile ?PERC .
#    }
#} WHERE
SELECT *
{
    SELECT ?o1 ?ds (sum(?lower) as ?LOWER) (sum(?higher) as ?HIGHER) ((?LOWER/(?LOWER+?HIGHER))*100 as ?PERC) {
        {
            SELECT * where {
                ?o1 :eval_score ?grade ;
                    qb:dataSet ?ds ;
                    ?dim ?val ;
                .
                ?ds qb:structure/qb:component/qb:dimension ?dim .
            }
        }
        ?o2 :eval_score ?grade2 ;
            qb:dataSet ?ds ;
            ?dim ?val ;
        .
        filter(!sameterm(?o2,?o1))
        bind(if(?grade>=?grade2,1,0) as ?lower)
        bind(if(?grade<?grade2,1,0) as ?higher)
    } group by ?o1 ?ds
}