#http://edu.ontotext.com/orefine/project?project=1762175864737

BASE <http://edu.ontotext.com/resource/>
PREFIX mapper: <http://www.ontotext.com/mapper/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX school: <http://edu.ontotext.com/resource/school/>
PREFIX : <http://edu.ontotext.com/resource/ontology/>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX place: <http://edu.ontotext.com/resource/place/>
PREFIX week_number: <http://edu.ontotext.com/resource/week_number/>
#http://edu.ontotext.com/orefine/project?project=1655428113622
INSERT {
    GRAPH ?DataSet {
    ?URI_OK a qb:Observation ;
            qb:dataSet ?DataSet ;
            :place ?PLACE ;
 			:week_number ?WEEK_NUMBER ;
            :year ?YEAR ;
            :quantity_people ?DEATHS ;
  .
  }
 }
WHERE {
    SERVICE <rdf-mapper:ontorefine:1655428113622> {
        BIND(<cube/nsi_deaths/data> as ?DataSet)
        # Columns as variables:
        #   ?c_region_id, ?c_week ?c_year, ?c_deaths
        BIND(uri(concat(str(place:),?c_region_id)) as ?PLACE)
        BIND(uri(concat(str(week_number:),str(?c_week))) as ?WEEK_NUMBER)
        BIND(strdt(?c_year,xsd:gYear) as ?YEAR)
        BIND(xsd:integer(?c_deaths) as ?DEATHS )
        BIND(if(xsd:integer(?DEATHS) > 0,uri(concat(str(?DataSet),"/",md5(concat(str(?YEAR),str(?PLACE),str(?WEEK_NUMBER))))),?null) as ?URI_OK)
    }
}