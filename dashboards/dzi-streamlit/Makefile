# Define the image name
IMAGE_NAME=data-for-good-bg/eddata

# Define the Dockerfile and build context
DOCKERFILE=Dockerfile
BUILD_CONTEXT=.


.PHONY: help build-prod build-staging

# https://stackoverflow.com/a/35730928

# Show this help.
help:
	@awk '/^#/{c=substr($$0,3);next}c&&/^[[:alpha:]][[:alnum:]_-]+:/{print substr($$1,1,index($$1,":")),c}1{c=0}' $(MAKEFILE_LIST) | column -s: -t


# Builds production docker image with production tag
build-prod:
	@if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then \
		echo "Error: You must be on the 'main' branch to build the production image."; \
		exit 1; \
	fi
	docker build -t $(IMAGE_NAME):production -f $(DOCKERFILE) $(BUILD_CONTEXT)


# Builds production docker image with staging tag
build-staging:
	docker build -t $(IMAGE_NAME):staging -f $(DOCKERFILE) $(BUILD_CONTEXT)
