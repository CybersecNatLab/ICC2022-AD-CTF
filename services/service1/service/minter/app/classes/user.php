<?php
require_once 'functions.php';

class User{
    private $username;
    private $public_key;
    private $id;

    public function __construct($username, $password)
    {
        $data = [
            'username' => $username,
            'password' => $password
        ];
        $LOGIN_PATH = 'http://' . getenv('CLOSED_SEA_HOST') . '/api/login';
        $result = request_post($LOGIN_PATH, $data);

        if(!$result){
            throw new Exception('Cannot login user');
        }
        $this->username = $result->username;
        $this->id = $result->user_id;
        $this->public_key = $result -> public_key;
    }

    public function getId(){
        return $this->id;
    }
}