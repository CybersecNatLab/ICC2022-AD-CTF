#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include "cryptopp/integer.h"
#include "cryptopp/eccrypto.h"
#include "cryptopp/osrng.h"
#include "cryptopp/chacha.h"
#include "cryptopp/oids.h"
#include "cryptopp/hex.h"
#include "cryptopp/files.h"
#include "cryptopp/cryptlib.h"
#include "cryptopp/rijndael.h"
#include "cryptopp/modes.h"
using namespace CryptoPP;

#include <iostream>
#include <cstdlib>
using std::string;

#include "auth_utils.h"

typedef DL_GroupParameters_EC<ECP> GroupParameters;
typedef DL_GroupParameters_EC<ECP>::Element Element;

string get_secret(string psw){
  try{
    SHA256 hash;
    string digest, hexdigest;
    HexEncoder encoder(new StringSink(hexdigest));
    StringSource(psw, true, new HashFilter(hash, new StringSink(digest)));
    StringSource(digest, true, new Redirector(encoder));
    return (hexdigest + "h");
  }catch(...){
    return "BAD";
  }
}

struct AuthClient {
    GroupParameters group;
    AutoSeededRandomPool prng;
    Integer x1, x2, s;
    ECP::Point g1, g2, g3, g4, A, B;

    AuthClient(string username, string psw){
        group.Initialize(ASN1::secp256r1());
        x1 = Integer(prng, Integer::Zero(), group.GetMaxExponent());
        x2 = Integer(prng, Integer::One(), group.GetMaxExponent());
        g1 = group.ExponentiateBase(x1);
        g2 = group.ExponentiateBase(x2);
        s = Integer(get_secret(psw).c_str(), BIG_ENDIAN_ORDER) % (group.GetSubgroupOrder()*group.GetCofactor());
    }

    string get_starting_values();
    string get_final_values(string);
    string get_shared_key();
};

struct TicketClient {
    string username, srv_id, auth_token, shared_key;

    TicketClient(string _username, string _srv_id, string _auth_token, string _key){
        username = _username;
        srv_id = _srv_id;
        auth_token = _auth_token;
        shared_key = hex_to_string(_key);
    }

    string get_user_token();
    string finalize_token(string, string);
};

struct AuthService {
    GroupParameters group;
    AutoSeededRandomPool prng;
    Integer x3, x4, s;
    ECP::Point g1, g2, g3, g4, A, B;
    string username;
    string KEY;

    AuthService(string _username, string hex_psw, string _auth_key){
        group.Initialize(ASN1::secp256r1());
        x3 = Integer(prng, Integer::Zero(), group.GetMaxExponent());
        x4 = Integer(prng, Integer::One(), group.GetMaxExponent());
        g3 = group.ExponentiateBase(x3);
        g4 = group.ExponentiateBase(x4);
        s = Integer(hex_psw.c_str(), BIG_ENDIAN_ORDER);
        s = s % (group.GetSubgroupOrder()*group.GetCofactor());
        username = _username;
        KEY = _auth_key;
    }

    string get_values(string);
    string finalize_token(string);
};

struct TicketService {
    vector<string> service_keys;
    string KEY;

    TicketService(string _key, vector<string> _service_keys){
        KEY = _key;
        service_keys = _service_keys;
    }

    vector<string> get_service_tokens(string, string);

};

