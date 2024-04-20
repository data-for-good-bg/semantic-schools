BASE <https://schools.ontotext.com/data/resource/>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX subject: <https://schools.ontotext.com/data/resource/subject/>
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX mapper: <http://www.ontotext.com/mapper/>
PREFIX school: <https://schools.ontotext.com/data/resource/school/>

#Project http://edu.ontotext.com/orefine/project?project=2230913364235

INSERT {
    GRAPH ?DataSet {
    ?URI_OK a qb:Observation ;
            qb:dataSet ?DataSet ;
            :subject ?SUBJECT ;
            :quantity_people ?QUANTITY ;
            :school ?SCHOOL ;
   .
  }
}
WHERE {
    SERVICE <rdf-mapper:ontorefine:2230913364235> {
        # Columns as variables:
        #   ?c_school_id, ?c_quantity, ?c_subject

        bind(xsd:integer(?c_quantity) as ?QUANTITY)

        BIND(<cube/teachers_school_subject/2020-09-15> as ?DataSet)

        BIND(uri(concat(str(subject:),?c_subject)) as ?SUBJECT)
        BIND(uri(concat(str(school:),?c_school_id)) as ?SCHOOL)

        BIND(if(xsd:integer(?c_quantity) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?SUBJECT),str(?SCHOOL))))),?null) as ?URI_OK)
    }
}