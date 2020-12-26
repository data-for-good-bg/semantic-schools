#!/usr/bin/env bash

#Measures
curl "https://docs.google.com/spreadsheets/d/1UgEswvbaF9qDGyK8Gq2hkO4F1DtXsXvrY4eE_rDKAUs/gviz/tq?tqx=out:csv&sheet=Measures" | ../bin/my-tarql "-d , --stdin" ../model/prefixes.ttl tarql/measures.tarql > rdf/measures.ttl

#Attributes
curl "https://docs.google.com/spreadsheets/d/1UgEswvbaF9qDGyK8Gq2hkO4F1DtXsXvrY4eE_rDKAUs/gviz/tq?tqx=out:csv&sheet=Attributes" | ../bin/my-tarql "-d , --stdin" ../model/prefixes.ttl tarql/attributes.tarql > rdf/attributes.ttl

#Dimensions
curl "https://docs.google.com/spreadsheets/d/1UgEswvbaF9qDGyK8Gq2hkO4F1DtXsXvrY4eE_rDKAUs/gviz/tq?tqx=out:csv&sheet=Dimensions" | ../bin/my-tarql "-d , --stdin" ../model/prefixes.ttl tarql/dimensions.tarql > rdf/dimensions.ttl

#RDF-ize coded list master sheet
curl "https://docs.google.com/spreadsheets/d/1UgEswvbaF9qDGyK8Gq2hkO4F1DtXsXvrY4eE_rDKAUs/gviz/tq?tqx=out:csv&sheet=CodeListMaster" | ../bin/my-tarql "-d , --stdin" ../model/prefixes.ttl tarql/codedLists.tarql > rdf/codedLists.ttl

#Subject coded list values
curl "https://docs.google.com/spreadsheets/d/1UgEswvbaF9qDGyK8Gq2hkO4F1DtXsXvrY4eE_rDKAUs/gviz/tq?tqx=out:csv&sheet=subject" | ../bin/my-tarql "-d , --stdin" ../model/prefixes.ttl tarql/codedValues.tarql > rdf/subject.ttl

#Statistical Summary
#curl "https://docs.google.com/spreadsheets/d/1UgEswvbaF9qDGyK8Gq2hkO4F1DtXsXvrY4eE_rDKAUs/gviz/tq?tqx=out:csv&sheet=measurementContext" | ../bin/my-tarql "-d , --stdin" ../model/prefixes.ttl  tarql/measurementContexts.tarql > rdf/measurementContext.ttl

#Concatenate vocabulary
cat rdf/*.ttl | riot --syntax=ttl --formatted=ttl> semantic-schools.ttl