string AuthClient::get_starting_values(){
  try{
    string toret = IntToString(g1.x, 10) + "|" + IntToString(g1.y, 10) + "|" + IntToString(g2.x, 10) + "|" + IntToString(g2.y, 10);
    return string_to_hex(stream_encrypt(toret));
  }catch(...){
    return "BAD";
  }
}
string AuthClient::get_final_values(string enc_serverval){
  try{
    string dec = stream_decrypt(hex_to_string(enc_serverval));
    vector<string> elements = unpack_values(dec);
    if(elements.size() < 6) return std::to_string((int)elements.size());
    g3 = ECP::Point(Integer(elements[0].c_str(), BIG_ENDIAN_ORDER), Integer(elements[1].c_str(), BIG_ENDIAN_ORDER));
    g4 = ECP::Point(Integer(elements[2].c_str(), BIG_ENDIAN_ORDER), Integer(elements[3].c_str(), BIG_ENDIAN_ORDER));
    B = ECP::Point(Integer(elements[4].c_str(), BIG_ENDIAN_ORDER), Integer(elements[5].c_str(), BIG_ENDIAN_ORDER));
    A = group.GetCurve().Add(g1, g3);
    A = group.GetCurve().Add(A, g4);
    A = group.GetCurve().ScalarMultiply(A, x2*s);

    string toret = IntToString(A.x, 10) + "|" + IntToString(A.y, 10);
    return string_to_hex(stream_encrypt(toret));
  }catch(...){
    return "BAD";
  }
}
string AuthClient::get_shared_key(){
  try{
    Element Kb = group.GetCurve().Inverse(group.GetCurve().ScalarMultiply(g4, x2*s));
    Kb = group.GetCurve().Add(B, Kb);
    Kb = group.GetCurve().ScalarMultiply(Kb, x2);

    return string_to_hex(get_key_from_int(Kb.x));
  }catch(...){
    return "BAD";
  }
}

string TicketClient::get_user_token(){
  try{
    TOKEN user_token;
    user_token.ts = std::to_string(std::time(0));
    user_token.user = string_to_hex(username);
    user_token.key = "";
    user_token.type = "USER_TOKEN";
    user_token.service = srv_id;

    string user_token_json = serialize_token(user_token, shared_key);
    string enc_user_token = aes_256_encrypt(shared_key, user_token_json);

    return enc_user_token;
  }catch(...){
    return "BAD";
  }
}
string TicketClient::finalize_token(string enc_key_token, string enc_service_token){
  try{
        auto dec_key_token = aes_256_decrypt(shared_key, enc_key_token);
        auto key_token = deserialize_token(dec_key_token, true, shared_key);
        auto tmp_key = hex_to_string(key_token.key);

        TOKEN app_token;
        app_token.user = key_token.user;
        app_token.ts = std::to_string(std::time(0));
        app_token.key = "0";
        app_token.service = "0";
        app_token.type = "APP_TOKEN";

        auto enc_app_token = aes_256_encrypt(tmp_key, serialize_token(app_token, tmp_key));
        return enc_app_token + "." + enc_service_token;
  }catch(...){
    return "BAD";
  }
}

string AuthService::get_values(string enc_clientval){
  try{
    string dec = stream_decrypt(hex_to_string(enc_clientval));
    vector<string> elements = unpack_values(dec);
    if(elements.size() < 4) return std::to_string((int)elements.size());
    g1 = ECP::Point(Integer(elements[0].c_str(), BIG_ENDIAN_ORDER), Integer(elements[1].c_str(), BIG_ENDIAN_ORDER));
    g2 = ECP::Point(Integer(elements[2].c_str(), BIG_ENDIAN_ORDER), Integer(elements[3].c_str(), BIG_ENDIAN_ORDER));
    B = group.GetCurve().Add(g1, g2);
    B = group.GetCurve().Add(B, g3);
    B = group.GetCurve().ScalarMultiply(B, x4*s);

    string toret = IntToString(g3.x, 10) + "|" + IntToString(g3.y, 10) + "|" + IntToString(g4.x, 10) + "|" + IntToString(g4.y, 10) + "|" + IntToString(B.x, 10) + "|" + IntToString(B.y, 10);
    return string_to_hex(stream_encrypt(toret));
  }catch(...){
    return "BAD";
  }
}
string AuthService::finalize_token(string enc_clientval){
  try{
    string dec = stream_decrypt(hex_to_string(enc_clientval));
    vector<string> elements = unpack_values(dec);
    if(elements.size() < 2) return std::to_string((int)elements.size());
    A = ECP::Point(Integer(elements[0].c_str(), BIG_ENDIAN_ORDER), Integer(elements[1].c_str(), BIG_ENDIAN_ORDER));

    Element Ka = group.GetCurve().Inverse(group.GetCurve().ScalarMultiply(g2, x4*s));
    Ka = group.GetCurve().Add(A, Ka);
    Ka = group.GetCurve().ScalarMultiply(Ka, x4);

    auto key = get_key_from_int(Ka.x);

    TOKEN tgt_token;
    tgt_token.ts = std::to_string(std::time(0));
    tgt_token.user = string_to_hex(username);
    tgt_token.key = string_to_hex(key);
    tgt_token.type = "AUTH_TOKEN";
    tgt_token.service = "0";

    auto token = serialize_token(tgt_token, KEY);
    string enc_token = aes_256_encrypt(KEY, token);
    return enc_token;
  }catch(...){
    return "BAD";
  }
}

