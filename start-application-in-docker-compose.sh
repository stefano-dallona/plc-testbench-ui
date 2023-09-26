#!/bin/sh
# start all containers based on docker
docker compose -f ./docker-compose.yml --env-file ./development-docker.env up