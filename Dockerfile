FROM python:3.8-slim-buster
#FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine

WORKDIR /plc-testbench-ui

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies:
COPY requirements.txt .

RUN apt-get update
RUN apt-get install libsndfile1-dev --yes --force-yes
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

COPY . .
# Install ecctestbench:
RUN python3 -m pip install -f dist ecc-testbench

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0" ]