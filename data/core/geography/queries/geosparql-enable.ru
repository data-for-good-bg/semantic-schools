#Create lat/lon nodes from WKT

PREFIX sf: <http://www.opengis.net/ont/sf#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX geo-pos: <http://www.w3.org/2003/01/geo/wgs84_pos#>
clear silent graph <https://schools.ontotext.com/resource/graph/geo-coord-pairs> ;
insert {
    graph <https://schools.ontotext.com/resource/graph/geo-coord-pairs> {
    ?point geo-pos:lat ?lat ;
           geo-pos:long ?lon .
	}
} where {
	?point a sf:Point ; geo:asWKT ?wkt .
    bind(xsd:float(replace(strafter(str(?wkt),"Point(")," .*","")) as ?lon)
    bind(xsd:float(replace(strafter(str(?wkt),"Point("),"([0-9]|\\.)* |\\)","")) as ?lat)
};

PREFIX : <http://www.ontotext.com/plugins/geosparql#>

#Enable plugin
INSERT DATA {
  _:s :enabled "true" .
};

#Make index
PREFIX ontogeo: <http://www.ontotext.com/owlim/geo#>
INSERT DATA { _:b1 ontogeo:createIndex _:b2. }