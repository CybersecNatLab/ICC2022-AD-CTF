FROM ubuntu:20.04

RUN apt-get update && apt-get install -y python3 python3-dev socat python3-pip

WORKDIR /service/server
COPY app/requirements.txt .
RUN pip install -r ./requirements.txt

COPY app .
RUN mkdir -p /service/server/data && chown -R nobody /service/server
USER nobody
ENV EncryptedNotesKey="EncryptedNotesAppDefaultKey00000"

ENTRYPOINT socat -d TCP-LISTEN:8000,reuseaddr,fork EXEC:'python3 server.py'
