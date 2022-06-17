FROM ubuntu:20.04

RUN apt update \
    && apt install -y python3 python3-dev socat python3-pip gcc g++ make libffi-dev

RUN useradd --no-create-home --shell /bin/false --uid 1000 --user-group srv

ADD authlib.cpython-38-x86_64-linux-gnu.so /service/server/
ADD server.py user_handlers.py /service/server/

WORKDIR /service/server
RUN mkdir users
RUN chmod +x server.py
RUN chmod -R 777 users

USER srv
ENV MasterKey="AuthenticationSystemMasterKey000"
ENV ExamNotesKey="ExamNotesAppDefaultKey0000000000"
ENV EncryptedNotesKey="EncryptedNotesAppDefaultKey00000"
ENV ExamPortalKey="ExamPortalAppDefaultKey000000000"

ENTRYPOINT socat -d TCP-LISTEN:8000,reuseaddr,fork EXEC:'timeout -k 5 30 python3 -u server.py'
