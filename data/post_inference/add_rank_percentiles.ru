INSERT {
    GRAPH ?G {
    ?o1 :rank_percentile ?PERC .
    }
} WHERE
#SELECT *
{
    SELECT ?o1 ?G (sum(?lower) as ?LOWER) (sum(?higher) as ?HIGHER) ((?LOWER/(?LOWER+?HIGHER))*100 as ?PERC) {
        {
            SELECT * where {
                GRAPH ?G {
                    #bind(subject:nmb_35 as ?subj)
                    ?o1 :eval_score ?grade ;
                        :school ?school ;
                        :subject ?subj ;
                        :quantity_people ?num_students ;
                        :date ?date .
                }
            }
        }
        ?o2 :eval_score ?grade2 ;
            :school ?school2 ;
            :subject ?subj ;
            :date ?date .
        filter(!sameterm(?o2,?o1))
        bind(if(?grade>=?grade2,1,0) as ?lower)
        bind(if(?grade<?grade2,1,0) as ?higher)
    } group by ?o1 ?G
}