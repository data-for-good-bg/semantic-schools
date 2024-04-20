PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX ethnic_group: <https://schools.ontotext.com/data/resource/ethnic_group/>
PREFIX mapper: <http://www.ontotext.com/mapper/>
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX place: <https://schools.ontotext.com/data/resource/place/>
BASE <https://schools.ontotext.com/data/resource/>
INSERT {
    GRAPH ?DataSet {
    ?URI_BG_OK a qb:Observation ;
               qb:dataSet ?DataSet ;
               :place ?PLACE ;
               :ethnic_group ethnic_group:bg ;
               :quantity_people ?BG ;
               .
    ?URI_TR_OK a qb:Observation ;
               qb:dataSet ?DataSet ;
               :place ?PLACE ;
               :ethnic_group ethnic_group:tr ;
               :quantity_people ?TR ;
               .
    ?URI_ROMA_OK a qb:Observation ;
                 qb:dataSet ?DataSet ;
                 :place ?PLACE ;
                 :ethnic_group ethnic_group:roma ;
                 :quantity_people ?ROMA ;
                 .
    ?URI_OTH_OK a qb:Observation ;
                qb:dataSet ?DataSet ;
                :place ?PLACE ;
                :ethnic_group ethnic_group:oth ;
                :quantity_people ?OTH ;
                .
    ?URI_DNI_OK a qb:Observation ;
                qb:dataSet ?DataSet ;
                :place ?PLACE ;
                :ethnic_group ethnic_group:dni ;
                :quantity_people ?DNI ;
                .
    }
}
WHERE {
    SERVICE <rdf-mapper:ontorefine:2584892624632> {
        bind(xsd:integer(?c_bg) as ?BG)
        bind(xsd:integer(?c_tr) as ?TR)
        bind(xsd:integer(?c_roma) as ?ROMA)
        bind(xsd:integer(?c_oth) as ?OTH)
        bind(xsd:integer(?c_dni) as ?DNI)
        BIND(<cube/nsi_ethnicity/2011> as ?DataSet)
        BIND(uri(concat(str(place:),?c_wd_id)) as ?PLACE)
        BIND(if(xsd:integer(?BG) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?PLACE),"bg")))),?null) as ?URI_BG_OK)
        BIND(if(xsd:integer(?TR) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?PLACE),"tr")))),?null) as ?URI_TR_OK)
        BIND(if(xsd:integer(?ROMA) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?PLACE),"roma")))),?null) as ?URI_ROMA_OK)
        BIND(if(xsd:integer(?OTH) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?PLACE),"oth")))),?null) as ?URI_OTH_OK)
        BIND(if(xsd:integer(?DNI) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?PLACE),"dni")))),?null) as ?URI_DNI_OK)
    }
}