'use strict';

const spdy = require('spdy');
const spdy_transport = require('spdy-transport');
const util = require('util');
const express = require('express');
const { Server } = require("socket.io");
const asyncHandler = require('express-async-handler');
const mysql = require('mysql');

function http2_upgrade(req, sock, head) {
    var conn = (req.headers['connection'] || '').toLowerCase().split(/,\s*/);
    var upg = (req.headers['upgrade'] || '').toLowerCase();
    if (
      conn.indexOf('upgrade') != -1 &&
      conn.indexOf('http2-settings') != -1 &&
      /^h2c/.test(upg) &&
      'http2-settings' in req.headers
    ) {
      sock.write([
        'HTTP/1.1 101 Switching Protocols',
        'Connection: Upgrade',
        'Upgrade: ' + upg,
        '', ''
      ].join('\r\n'));
      delete req.headers['upgrade'];
      delete req.headers['connection'];
      delete req.headers['http2-settings'];
      var connection = spdy_transport.connection.create(sock, util._extend({
        protocol: 'http2',
        isServer: true
      }, this._spdyState.options.connection || {}));
      connection.start(4);
      connection.on('error', sock.destroy.bind(sock));
      connection.on('stream', this._onStream.bind(this));
      connection._handleFrame({
        type: 'HEADERS',
        id: 1,
        priority: { parent: 0, exclusive: false, weight: 16 },
        fin: false,
        writable: true,
        headers: util._extend(req.headers, {
          ':method': req.method,
          ':path': req.url,
          ':scheme': 'http',
          ':authority': req.headers.host,
        }),
        path: req.url
      });
      return true;
    }
}

const app = express();
app.use(express.json());
  

var spdy_server = spdy.createServer({
  spdy: {
    protocols: ['h2', 'http/1.1'],
    plain: true,
    ssl: false,
  }
}, app);
  
const io = new Server(spdy_server);

spdy_server.on('upgrade', function (req, sock, head) {
  if (http2_upgrade.call(this, req, sock, head)) return;
});

const pool = mysql.createPool({
    connectionLimit: 10,
  host: process.env.DBHOST,
  user: process.env.DBUSER,
  password: process.env.DBPASS,
  database: process.env.DBSCHEMA
});

const query = util.promisify(pool.query).bind(pool);


exports.app = app;
exports.query = query;
exports.pool = pool;
exports.io = io;
exports.spdy_server = spdy_server;
