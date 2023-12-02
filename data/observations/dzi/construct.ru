BASE <https://schools.ontotext.com/data/resource/>
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX mapper: <http://www.ontotext.com/mapper/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX school: <https://schools.ontotext.com/data/resource/school/>
PREFIX qb: <http://purl.org/linked-data/cube#>
INSERT {
    GRAPH ?DataSet {
    ?URI_OK a qb:Observation ;
            qb:dataSet ?DataSet ;
            :school ?SCHOOL ;
 			?PROP ?VALUE ;
            :subject ?SUBJECT ;
  .
  }
} WHERE {
    #http://schools.ontotext.com:7333/repositories/ontorefine:2575173855452 - 2018
    #http://schools.ontotext.com:7333/repositories/ontorefine:2507564030891 - 2019
    #http://schools.ontotext.com:7333/repositories/ontorefine:2190454123408 - 2020
    #http://schools.ontotext.com:7333/repositories/ontorefine:2053655239041 - 2021
    #http://schools.ontotext.com:7333/repositories/ontorefine:2534582373267 - 2022
    #http://schools.ontotext.com:7333/repositories/ontorefine:1928644177398 - 2023
    SERVICE <http://schools.ontotext.com:7333/repositories/ontorefine:2575173855452> {
        BIND(<cube/dzi/2018> as ?DataSet)
        # Columns as variables:
        #   ?c_school_id, ?c_subject_code, ?c_prop, ?c_value
        # Metadata as variables:
        #   ?row_index, ?record_id

        BIND(IRI(mapper:encode_iri(school:, ?c_school_id)) as ?SCHOOL)
        BIND(IRI(mapper:encode_iri(:, ?c_prop)) as ?PROP)
        BIND(IF(?c_prop="quantity_people",xsd:integer,xsd:double) as ?DT)
        BIND(STRDT(?c_value,?DT) as ?VALUE)
        BIND(strlang(ucase(?c_subject_code),"bg") as ?SUBJECT_CODE)
        BIND(if(?VALUE > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?SCHOOL),str(?c_subject_code))))),?null) as ?URI_OK)
    }
	?SUBJECT skos:notation ?SUBJECT_CODE.
}