BASE <http://example/base/>
PREFIX mapper: <http://www.ontotext.com/mapper/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX sf: <http://www.opengis.net/ont/sf#>
PREFIX : <https://schools.ontotext.com/resource/ontology/>
PREFIX place: <https://schools.ontotext.com/resource/place/>

INSERT {
    GRAPH place:shapes {
        ?s1 a sf:Polygon ;
            geo:asWKT ?o_asWKT .
        ?s2 :hasShape ?o_hasShape .
    }
} WHERE {
    SERVICE <rdf-mapper:ontorefine:2387195443838> {
        # Columns as variables:
        #   ?c_s, ?c_shape_uri, ?c_osm, ?c_polygon, ?c_gen_url, ?c_gen_action
        # Metadata as variables:
        #   ?row_index, ?record_id
        BIND(IRI(?c_shape_uri) as ?s1)
        BIND(STRDT(?c_polygon, geo:wktLiteral) as ?o_asWKT)
        BIND(IRI(?c_s) as ?s2)
        BIND(IRI(?c_shape_uri) as ?o_hasShape)
    }
}