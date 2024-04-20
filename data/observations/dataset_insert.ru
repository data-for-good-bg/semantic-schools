## ugly hack INSERT PATTERN FOR dataset.ttl

BASE <https://schools.ontotext.com/data/resource/>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
insert data {
    graph <cube/place_summary> {
        <cube/place_summary> a qb:DSD ;
            qb:component
                [qb:dimension  :date ],
                [qb:dimension  :grade_level ],
                [qb:dimension  :place ],
                [qb:dimension  :subject ],
                [qb:measure    :eval_score ],
                [qb:measure    :quantity_people  ],
                [qb:measure    :rank_percentile  ],
                [qb:attribute  :score_type  ],
        .

        <cube/place_summary/data> a qb:DataSet ;
            rdfs:label "Aggregate evaluation scores by place" ;
            qb:structure <cube/place_summary> ;
        .
    }
}