# semantic-schools

Semantic data model and data integration specs for schools in Bulgaria.

* Endpoint URL: <http://edu.ontotext.com/>
* Repository: semantic-schools

Analysis of the ethnic population correlation with matura results can be found in the <b>analysis</b> folder. <br />
Vocab generation can be found in the <b>bin</b> folder. <br />
Data processing can be found in the <b>data</b> folder. <br />
The semantic model is visualized with graphs and diagrams in the <b>model</b> folder. <br />
Vocabulary generation happens in the <b>vocab</b> folder.

# Objectives

<b>The specific problem we are tackling is…</b>

The unavailability, fragmentation, overall poor quality, and limited culture of usage of public
education data. Thus, sub-optimal decisions and poor resource allocation limit Bulgaria’s
knowledge economy.

<b>To counter this problem, we...</b>

Design, build, continuously populate and maintain a data-centric infrastructure and public
Knowledge Graph integrating all relevant data related to Bulgarian school system. The data will
be published as five-star linked-data.

<b>If successful, in five years the impact of our project will be...</b>

The go-to data source for education research and good policy decisions & for deep insights into
the local education environment; a best practice on regional and European level.

# Method
![image](https://user-images.githubusercontent.com/80645419/120837640-9d896100-c56f-11eb-8329-3b575182168d.png)

<b>Scalable and sustainable data integration task</b>

# Data sources
* Wikidata (heavy contribution from us) - [Map with all schools in Bulgaria](https://query.wikidata.org/embed.html#%23defaultView%3AMap%0A%0Aselect%20%3Fschool%20%3FschoolLabel%20%3Floc%20%3Flayer%20%3Fsector%20%7B%0A%20%20%3Fschool%20wdt%3AP31%2Fwdt%3AP279%3F%20wd%3AQ3914%20%3B%20wdt%3AP131%20%3Fdistrict%20%3B%20wdt%3AP625%20%3Floc%20.%0A%20%20%3Fdistrict%20wdt%3AP31%20wd%3AQ7553685%20%3B%20wdt%3AP131%20wd%3AQ4442915%20.%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22bg%22.%20%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%3Fdistrict%20rdfs%3Alabel%20%3Flayer%20.%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%3Fschool%20rdfs%3Alabel%20%3FschoolLabel%20%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%23optional%20%7B%3Fschool%20wdt%3AP3896%20%3Fsector%20.%7D%0A%7D)

* Open Data From Ministry of Education - [Matura results](https://data.egov.bg/data?q=%D0%B7%D1%80%D0%B5%D0%BB%D0%BE%D1%81%D1%82%D0%B5%D0%BD+%D0%B8%D0%B7%D0%BF%D0%B8%D1%82)

* Demanded public data From Ministry of Education - [Example teacher demographics](https://docs.google.com/spreadsheets/d/1T8vBFHKMJ4zHuz-42Bp3KF7sVNDZmWkv/edit#gid=1341478489)
