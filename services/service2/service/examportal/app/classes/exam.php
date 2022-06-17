<?php

require_once('database.php');

class Exam {
    private $id;
    private $owner;
    private $name;
    private $questions;
    private $answers;
    private $correct;
    private $prize;

    public function __construct() {
        return;
    }

    public static function fromId($id) {
        $exam = new Exam();
        $exam->setId($id);
        return $exam;
    }

    public static function fromVals($owner, $name, $questions, $answers, $correct, $prize) {
        $exam = new Exam();
        $exam->setOwner($owner);
        $exam->setName($name);
        $exam->setQuestions($questions);
        $exam->setAnswers($answers);
        $exam->setCorrect($correct);
        $exam->setPrize($prize);
        return $exam;
    }

    public function DB_get() {
        $res = execute_query("SELECT * FROM exams WHERE id = ?", "i", [$this->id]);
        if ($res===false) return false;
        if (count($res)!==1) return false;
        $exam_db = $res[0];
        $this->owner = $exam_db["owner"];
        $this->name = $exam_db["name"];
        $this->questions = $exam_db["questions"];
        $this->answers = $exam_db["answers"];
        $this->correct = $exam_db["correct"];
        $this->prize = $exam_db["prize"];
        return true;
    }

    public function DB_set() {
        $vals = [$this->owner, $this->name, $this->questions, $this->answers, $this->correct, $this->prize];
        $res = execute_insert("INSERT INTO exams SET owner = ?, name = ?, questions = ?, answers = ?, correct = ?, prize = ?", "isssss", $vals);
        if ($res === -1) return false;
        $this->id = $res;
        return $res;
    }

    public function getId() {
        return $this->id;
    }

    public function setId($id) {
        $this->id = $id;
    }

    public function getOwner() {
        return $this->owner;
    }

    public function setOwner($owner) {
        $this->owner = $owner;
    }

    public function getName() {
        return $this->name;
    }

    public function setName($name) {
        $this->name = $name;
    }

    public function getPrize() {
        return $this->prize;
    }

    public function setPrize($prize) {
        $this->prize = $prize;
    }

    public function getQuestions() {
        return explode("|", $this->questions);
    }

    public function setQuestions($questions) {
        $this->questions = implode("|", $questions);
    }

    public function getCorrect() {
        return explode("|", $this->correct);
    }

    public function setCorrect($correct) {
        $this->correct = implode("|", $correct);
    }

    public function getAnswers() {
        $ans = explode("|", $this->answers);
        $res = [];
        foreach($ans as $a) array_push($res, explode(";", $a));
        return $res;
    }

    public function setAnswers($answers) {
        $ans = [];
        foreach($answers as $a) array_push($ans, implode(";", $a));
        $this->answers = implode("|", $ans);
    }
}
