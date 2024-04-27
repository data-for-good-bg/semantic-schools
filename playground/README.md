The docker-compose file in this directory starts Jupyter notebook in container
and allows experimenting with data.

In order to use one should:
1. Install docker-compose -> https://docs.docker.com/compose/install/.
2. Then follow this:

```
cd playground

# create the work directory which is mounted in the container
mkdir -p work

# make the directory owned by user with id 1000, because the container
# works on behalf of such user
chown 1000:1000 work

# start docker-compose and follow the instructions
docker-compose up

```
