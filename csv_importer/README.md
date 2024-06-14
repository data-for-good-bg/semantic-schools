This directory contains python code which will handle importing NVO and DZI
data provided by egov.data.bg into relational or graph DB.

The initial version is quite simple:

1. Python code will be used to convert the various CSV files into the same
format.


2. Python code will push the refined CSV files into relational DB (sqlite, Postgres, BigQuery)
sqlachemy library will be used in order to support different SQL engines.

The long term version probably will be something like this:

1. Python code will be used to convert the various CSV files into the same
format.

2. Python code and SPARQL will be used to import scores data into GraphDB from
the refined CSV files

3. Python code and SPARQL will be used to import information for city, villages,
schools, into GraphDB

4. Python code will be used to create relational database from the GraphDB.
