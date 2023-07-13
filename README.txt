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
-e FRONTEND_DATA_FOLDER=/original_tracks \
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
--entrypoint python plc-testbench-ui-frontend app.py

# connect to a running image in a shell
docker exec <container-id> -it sh

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
docker system prune -a --volumes
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
docker compose --env-file <path-to-env-file> up

#generate SSL cert and key
# run openssl in gitbash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem
openssl x509 -inform der -in zscaler-root-ca.cer -out zscaler-root-ca.pem
# application URL: https://127.0.0.1:5000/