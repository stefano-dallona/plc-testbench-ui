#!/bin/sh

# start mongodb container
docker run \
--rm --detach --memory=4g --publish 27017:27017 \
--env MONGO_DATA_VOLUME_PATH=<path-to-your-mongo-data-inside-your-host> \ # e.g. /mongo-data
--env MONGO_INITDB_ROOT_PASSWORD=<password> \
--env MONGO_INITDB_ROOT_USERNAME=root \
--volume ${MONGO_DATA_VOLUME_PATH}:<path-to-your-mongo-data-inside-your-container> \ # e.g. /data/db
--name mongo \
library/mongo:4.4.18

# start plc-testbench-ui's web application's container
docker run --rm --detach --memory=16g \
--env APP_PORT=5000 \
--env CERT_FILE=<path-to-your-ssl-cert-file> \ # e.g. /plc-testbench-ui/secrets/cert.pem
--env DATA_FOLDER=/plc-testbench-ui/original_tracks \
--env DB_CONN_STRING=mongodb://mongo:27017 \
--env DB_PASSWORD=<mongodb-password> \
--env DB_USERNAME=root \
--env FLASK_APP=app.py \
--env FLASK_DEBUG=0 \
--env GEVENT_SUPPORT=True \
--env GOOGLE_CLIENT_ID=524953903108-944ibh494ugop6i54jh18gu2pkokfi9r.apps.googleusercontent.com \
--env GOOGLE_CLIENT_SECRET="" \
--env GOOGLE_OAUTH_CERTS=https://www.googleapis.com/oauth2/v1/certs \
--env KEY_FILE=<path-to-yout-ssl-key-file> \ # e.g. /plc-testbench-ui/secrets/key.pem
--env REQUESTS_CA_BUNDLE=<path-to-your-ca-keystore-file> \ e.g. /plc-testbench-ui/secrets/cacert.pem
--env SECURITY_ENABLED=True \
--volume <path-to-your-secrets-folder>:/plc-testbench-ui/secrets \ # e.g. /c/Data/plc-testbench-ui/plc-testbench-ui/secrets
--volume <path-to-your-data-folder-on-host>:${DATA_FOLDER} \ # e.g. /c/Data/personale/Università/2022-2023/original_tracks
--name plc-testbench-ui \
--link mongo:mongo \
--publish <host-port>:${APP_PORT} \
stdallona/plc-testbench-ui:1.0.5