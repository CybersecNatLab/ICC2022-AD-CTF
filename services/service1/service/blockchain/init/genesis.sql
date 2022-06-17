-- Create a couple of users
CREATE DATABASE blockchain;

USE blockchain;
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(30) NOT NULL UNIQUE,
    password VARCHAR(150) NOT NULL,
    public_key VARCHAR(150) NOT NULL,
    money1 INT NOT NULL DEFAULT 60,
    money2 INT NOT NULL DEFAULT 20
);

CREATE TABLE nfts(
    nft_id VARCHAR(36) PRIMARY KEY,
    owner VARCHAR(36) NOT NULL,
    title varchar(50),
    price INT, -- if zero, the NFT is a copy or unlisted
    data TEXT,
    nft_created  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES users(id)
);


CREATE TABLE nft_chain(
    nft_id VARCHAR(36),
    chain_number BOOLEAN, -- 0 is private, 1 is public
    PRIMARY KEY(nft_id, chain_number),
    FOREIGN KEY (nft_id) REFERENCES nfts(nft_id)
);


CREATE TABLE transactions(
    tx_id VARCHAR(36) PRIMARY KEY,
    from_user VARCHAR(36) NOT NULL,
    to_user VARCHAR(36) NOT NULL,
    nft_id VARCHAR(36) NOT NULL,
    type VARCHAR(10) NOT NULL,
    signature TEXT NOT NULL,
    time_executed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user) REFERENCES users(id),
    FOREIGN KEY (to_user) REFERENCES users(id)
);
