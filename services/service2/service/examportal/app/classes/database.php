<?php

function create_connection() {
    $dbhost = getenv("DBHOST");
    $dbuser = getenv("DBUSER");
    $dbpass = getenv("DBPASS");
    $dbname = getenv("DBNAME");

    $conn = new mysqli($dbhost, $dbuser, $dbpass, $dbname);
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }
    return $conn;
}

function execute_query_noparams($query) {
    $conn = create_connection();
    $result = $conn->query($query);
    $res = $result->fetch_all(MYSQLI_ASSOC);
    $conn->close();
    return $res;
}

function execute_query($query, $types, $params) {
    $conn = create_connection();
    $stmt = $conn->prepare($query);
    $stmt->bind_param($types, ...$params);
    $stmt->execute();
    if ($stmt->errno !== 0) {
        echo var_dump($stmt->error);
        return false;
    }
    $result = $stmt->get_result();
    $res = $result->fetch_all(MYSQLI_ASSOC);
    $conn->close();
    return $res;
}

function execute_insert($query, $types, $params) {
    $conn = create_connection();
    $stmt = $conn->prepare($query);
    $stmt->bind_param($types, ...$params);
    $stmt->execute();
    if ($stmt->errno !== 0) {
        echo var_dump($stmt->error);
        return -1;
    }
    $res = $stmt->insert_id;
    $conn->close();
    return $res;
}

function get_user($username) {
    $res = execute_query("SELECT * FROM users WHERE username = ?", "s", [$username]);
    if (count($res)===0) return false;
    return $res[0];
}

function add_user($username, $tfa) {
    return execute_insert("INSERT INTO users SET username = ?, 2fa = ?", "ss", [$username, $tfa]);
}

function get_all_exams() {
    $exams = execute_query_noparams("SELECT id, name FROM exams", "", []);
    return $exams;
}

?>
