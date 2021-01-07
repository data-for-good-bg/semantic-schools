PREFIX qb:             <http://purl.org/linked-data/cube#>

# Dataset attachments
INSERT {
    GRAPH ?dataset {
    	?obs  ?comp ?value
	}
} WHERE {

    ?spec    qb:componentProperty ?comp ;
             qb:componentAttachment qb:DataSet .
    ?dataset qb:structure [qb:component ?spec];
             ?comp ?value .
    GRAPH ?dataset {
    	?obs     qb:dataSet ?dataset.
	}
}