vector<string> TicketService::get_service_tokens(string enc_user_token, string enc_auth_token){
  try{
    auto dec_auth_token = aes_256_decrypt(KEY, enc_auth_token);
    auto auth_token = deserialize_token(dec_auth_token, true, KEY);
    assert(auth_token.type == "AUTH_TOKEN");
    assert(std::time(0) - std::stoi(auth_token.ts) < TOKEN_EXP);


    auto user_key = hex_to_string(auth_token.key);
    auto user = hex_to_string(auth_token.user);

    auto dec_user_token = aes_256_decrypt(user_key, enc_user_token);
    auto user_token = deserialize_token(dec_user_token, true, user_key);

    assert(user == hex_to_string(user_token.user));
    assert(user_token.type == "USER_TOKEN");
    assert(std::time(0) - std::stoi(user_token.ts) < TOKEN_EXP);

    TOKEN key_token;

    AutoSeededRandomPool prng;
    SecByteBlock tmp_key(AES::MAX_KEYLENGTH);
    prng.GenerateBlock(tmp_key, tmp_key.size());

    string str_tmp_key(reinterpret_cast<const char*>(&tmp_key[0]), tmp_key.size());
    auto hex_tmp_key = string_to_hex(str_tmp_key);

    key_token.key = hex_tmp_key;
    key_token.user = string_to_hex(user);
    key_token.service = "0";
    key_token.type = "KEY_TOKEN";
    key_token.ts = std::to_string(std::time(0));

    auto enc_key_token = aes_256_encrypt(user_key, serialize_token(key_token, user_key));

    TOKEN service_token;

    service_token.user = string_to_hex(user);
    service_token.key = hex_tmp_key;
    service_token.service = "0";
    service_token.type = "SERVICE_TOKEN";
    service_token.ts = std::to_string(std::time(0));

    auto enc_service_token = aes_256_encrypt(service_keys.at((size_t)(std::stoi(user_token.service) - 1)), serialize_token(service_token, service_keys.at((size_t)(std::stoi(user_token.service) - 1))));

    vector<string> ret;
    ret.push_back(enc_key_token);
    ret.push_back(enc_service_token);

    return ret;
  }catch(...){
    return {"BAD", ""};
  }
}

PYBIND11_MODULE(authlib, m) {
    py::class_<AuthClient>(m, "AuthClient")
        .def(py::init<string, string>())
        .def("get_starting_values", &AuthClient::get_starting_values)
        .def("get_final_values", &AuthClient::get_final_values)
        .def("get_shared_key", &AuthClient::get_shared_key);

    py::class_<TicketClient>(m, "TicketClient")
        .def(py::init<string, string, string, string>())
        .def("get_user_token", &TicketClient::get_user_token)
        .def("finalize_token", &TicketClient::finalize_token);

    py::class_<AuthService>(m, "AuthService")
        .def(py::init<string, string, string>())
        .def("get_values", &AuthService::get_values)
        .def("finalize_token", &AuthService::finalize_token);

    py::class_<TicketService>(m, "TicketService")
        .def(py::init<string, vector<string>>())
        .def("get_service_tokens", &TicketService::get_service_tokens);

    m.def("get_secret", &get_secret);
}
