PROD_PROJECT=eddata-prod
PROD_ENV=./prod.env
STAGING_PROJECT=eddata-staging
STAGING_ENV=./staging.env


.PHONY: help up-prod down-prod up-staging down-staging


# Show this help (https://stackoverflow.com/a/35730928)
help:
	@awk '/^#/{c=substr($$0,3);next}c&&/^[[:alpha:]][[:alnum:]_-]+:/{print substr($$1,1,index($$1,":")),c}1{c=0}' $(MAKEFILE_LIST) | column -s: -t


# starts production docker-compose service
up-prod:
	docker compose --env-file $(PROD_ENV) -p $(PROD_PROJECT) up -d


# stops production docker-compose service
down-prod:
	docker compose --env-file $(PROD_ENV) -p $(PROD_PROJECT) down


# Starts staging docker-compose service
up-staging:
	docker compose --env-file $(STAGING_ENV) -p $(STAGING_PROJECT) up -d


# Stops staging docker-compose service
down-staging:
	docker compose --env-file $(STAGING_ENV) -p $(STAGING_PROJECT) down
