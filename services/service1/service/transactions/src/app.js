'use strict';

const asyncHandler = require('express-async-handler')
const EC = require('elliptic').ec;
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');
const starter = require('./start-app.js');


const app = starter.app;
const io = starter.io;
const pool = starter.pool;
const spdy_server = starter.spdy_server;
const query = starter.query; 


function insert_nft(nft, chain, callback) {
    let {owner, title, data, price, id} = nft;
    
    if(!id){
        id = uuidv4();
    }
    var new_nft = {
        nft_id: id,
        price: price,
        owner: owner,
        title: title,
        data: data
    }
    pool.query("INSERT INTO nfts SET ?", [new_nft], (err, result, fields) => {
        pool.query("INSERT INTO nft_chain SET ?", [{nft_id: id, chain_number: chain}], (err, result, fields) => {
            
            if (err) callback(err, -1);

            callback(null, id);
        });
    });
}

function insert_transaction(nft_id, from_user, to_user, type, signature) {
    var tx_id = uuidv4();
    var tx = { tx_id, nft_id, from_user, to_user, type, signature };
    pool.query("INSERT INTO transactions SET ?", [tx], (err, results) => {
        if (err) throw err;
        // real time transactions!!!
        var time_executed = new Date().toISOString();
        var stx = {...tx, time_executed};
        io.emit("transactions_rt", stx);
    });
}


function verify(hash, signature, pubkey) {
    var ec = new EC('secp256k1');
    var pub = "04"+pubkey;
    var key = ec.keyFromPublic(pub, 'hex');
    var sig = {r: signature.slice(0, 64), s: signature.slice(64, 128)};

    return key.verify(hash, sig);
}


io.on('connection', (socket) => {
    console.log('User Connected');  


  socket.on('transactions_all', (msg) => {
    pool.query("SELECT * FROM transactions ORDER BY time_executed DESC LIMIT 10", (err, results, fields) => {
        socket.emit('transactions_resp', results);
    });
  });

  socket.on('transactions_for_nft', (nft_id) => {
      pool.query("SELECT * FROM transactions WHERE nft_id = ? ORDER BY time_executed DESC LIMIT 10", [nft_id], (err, results, fields) => {
          socket.emit('transactions_resp', results);
      });
  });

  socket.on('transactions_for_user', (user_id) => {
      pool.query("SELECT * FROM transactions WHERE from_user = ? OR to_user = ? ORDER BY time_executed DESC LIMIT 10", [user_id, user_id], (err, results, fields) => {
          
          socket.emit('transactions_resp', results);
      });
  });

  socket.on('disconnect', () => {
    console.log('user disconnected');
  });
});


app.get('/', (req, res) => {
  res.writeHead(200);
  res.end('SERVICE HEALTHY');
});

app.post('/switch_chain', asyncHandler(async (req, res, next) => {
    var nft_id = req.body.nft_id;
    var user_id = req.body.user_id;
    var chain_number = req.body.chain;

    var user = await query("SELECT * FROM users WHERE id = ?", [user_id]);
    user = user[0];
    var nft = await query("SELECT * FROM nfts JOIN nft_chain ON nfts.nft_id = nft_chain.nft_id WHERE nfts.nft_id = ?", [nft_id]);
    nft = nft[0];

    if (nft.owner != user_id) {
        res.json({"success": false, "message": "You don't own this NFT!"})
        return;
    }

    pool.query("DELETE FROM nft_chain WHERE nft_id = ? ", [nft_id], (err, results, fields) => {
        pool.query("INSERT INTO nft_chain SET ?", [{nft_id: nft_id, chain_number: chain_number}], (err, result, fields) => {
            if (err){
                res.json({"success": false});
                return;
            }

            res.json({"success": true});
        });
    });


}));

