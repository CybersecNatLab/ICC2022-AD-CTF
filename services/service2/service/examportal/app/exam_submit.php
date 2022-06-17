<?php

require_once("classes/exam.php");
require_once("classes/user.php");

session_start();
if (!isset($_SESSION["user"])) die(json_encode(["msg" => "Login is required"]));

if (isset($_POST)) {
    $obj = json_decode(file_get_contents("php://input"), true);
    $id = $obj["id"];
    $exam = Exam::fromId($id);
    if ($exam->DB_get() == false) die("No such exam");
    $correct = $exam->getCorrect();
    $num = count($correct);
    $score = 0;
    foreach($correct as $i=>$corr_ans) {
        $given_ans = $obj["answers"][$i];
        if ($corr_ans == $given_ans) $score++;
    }
    if ($score == $num) $message = $exam->getPrize();
    else $message = "Better luck next time!";

    echo json_encode(["msg" => $message]);
}
?>
