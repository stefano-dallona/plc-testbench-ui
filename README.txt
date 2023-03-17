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
docker run --rm -it -p 5000:5000 [-d (detached mode)] [--entrypoint sh (to override the entrypoint)] plc-testbench-ui

# connect to a running image
docker exec <container-id> sh

# stopping the container
docker stop <container-id>

# removing a container
docker rm <container-id>  # after stop or docker rm --force <container-id> # without previously stopping the container

# deleting the image
docker image rm --force plc-testbench-ui

#access the application at URL http://<any-ip-of-the-host-except-loopback>:5000/


#GitHub Repo:
#https://github.com/stefano-dallona/plc-testbench-ui/
