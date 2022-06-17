#!/bin/bash

DB_PASS=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom);
SECRET_CLOSEDSEA=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom);

if [[ ! -f ".env" ]]
then
    echo "BLOCKCHAIN_PASSWORD=${DB_PASS}" > .env
    echo "SECRET_CLOSEDSEA=${SECRET_CLOSEDSEA}" >> .env
fi

docker-compose up --build --remove-orphans -d
