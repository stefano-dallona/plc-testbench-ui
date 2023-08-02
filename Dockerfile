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
# Install gstremer dependencies
RUN apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio git gtk-doc-tools git2cl --yes --force-yes
# Start of download and compile gstpeaq
RUN mkdir gstpeaq && git clone https://github.com/HSU-ANT/gstpeaq.git gstpeaq
WORKDIR /plc-testbench-ui/gstpeaq
RUN aclocal && autoheader && ./autogen.sh && sed -i 's/SUBDIRS = src doc/SUBDIRS = src/' Makefile.am && ./configure --libdir=/usr/lib && automake && make && make install
# End of download and compile gstpeaq
WORKDIR /plc-testbench-ui
# Install plctestbench
RUN git clone --branch ui https://github.com/LucaVignati/plc-testbench.git && cd plc-testbench && python setup.py sdist && python3 -m pip install -f ./dist plc-testbench
# Install ui dependencies
COPY requirements.txt /tmp
RUN python3 -m pip install --upgrade pip && python3 -m pip install -r /tmp/requirements.txt

COPY . .

ENTRYPOINT [ "python3", "app.py" ]