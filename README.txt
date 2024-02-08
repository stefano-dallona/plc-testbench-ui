# virtual environment creation
cd <project-root>
python -m venv env

# virtual environment activation
.\env\Scripts\activate

# list virtual environment's packages
python -m pip freeze # > requirements.txt # in order to dump the dependencies into the requirements file

# manually add dependencies to a requirements file
echo <package-name>[==<package-version>] >> requirements.txt

# install dependencies from requirements.txt
python -m pip install -r requirements.txt

# virtual environment deactivation
.\env\Scripts\deactivate

# building image from dockerfile
docker build --tag plc-testbench-ui .

# running the image
docker run -e DATA_FOLDER="/plc-testbench-ui/original_tracks" -e ... --rm -it --memory="16g" -p 5000:5000 [-d (detached mode)] [--entrypoint sh (to override the entrypoint)] plc-testbench-ui
docker run \
-e MONGO_INITDB_ROOT_USERNAME=root \
-e MONGO_INITDB_ROOT_PASSWORD="" \
-e MONGO_DATA_VOLUME_PATH=/c/Data/plc-testbench-ui/plc-testbench-ui/ui/data \
-e FLASK_APP=app.py \
-e FLASK_DEBUG=0 \
-e DATA_FOLDER=/original_tracks \
-e DB_CONN_STRING=mongodb://mongo:27017 \
-e DB_HOST=mongo \
-e DB_USERNAME=root \
-e DB_PASSWORD="" \
-e GEVENT_SUPPORT=True \
-e GOOGLE_CLIENT_ID="" \
-e GOOGLE_CLIENT_SECRET="" \
-e GOOGLE_OAUTH_CERTS=https://www.googleapis.com/oauth2/v1/certs \
-e REQUESTS_CA_BUNDLE=/plc-testbench-ui/secrets/cacert.pem \
-e CERT_FILE=/plc-testbench-ui/secrets/cert.pem \
-e KEY_FILE=/plc-testbench-ui/secrets/key.pem \
--rm -it --memory="16g" -p 5000:5000 \
--entrypoint python plc-testbench-ui app.py

# connect to a running image in a shell
docker exec -it <container-id> sh

# attach to a running image
docker attach 0425a3719996

# stopping the container
docker stop <container-id>

# removing a container
docker rm <container-id>  # after stop or docker rm --force <container-id> # without previously stopping the container

# deleting the image
docker image rm --force plc-testbench-ui

# monitor container resources usage
docker stats <container-id>

# free space in docker machine
docker system prune --all --force --volumes

#access the application at URL http://<any-ip-of-the-host-except-loopback>:5000/

# free docker orphaned volumes
https://medium.com/@wlarch/no-space-left-on-device-when-using-docker-compose-why-c4a2c783c6f6#:~:text=1)%20Delete%20Orphaned%20Docker%20Volumes,data%20is%20stored%20on%20them.
docker volume rm $(docker volume ls -qf dangling=true)
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker system prune --volumes #most useful to reclaim space
docker rmi $(docker images -q)

#GitHub Repo:
#https://github.com/stefano-dallona/plc-testbench-ui/

# compile eccworkbench
cd <eccworkbench-src-directory>
cd <plc-workbench-src-directory>
python setup.py sdist

# uninstall eccworkbench from local archive
# after activating plc-testbench-ui virtualenv from plc-testbench-ui project dir
(env) python -m pip uninstall ecc_testbench
(env) python -m pip uninstall plc-testbench

# install eccworkbench from local archive
# after activating plc-testbench-ui virtualenv, copying the archive from plc-testbench into plc-testbench-ui project, executing from plc-testbench-ui project dir
(env) python -m pip install -f dist ecc_testbench
(env) python -m pip install <path-to-plc-testbench-*.tar.gz>

# running with waitress (WSGI server)
python -m pip install waitress
# switch app.run instruction with serve
python app.py

# App URLs:
#myIP: 10.223.35.25
http://<local-machine-ip>:5000/testbench-configuration.html
http://<local-machine-ip>:5000/testbench-output-analysis.html?run_id=<run_id>

# copy the file .vscode/launch.json in your .vscode directory in order to simplify launching
# replace output dir with your own path

# Staring up mongodb
docker-machine start default2
cd <project-root>
docker-compose up

