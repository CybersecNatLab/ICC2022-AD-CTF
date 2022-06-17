<?php

require_once('database.php');

class User {
    private $id;
    private $username;
    private $tfa=NULL;

    public function __construct($username) {
        $this->username = $username;
    }

    public function do_login($tfa) {
        $db_user = get_user($this->username);
        if ($db_user === false) {
            // add the user, trusting the login token
            if ($tfa === "") $tfa = NULL;
            $res = add_user($this->username, $tfa);
            if ($res === -1) return false;
            $this->id = $res;
            $this->tfa = $tfa;
            return true;
        }
        if (($db_user["2fa"] !== NULL) && ($db_user["2fa"] !== $tfa)) return false;
        $this->id = $db_user["id"];
        $this->tfa = $db_user["2fa"];
        return true;
    }

    public function getId() {
        return $this->id;
    }

    public function getUsername() {
        return $this->username;
    }

    public function has2fa() {
        return ($this->tfa !== NULL);
    }
}

?>
