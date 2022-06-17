FROM ubuntu:20.04

RUN apt update \
    && apt install -y python3 python3-dev socat python3-pip gcc g++ make libffi-dev

WORKDIR /service/server
ADD app/requirements.txt .
RUN pip3 install -r requirements.txt

RUN useradd --no-create-home --shell /bin/false --uid 1000 --user-group app1

ADD app .
RUN mkdir data
RUN chmod +x server.py
RUN chmod -R 777 data

USER app1
ENV ExamNotesKey="ExamNotesAppDefaultKey0000000000"

ENTRYPOINT socat -d TCP-LISTEN:8000,reuseaddr,fork EXEC:'timeout -k 5 30 python3 -u server.py'
