1. make yourself postgres
su - postgres


2. create the database and two users
```
createdb eddata

createuser -P eddata-reader
createuser -P eddata-writer

```

3. start `psql eddata`

grant permissions to the two users

```
grant connect on database eddata to "eddata-reader";
grant connect on database eddata to "eddata-writer";

GRANT SELECT ON ALL TABLES IN SCHEMA public to "eddata-reader";
grant all on schema public TO "eddata-writer";
```