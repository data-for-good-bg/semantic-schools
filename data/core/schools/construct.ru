INSERT {
    GRAPH school: {
    ?s1 a schema:School ;
        schema:name ?o_name ;
        :place ?o_sfWithin .
    }
} WHERE {
    SERVICE <rdf-mapper:ontorefine:2058181869306> {
        # Columns as variables:
        #   ?c_obl, ?c_mun, ?c_city, ?c_city_id, ?c_school_id, ?c_label_bg
        # Metadata as variables:
        #   ?row_index, ?record_id
        BIND(IRI(mapper:encode_iri(school:, ?c_school_id)) as ?s1)
        BIND(STRLANG(?c_label_bg, "bg") as ?o_name)
        BIND(IRI(mapper:encode_iri(place:, ?c_city_id)) as ?o_sfWithin)
    }
}