BASE <https://schools.ontotext.com/data/resource/>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
INSERT {
    GRAPH ?DataSet {
        ?URI_OK a qb:Observation ;
                :place ?place ;
                :grade_level ?grade ;
                :subject ?subj ;
                ?pred_score ?avg_score ;
                :date ?date ;
                :quantity_people ?sum_kids ;
                :score_type ?pred_score ;
        .
    }
} WHERE {
BIND(<cube/place_summary/data> as ?DataSet)
BIND(uri(concat(str(?DataSet),"/",md5(concat(str(?place),str(?date),str(?pred_score),str(?grade),str(?subj))))) as ?URI_OK)
    { select
        ?place ?date ?pred_score ?grade ?subj (sum(?num_kids) as ?sum_kids) (sum(?points) as ?sum_points) (?sum_points/?sum_kids as ?avg_score)
        where {
            ?pred_score rdfs:subPropertyOf :eval_score.
            ?obs a qb:Observation ;
              :school ?school ;
              :grade_level ?grade ;
              :subject ?subj ;
              ?pred_score ?score ;
              :date ?date ;
              :quantity_people ?num_kids ;
              .
            bind(?num_kids*?score as ?points)
            ?school :place/geo:sfWithin* ?place .
    } group by ?place ?date ?pred_score ?grade ?subj }
}