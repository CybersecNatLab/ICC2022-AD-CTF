FROM node:12.22

RUN apt-get update \
 && apt-get install -y libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxi6 libxtst6 libnss3 libcups2 libxss1 libxrandr2 \
    libgconf-2-4 libasound2 libatk1.0-0 libgtk-3-0 dumb-init \
 && rm -rf /var/lib/apt/lists/*


#RUN chmod -R o+rx /usr/local/lib/nodejs/node-v12.22.1-linux-x64/lib/node_modules/puppeteer/.local-chromium

WORKDIR /app


COPY . /app
RUN npm install
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["node", "app.js"]