# these two are in common for all the chalenges.
# We need to install some packets in order to "simplify" some challenges
FROM python:3.10
RUN apt-get update \
    && apt-get upgrade -y

# common for python3 challenges
RUN useradd -ms /bin/null web && DEBIAN_FRONTEND="noninteractive" apt-get install -y nginx supervisor default-mysql-client

COPY requirements.txt /srv/app/
RUN pip3 install --no-cache-dir -r /srv/app/requirements.txt 

COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY src /srv/app/
COPY config/uwsgi.ini /srv/app/

ENV UWSGI_INI /srv/app/uwsgi.ini

WORKDIR /srv/app/

EXPOSE 80