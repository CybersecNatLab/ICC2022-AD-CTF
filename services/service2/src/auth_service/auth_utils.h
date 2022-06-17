#include "cryptopp/integer.h"
#include "cryptopp/eccrypto.h"
#include "cryptopp/osrng.h"
#include "cryptopp/oids.h"
#include "cryptopp/hex.h"
#include "cryptopp/chacha.h"
#include "cryptopp/files.h"
#include "cryptopp/cryptlib.h"
#include "cryptopp/rijndael.h"
#include "cryptopp/modes.h"
#include "cryptopp/hmac.h"
using namespace CryptoPP;

#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
using namespace rapidjson;

#include <iostream>
#include <cstdlib>
#include <vector>
using std::string;
using std::vector;

const int TOKEN_EXP = 120;

struct TOKEN{
    string ts;
    string type;
    string user;
    string key;
    string service;
};

string get_key_from_int(Integer x){
    SHA256 hash;
    string digest;
    StringSource(IntToString(x), true, new HashFilter(hash, new StringSink(digest)));

    return digest;
}

string string_to_hex(string x){
    string to_ret;
    HexEncoder encoder(new StringSink(to_ret));
    StringSource(x, true, new Redirector(encoder));

    return to_ret;
}

string hex_to_string(string x){
    string to_ret;
    StringSource(x, true, new HexDecoder(new StringSink(to_ret)));

    return to_ret;
}

string serialize_token(TOKEN t, string _key = ""){
    const char* base_json = "{\"ts\":\"\",\"type\":\"\",\"user\":\"\",\"key\":\"\",\"service\":\"\"}";
    Document d;
    d.Parse(base_json);
    d["ts"].SetString(t.ts.c_str(), d.GetAllocator());
    d["type"].SetString(t.type.c_str(), d.GetAllocator());
    d["user"].SetString(t.user.c_str(), d.GetAllocator());
    d["key"].SetString(t.key.c_str(), d.GetAllocator());
    d["service"].SetString(t.service.c_str(), d.GetAllocator());

    if(_key != ""){
        string plain, tag;
        plain = t.ts + "|" + t.type + "|" + t.user + "|" + t.key + "|" + t.service;
        SecByteBlock key(reinterpret_cast<const unsigned char *>(_key.c_str()), 32);
        HMAC<SHA256> hmac(key, key.size());
        StringSource(plain, true, new HashFilter(hmac, new StringSink(tag)));
        d.AddMember("tag", "", d.GetAllocator());
        d["tag"].SetString(string_to_hex(tag).c_str(), d.GetAllocator());
    }

    StringBuffer buffer;
    Writer<StringBuffer> writer(buffer);
    d.Accept(writer);

    return buffer.GetString();
}

TOKEN deserialize_token(string json, bool check_tag = false, string _key = ""){
    Document d;
    d.Parse(json.c_str());

    TOKEN to_ret;
    to_ret.ts = d["ts"].GetString();
    to_ret.type = d["type"].GetString();
    to_ret.user = d["user"].GetString();
    to_ret.key = d["key"].GetString();
    to_ret.service = d["service"].GetString();

    if(check_tag && _key != ""){
        string tag;
        string token_tag = d["tag"].GetString();
        string plain = to_ret.ts + "|" + to_ret.type + "|" + to_ret.user + "|" + to_ret.key + "|" + to_ret.service;
        SecByteBlock key(reinterpret_cast<const unsigned char *>(_key.c_str()), 32);
        HMAC<SHA256> hmac(key, key.size());
        StringSource(plain, true, new HashFilter(hmac, new StringSink(tag)));
        if(token_tag != string_to_hex(tag)){
          TOKEN dummy_tok;
          return dummy_tok;
        }
    }

    return to_ret;
}

string aes_256_encrypt(string key, string msg){
    string ctx, hexctx;
    AutoSeededRandomPool prng;

    if(key.size() == 16) key = key + key;

    SecByteBlock aes_key(reinterpret_cast<const unsigned char *>(key.c_str()), AES::MAX_KEYLENGTH);
    SecByteBlock aes_iv(AES::BLOCKSIZE);

    CTR_Mode<AES>::Encryption e;
    HexEncoder encoder(new StringSink(hexctx));
    prng.GenerateBlock(aes_iv, aes_iv.size());
    e.SetKeyWithIV(aes_key, aes_key.size(), aes_iv);
    StringSource(msg, true, new StreamTransformationFilter(e, new StringSink(ctx)));
    string aes_iv_str(reinterpret_cast<const char*>(&aes_iv[0]), aes_iv.size());
    StringSource(aes_iv_str + ctx, true, new Redirector(encoder));

    return hexctx;
}

string aes_256_decrypt(string key, string enc){
  //try{
    string raw_enc = hex_to_string(enc);
    string plain;
    //assert(raw_enc.size() > 16);

    SecByteBlock aes_key(reinterpret_cast<const unsigned char *>(key.c_str()), AES::MAX_KEYLENGTH);
    SecByteBlock aes_iv(reinterpret_cast<const unsigned char *>(raw_enc.substr(0,AES::BLOCKSIZE).c_str()), AES::BLOCKSIZE);

    CTR_Mode<AES>::Decryption d;
    d.SetKeyWithIV(aes_key, aes_key.size(), aes_iv);
    StringSource(raw_enc.substr(16), true, new StreamTransformationFilter(d, new StringSink(plain)));

    return plain;
  //}catch(...){
  //  return "BAD";
  //}
}

string stream_encrypt(string plain){
    string _key = "00000000000000000000000000000000", _iv = "12345678", cipher;
    SecByteBlock key(reinterpret_cast<const unsigned char *>(_key.c_str()), 32);
    SecByteBlock iv(reinterpret_cast<const unsigned char *>(_iv.c_str()), 8);

    ChaCha20::Encryption enc;
    enc.SetKeyWithIV(key, key.size(), iv, iv.size());

    cipher.resize(plain.size());
    enc.ProcessData((byte*)&cipher[0], (const byte*)plain.data(), plain.size());

    return cipher;
}

string stream_decrypt(string cipher){
    string _key = "00000000000000000000000000000000", _iv = "12345678", plain;
    SecByteBlock key(reinterpret_cast<const unsigned char *>(_key.c_str()), 32);
    SecByteBlock iv(reinterpret_cast<const unsigned char *>(_iv.c_str()), 8);

    ChaCha20::Decryption dec;
    dec.SetKeyWithIV(key, key.size(), iv, iv.size());

    plain.resize(cipher.size());
    dec.ProcessData((byte*)&plain[0], (const byte*)cipher.data(), cipher.size());

    return plain;
}

vector<string> unpack_values(string inp){
    vector<string> elements;
    auto startpos = inp.find("|");
    if(startpos != string::npos){
        elements.push_back(inp.substr(0, startpos));
    }
    while(startpos != string::npos){
        auto oldstart = startpos;
        startpos = inp.find("|", oldstart+1);
        elements.push_back(inp.substr(oldstart+1, startpos-oldstart-1));
    }
    return elements;
}