app.post('/donate', asyncHandler(async (req, res, next) => {
    var from_addr = req.body.from_addr;
    var to_addr = req.body.to_addr;
    var nft_id = req.body.nft_id;
    var signature = req.body.signature;
    var pubkey = req.body.pubkey;

    var blob = JSON.stringify({"nft_id": nft_id, "from_addr": from_addr, "to_addr": to_addr});
    var hash = crypto.createHash('sha256').update(blob).digest('hex');

    if (!verify(hash, signature, pubkey)) {
        res.json({"success": false, "message": "Signature verification failed"})
        return;
    }

    var nft = await query("SELECT * FROM nfts JOIN nft_chain ON nfts.nft_id = nft_chain.nft_id WHERE nfts.nft_id = ?", [nft_id]);
    nft = nft[0];

    if (nft.owner != from_addr) {
        res.json({"success": false, "message": "You don't own this NFT!"})
        return;
    }

    var copy_nft = {
        owner: to_addr,
        title: nft.title,
        data: nft.data,
        price: 0
    }

    insert_transaction(nft.nft_id, from_addr, to_addr, "donate", signature);
    insert_nft(copy_nft, nft.chain_number, (err, new_id) => {
        
        if (err) {
            res.json({"success": false});
            return;
        }
        res.json({"success": true, "new_id": new_id});
    });
}));

app.post('/buy', asyncHandler(async (req, res, next) => {

    var nft_id = req.body.nft_id;
    var user_id = req.body.user_id;
    var signature = req.body.signature;
    var pubkey = req.body.pubkey;


    var blob = JSON.stringify({"nft_id": nft_id, "user_id": user_id});
    var hash = crypto.createHash('sha256').update(blob).digest('hex');

    if (!verify(hash, signature, pubkey)) {
        res.json({"success": false, "message": "Signature verification failed"})
        return;
    }

    var user = await query("SELECT * FROM users WHERE id = ?", [user_id]);
    user = user[0];
    var nft = await query("SELECT * FROM nfts JOIN nft_chain ON nfts.nft_id = nft_chain.nft_id WHERE nfts.nft_id = ?", [nft_id]);
    nft = nft[0];

    if (nft.price == 0) {
        res.json({"success": false, "message": "Cannot buy a copy of a nft!"});
        return;
    }

    if (nft.chain_number) {
        var money = user.money2;
        var obj_update = {money2: user.money2-nft.price};
    } else {
        var money = user.money1;
        var obj_update = {money1: user.money1-nft.price};
    }

    if (nft.price > money) {
        res.json({"success": false, "message": "Not enough money"});
        return;
    }

    await query("UPDATE users SET ? WHERE id = ?", [obj_update, user_id]);

    var copy_nft = {
        owner: user_id,
        title: nft.title,
        data: nft.data,
        price: 0
    }
    insert_transaction(nft.nft_id, nft.owner, user_id, "buy", signature);
    insert_nft(copy_nft, nft.chain_number, (err, new_id) => {

        if (err) {
            res.json({"success": false});
            return;
        }
        res.json({"success": true, "new_id": new_id});
    });
}));

app.post('/mint', asyncHandler(async (req, res) => {
    var owner = req.body.owner;
    var title = req.body.title;
    var data = req.body.data;
    var price = req.body.price;
    var chain = req.body.public;
    var id = req.body.id;
    
    if(title.length > 50){
      res.json({"success": false});
      return;
    }

    var user = await query("SELECT * FROM users WHERE id = ?", [owner]);
    if (user == false) {
        res.json({"success": false});
        return;
    }
    user = user[0];

    const mint_cost = 1;
    if (chain) {
        var money = user.money2;
        var obj_update = {money2: user.money2-mint_cost};
    } else {
        var money = user.money1;
        var obj_update = {money1: user.money1-mint_cost};
    }

    if (money<mint_cost) {
        res.json({"success": false, "message": "Not enough money"});
        return;
    }
    await query("UPDATE users SET ? WHERE id = ?", [obj_update, owner]);

    var nft = {owner, title, data, price, id};
    insert_nft(nft, chain, (err, new_id) => {
        
        if (err) {
            res.json({"success": false});
            return;
        }
        res.json({"success": true, "new_id": new_id});
    })
}));

app.get('*', (req, res) => {
  res.writeHead(404);
  res.end('Not found');
});

app.use(function(err, req, res) {
    res.status(err.status || 500);
    res.render('error', {
        message: 'Error',
        error: {}
    });
    ;        
});

process.on('unhandledRejection', (reason, promise) => {
    console.log(reason)
    
   });
    
process.on('uncaughtException', (error) => {
 console.log(error);
});

console.log('Starting the transactions service.');
spdy_server.listen(8085);