# Start mongodb with custom env variables from file
docker compose --env-file <path-to-env-file> up [--build #to refresh the image]
docker compose --env-file .\development-docker.env up [--build #to refresh the image]

docker login --username stdallona
# access_token as password

ENV_FILE=/mongodb/development-docker.env && set -o allexport && dos2unix $ENV_FILE && source $ENV_FILE && set +o allexport && docker run \
--rm -it --memory="4g" -p 27010:27010 \
--env-file "$ENV_FILE"  \
--volume "${MONGO_DATA_VOLUME_PATH}:/data/db" \
--name mongo \
library/mongo:4.4.18

ENV_FILE=/mongodb/development-docker.env && set -o allexport && dos2unix $ENV_FILE && source $ENV_FILE && set +o allexport && docker run \
--rm -it -p "7000:${APP_PORT}" --memory="16g" \
--env-file "$ENV_FILE" \
--name plc-testbench-ui \
--link mongo:mongo \
stdallona/plc-testbench-ui:1.0.0

#"`"C:/Program Files/Docker Toolbox/docker-machine.exe`" ssh default2 `"[ -d /mongo-data ] || rm -fR /mongo-data`"" | cmd
powershell.exe -noprofile -executionpolicy bypass -file .\launch-command-with-env.ps1 -EnvFile development-docker.env docker run `
--rm -it --memory="4g" --publish '27017:27017' `
--env-file ./development-docker.env  `
--volume '${MONGO_DATA_VOLUME_PATH}:/data/db' `
--name mongo `
"library/mongo:4.4.18"

powershell.exe -noprofile -executionpolicy bypass -file .\launch-command-with-env.ps1 -EnvFile development-docker.env docker run `
--rm -it --memory="4g" --publish '27017:27017' `
--env-file ./development-docker.env  `
--volume '${MONGO_DATA_VOLUME_PATH}:/data/db' `
--name mongo `
"library/mongo:4.4.18"

powershell.exe -noprofile -executionpolicy bypass -file .\launch-command-with-env.ps1 -EnvFile development-docker.env docker run `
--rm -it --memory="16g" --publish 5000:5000 `
--env-file ./development-docker.env `
--volume 'C:/Data/plc-testbench-ui/plc-testbench-ui/secrets:/plc-testbench-ui/secrets' `
--volume 'C:/Data/personale/Università/2022-2023/original_tracks:${DATA_FOLDER}' `
--name plc-testbench-ui `
--link mongo:mongo `
stdallona/plc-testbench-ui:1.0.2


#Bug in google login (https://github.com/metabase/metabase/issues/32602)
#in order to fix it width in GoogleLogin component needs to be set as an int width={<w>} instead of width='<w>'

docker run ^
--rm -it --memory="16g" -p 5000:5000 ^
--env-file .\development-docker-mongoatlas.env  ^
--name plc-testbench-ui ^
stdallona/plc-testbench-ui:1.0.0

# start mongo container
docker run ^
--rm -it --memory=4g --publish 27017:27017 ^
--env MONGO_DATA_VOLUME_PATH=/mongo-data ^
--env MONGO_INITDB_ROOT_PASSWORD=Marmolada3343 ^
--env MONGO_INITDB_ROOT_USERNAME=root ^
--volume /mongo-data:/data/db ^
--name mongo ^
library/mongo:4.4.18

# start plc-testbench-ui container
docker run --rm -it --memory=16g --publish 9071:5000 ^
--env APP_PORT=5000 ^
--env CERT_FILE=/plc-testbench-ui/secrets/cert.pem ^
--env DB_CONN_STRING=mongodb://mongo:27017 ^
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
--env SECURITY_ENABLED=True ^
--volume /c/Data/plc-testbench-ui/plc-testbench-ui/secrets:/plc-testbench-ui/secrets ^
--volume /c/Data/personale/Università/2022-2023/original_tracks:/plc-testbench-ui/original_tracks ^
--name plc-testbench-ui ^
--link mongo:mongo ^
stdallona/plc-testbench-ui:1.0.2

#generate SSL cert and key
# run openssl in gitbash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem
openssl x509 -inform der -in zscaler-root-ca.cer -out zscaler-root-ca.pem
# application URL: https://127.0.0.1:5000/


# Debug python inside docker container with VS
#https://code.visualstudio.com/docs/containers/debug-python

!!! Attention !!!
The same DB on Windows cannot be shared between development mode (no containers)
and linux container mode as the file paths has a different and incompatible format.
So you need to either empty the DB by using the cleanup mongo statement, or use different
DBs.

# Dumping mongo database
mongodump \
--authenticationDatabase=admin \
--uri="mongodb://localhost:27017" \
--username=root --password=Marmolada3343 \
--db=stefano_dot_dallona_at_gmail_dot_com \
--archive=plc-testbench-db.20230921.gz \
--gzip

# Restoring mongo database
mongorestore \
--authenticationDatabase=admin \
--uri="mongodb://localhost:27017" \
--username=root \
--password=Marmolada3343 \
--gzip \
--archive=plc-testbench-db.20230921.gz \
--nsFrom "stefano_dot_dallona_at_gmail_dot_com.*" \
--nsTo "stefano_dot_dallona_2_at_gmail_dot_com.*"

# Installing jupiter in python virtual environment
# <venv_root>/Lib/Scripts/activate
python -m pip install ipykernel==6.16.2
python -m pip install ipywidgets

docker image pull docker.io/stdallona/plc-testbench-ui:x.x.x

PLC-Testbench-UI - Compliance rules
-----------------------------------
1) Each algorithm must extend directly or indirectly the base algorithm for the corresponding category (PacketLossSimulator, PLCAlgorithm, OutputAnalyser)
2) For each algorithm a corresponding Settings class must be provided
3) Each Settings class must inherit directly or indirectly from the base Settings class
4) Each Settings class must be named after the algorithm it belongs to, by suffixing the algorithm class name with 'Settings'
5) Each Settings class must have a constructor that supports instantiation with no arguments, providing therefore sensible defaults
6) If the change of any individual setting is supposed to enforce business rules or changes in the structure of the Settings, the class
   must expose a modifier for each such setting named after the setting by prefixing the setting name with "set_". The modifier method
   must have the new setting value as the only argument and must return a copy of the Settings consistent with the application of the needed logic.   
7) The type of each setting in a Settings class must be a base Python type (int, float, bool, str), an enumeration, a list of base types, a dictionary of base types,
   a list of other Settings classes, a dictionary having other Settings as values and a base type or enumeration as keys. Type hints must be provided for each constructor argument
   to allow proper type inference. All settings must appear as arguments in the constructor, except calculated/functionally dependent attributes that must be omitted from the constructor signature.
8) Enumeration must provide meaningful names for the values
9) Each algorithm must have a constructor that supports instantiation with the corresponding settings as the only argument
10) Each algorithm must provide progress events through tqdm iterators wrappers in the run method for the UI to be able to report progress properly

Any violation of these rules could end in the best case with the application ignoring the new algorithm, or in the worst case
with the application failing in unpredictable ways. 