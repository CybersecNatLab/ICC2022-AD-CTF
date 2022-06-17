#!/bin/bash

set -e;
DB_PASS=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom);

if [[ ! -f ".env" ]]
then
    echo "DB_PASS=${DB_PASS}" > .env
fi

docker-compose up --build --remove-orphans -d
