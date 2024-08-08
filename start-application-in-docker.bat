rem start mongo container
docker run ^
--rm --detach --memory=4g --publish 27017:27017 ^
--env MONGO_DATA_VOLUME_PATH=/mongo-data ^
--env MONGO_INITDB_ROOT_PASSWORD=Marmolada3343 ^
--env MONGO_INITDB_ROOT_USERNAME=root ^
--volume /mongo-data:/data/db ^
--name mongo ^
library/mongo:4.4.18

rem start plc-testbench-ui container
docker run --rm --detach ^
--memory=16g ^
--publish 9071:5000 ^
--publish 5678:5678 ^
--env APP_PORT=5000 ^
--env CERT_FILE=/plc-testbench-ui/secrets/cert.pem ^
--env DB_CONN_STRING=mongodb://mongo:27017 ^
--env DB_HOST=mongo ^
--env DB_PASSWORD=Marmolada3343 ^
--env DB_USERNAME=root ^
--env FLASK_APP=app.py ^
--env FLASK_DEBUG=0 ^
--env DATA_FOLDER=/plc-testbench-ui/original_tracks ^
--env GEVENT_SUPPORT=True ^
--env GOOGLE_CLIENT_ID=524953903108-944ibh494ugop6i54jh18gu2pkokfi9r.apps.googleusercontent.com ^
--env GOOGLE_CLIENT_SECRET="" ^
--env GOOGLE_OAUTH_CERTS=https://www.googleapis.com/oauth2/v1/certs ^
--env KEY_FILE=/plc-testbench-ui/secrets/key.pem ^
--env REQUESTS_CA_BUNDLE=/plc-testbench-ui/secrets/cacert.pem ^
--env SECURITY_ENABLED=False ^
--env DEBUGPY_PROCESS_SPAWN_TIMEOUT=180 ^
--volume /c/Data/plc-testbench-ui/plc-testbench-ui/secrets:/plc-testbench-ui/secrets ^
--volume /c/Data/personale/Università/2022-2023/original_tracks:/plc-testbench-ui/original_tracks ^
--name plc-testbench-ui ^
--link mongo:mongo ^
stdallona/plc-testbench-ui:1.4.0