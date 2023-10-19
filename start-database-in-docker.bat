rem start mongo container
docker run ^
--rm --detach --memory=4g --publish 27017:27017 ^
--env MONGO_DATA_VOLUME_PATH=/mongo-data ^
--env MONGO_INITDB_ROOT_PASSWORD=Marmolada3343 ^
--env MONGO_INITDB_ROOT_USERNAME=root ^
--volume /mongo-data:/data/db ^
--name mongo ^
library/mongo:4.4.18