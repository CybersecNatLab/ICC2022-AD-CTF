function keygen() {
    curve = sjcl.ecc.curves["k256"];
    keys = sjcl.ecc.ecdsa.generateKeys(curve);
    var pubkey = keys.pub.serialize().point;
    var privkey = keys.sec.serialize().exponent;
    //TODO: save privkey in local storage
    return {privkey, pubkey};
}

function sign(data, privkey) {
    console.log("signing", data);
    curve = sjcl.ecc.curves["k256"];
    secret = new sjcl.bn(privkey);
    var hash = sjcl.hash.sha256.hash(data);

    var R = curve.r, l = R.bitLength();
    var hbn = sjcl.bn.fromBits(hash);
    var k = hbn.mul(secret).mulmod(secret, R);
    var r = curve.G.mult(k).x.mod(R);
    var ss = hbn.add(r.mul(secret));
    var s = ss.mulmod(k.inverseMod(R), R);
    console.log(r.toString(), s.toString());
    var signature = sjcl.bitArray.concat(r.toBits(l), s.toBits(l));
    return sjcl.codec.hex.fromBits(signature);
}

function UI_create_key(){
    //priv ,pub = keygen();
    keys = keygen();
    $('#public_key').val(keys.pubkey);
    $('#private_ui').text(keys.privkey);
    $('#public_ui').text(keys.pubkey);

}
