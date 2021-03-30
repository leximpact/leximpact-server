FROM python:3.7

WORKDIR /opt
RUN apt-get update && apt-get -y install libyaml-dev libhdf5-serial-dev postgresql-client
RUN git clone https://github.com/leximpact/leximpact-server.git
WORKDIR /opt/leximpact-server
# Copy default conf
RUN cp ./docker/docker.env .env
# Tips : relative path is from root project folder as we use context in docker-compose
#COPY ./docker/.env.docker .env
# TODO : For unknown reseon we have to intall numpy to make "Building wheel for tables (setup.py)" work
# Despite it exist in dependancies.
RUN pip install numpy
RUN make install
RUN make test

# Make sure the entrypoint is executable
RUN chmod a+x entrypoint.sh
EXPOSE 5000
ENTRYPOINT ["/opt/leximpact-server/docker/entrypoint.sh"]
#ENTRYPOINT ["watch", "-n", "60", "echo 'Server is in debug...'"]
