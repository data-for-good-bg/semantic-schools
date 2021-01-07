INSERT {
    GRAPH ?DataSet {
    ?URI_OK a qb:Observation ;
            qb:dataSet ?DataSet ;
            :place ?PLACE ;
            :subject ?SUBJECT ;
            :age ?AGE ;
            :years_working   ?YEARS_TOTAL ;
            :years_teaching  ?YEARS_TEACH ;
            :years_spec      ?YEARS_SPEC ;
            :quantity_people ?QUANTITY ;
   .
   }
}

WHERE {
    SERVICE <rdf-mapper:ontorefine:2428818903640> {
        # Columns as variables:
        #   ?c_Obl_Name, ?c_Age, ?c_Teach_All, ?c_pens, ?c_Total_years, ?c_Spec_years,
        #   ?c_Teach_years, ?c_subj_code, ?c_quantity

        bind(xsd:integer(?c_quantity) as ?QUANTITY)

        BIND(<cube/teachers_by_age_region/2020-09-15_F> as ?DataSet)

        BIND(uri(concat(str(subject:),?c_subj_code)) as ?SUBJECT)

        (?row_index "\"place/\"+cells[\"Obl Name\"].recon.match.id ") mapper:grel ?o_place_grel .
        BIND(IRI(mapper:encode_iri(?o_place_grel)) as ?PLACE)
        BIND(xsd:integer(?c_Age) as ?AGE)
        BIND(xsd:integer(?c_Total_years) as ?YEARS_TOTAL)
        BIND(xsd:integer(?c_Teach_years) as ?YEARS_TEACH)
        BIND(xsd:integer(?c_Spec_years) as ?YEARS_SPEC)

        BIND(if(xsd:integer(?c_quantity) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?SUBJECT),str(?PLACE),?c_Age,?c_Total_years,?c_Spec_years,?c_Teach_years)))),?null) as ?URI_OK)
    }
}