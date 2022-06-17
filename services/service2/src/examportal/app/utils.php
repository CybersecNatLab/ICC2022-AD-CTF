<?php

function decrypt($ct, $key, $iv) {
    $ct = hex2bin($ct);
    $iv = hex2bin($iv);
    return openssl_decrypt($ct, "aes-256-ctr", $key,  OPENSSL_RAW_DATA| OPENSSL_ZERO_PADDING, $iv);
}

function validate_username($s) {
    return ctype_alnum($s) and (strlen($s)>7) and (strlen($s)<65);
}

function decode_token($token) {
    $app_key = getenv("ExamPortalKey");
    try {
        $pieces = explode(".", $token);
        $app_token = $pieces[0];
        $service_token = $pieces[1];

        $st_nonce = substr($service_token, 0, 32);
        $st_enc = substr($service_token, 32);

        $st_val = decrypt($st_enc, $app_key, $st_nonce);
        $st = json_decode($st_val, true);
        if ($st === false) return false;

        $user1 = hex2bin($st["user"]);
        $key = hex2bin($st["key"]);
        $at_nonce = substr($app_token, 0, 32);
        $at_enc = substr($app_token, 32);
        $at_val = decrypt($at_enc, $key, $at_nonce);
        $at = json_decode($at_val, true);
        if ($at === false) return false;

        $user2 = hex2bin($at["user"]);
        if ($st["type"] !== "SERVICE_TOKEN") return false;
        if ($at["type"] !== "APP_TOKEN") return false;
        if ($user1 !== $user2) return false;
        if (validate_username($user1)) return $user1;
        else return false;
    } catch (Exception $e) {
        echo 'Caught exception: ',  $e->getMessage(), "\n";
        return false;
    }
}


?>
