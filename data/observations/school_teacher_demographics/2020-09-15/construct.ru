INSERT {
    GRAPH ?DataSet {
    ?URI_OK a qb:Observation ;
            qb:dataSet ?DataSet ;
            :school ?SCHOOL ;
            :occupation ?OCC ;
            :age_bracket ?AGE_BRACKET ;
            :quantity_people ?QUANTITY ;
  .
   }
}
WHERE {
    SERVICE <rdf-mapper:ontorefine:2536231271386> {
        # Columns as variables:
        #   ?c_school_id, ?c_age_0-25, ?c_occ_id

        BIND(<cube/school_teacher_demographics/2020-09-15> as ?DataSet)

        BIND(xsd:integer(?c_quantity) as ?QUANTITY)
        BIND(uri(concat(str(school:),?c_school_id)) as ?SCHOOL)
        BIND(uri(concat(str(age_bracket:),?c_age_bracket)) as ?AGE_BRACKET)
        BIND(uri(concat(str(occupation:),?c_occ_id)) as ?OCC)

        BIND(if(xsd:integer(?c_quantity) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?SCHOOL),str(?AGE_BRACKET),str(?OCC))))),?null) as ?URI_OK)
    }
}