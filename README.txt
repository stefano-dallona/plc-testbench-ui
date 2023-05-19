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
docker run -e DATA_FOLDER="/plc-testbench-ui/original_tracks" --rm -it --memory="16g" -p 5000:5000 [-d (detached mode)] [--entrypoint sh (to override the entrypoint)] plc-testbench-ui

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