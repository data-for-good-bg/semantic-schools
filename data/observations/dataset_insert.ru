## ugly hack INSERT PATTERN FOR dataset.ttl

BASE <http://edu.ontotext.com/resource/>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX : <http://edu.ontotext.com/resource/ontology/>
insert data {
    graph <cube/dzi/2021> {
        <cube/dzi/2021> a qb:DataSet ;
        rdfs:label "DZI - 2021" ;
        rdfs:comment "Резултати от държавен зрелсотен изпит - 2021 "@bg ;
        qb:structure <cube/dzi> ;
        :date "2020-05-19"^^xsd:date ;
	.
    }
}