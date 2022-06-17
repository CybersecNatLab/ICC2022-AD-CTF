<?

require_once("classes/user.php");
require_once("classes/exam.php");
session_start();

if (!isset($_SESSION["user"])) die("Authentication required");
$user = $_SESSION["user"];

if (!empty($_POST["name"])) {
    if (!$user->has2fa()) die("Two factor authentication is needed for creating exams");

    $owner = $user->getId();
    $name = htmlspecialchars($_POST["name"]);
    $prize = htmlspecialchars($_POST["prize"]);

    $questions = [];
    $answers = [];
    $correct = [];

    $i = 0;
    while (array_key_exists("question_${i}", $_POST)) {
        $q = $_POST["question_${i}"];
        $a = [$_POST["answer_${i}_0"], $_POST["answer_${i}_1"], $_POST["answer_${i}_2"], $_POST["answer_${i}_3"]];
        $c = $_POST["correct_${i}"];

        array_push($questions, $q);
        array_push($answers, $a);
        array_push($correct, $c);
        $i++;
    }

    $exam = Exam::fromVals($owner, $name, $questions, $answers, $correct, $prize);
    $res = $exam->DB_set();
    if ($res !== false) header("Location: /exam_view.php?id=${res}");
}

?>


<!doctype html>
<html lang="en" dir="ltr">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-0evHe/X+R7YkIZDRvuzKMRqM+OrBnVFBL6DOitfPri4tjfHxaWutUpFmBp4vmVor" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/js/bootstrap.bundle.min.js" integrity="sha384-pprn3073KE6tl6bjs2QrFaJGz5/SUsLqktiwsUTF55Jfv3qYSDhgCecCxMW52nD2" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css" integrity="sha512-KfkfwYDsLkIlwQp6LFnl8zNdLGxu9YAA1QvwINks4PhcElQSvqcyVLLD9aMhXd13uQjoXtEKNosOWaZqXgel0g==" crossorigin="anonymous" referrerpolicy="no-referrer" />

    <title>ExamPortal - Create exam</title>
</head>

<body class="bg-light">

    <nav class="navbar  navbar-expand-lg  bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand btn btn-warning" href="/">
                <i class="fa-solid fa-building-columns"></i> CyberUni - ExamPortal
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarToggler" aria-controls="navbarToggler" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarToggler">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                </ul>
                <form class="d-flex" role="search">
                    <?php
                    if (isset($_SESSION["user"])) {
                        $username = $_SESSION["user"]->getUsername();
                        echo "<button type='button' class='btn btn-sm btn-success mx-2'><i class='fa-solid fa-user'></i> $username</button>";
                        echo "<a class='btn btn-sm btn-danger mx-2' href='logout.php'><i class='fa-solid fa-right-from-bracket'></i> Logout</a>";
                    } else {
                    ?>
                        <a class="btn btn-sm mx-2 btn-success" href="login.php"><i class="fa-solid fa-right-to-bracket"></i> Login</a>
                    <?
                    } ?>
                </form>
            </div>
        </div>

    </nav>


    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-12 col-md-8 text-center">
                <h1><i class="fa-solid fa-building-columns"></i> CyberUni</h1>
                <h3>ExamPortal</h3>
            </div>
        </div>
        <div class="row justify-content-center mt-3">
            <div class="col-12 col-md-8  py-3 border rounded bg-primary text-white">

                <h3><i class="fa-solid fa-file-circle-plus"></i> Create a new exam</h3>

                <form method="POST" class="rounded bg-light p-3 text-dark">

                    <div>
                        <label for="name" class="form-label"><i class="fa-solid fa-file-lines"></i> Exam name</label>
                        <input type="name" class="form-control" id="name" name="name" placeholder="name">
                    </div>

                    <label class="form-label mt-3"><i class='fa-solid fa-circle-question'></i> Questions</label>



                    <?
                    for ($i = 0; $i < 10; $i++) {
                        echo "<hr />";
                        echo "<div class='mt-3'><label for='question_0' class='form-label'>Question #${i}</label><textarea class='form-control' id='question_${i}' name='question_${i}' rows='3'></textarea></div>";
                        echo "<div class='mt-3'><input type='text' class='form-control' id='answer_${i}_0' name='answer_${i}_0' placeholder='Answer A'></div>";
                        echo "<div class='mt-3'><input type='text' class='form-control' id='answer_${i}_1' name='answer_${i}_1' placeholder='Answer B'></div>";
                        echo "<div class='mt-3'><input type='text' class='form-control' id='answer_${i}_2' name='answer_${i}_2' placeholder='Answer C'></div>";
                        echo "<div class='mt-3'><input type='text' class='form-control' id='answer_${i}_3' name='answer_${i}_3' placeholder='Answer D'></div>";
                        echo "<div class='mt-3'><label for='correct_${i}' class=' form-label'>Correct answer</label><select class='form-select' name='correct_${i}'><option value='A'>A</option><option value='B'>B</option><option value='C'>C</option><option value='D'>D</option></select></div>";
                    }
                    ?>



                    <hr />

                    <div class="mt-3">
                        <label for="prize" class="form-label"><i class="fa-solid fa-gift"></i> Special prize</label>
                        <input type="text" class="form-control" id="prize" name="prize" placeholder="prize">
                    </div>


                    <div class="text-center mt-3">
                        <button class="btn btn-success" type="submit">
                            <i class="fa-solid fa-file-circle-plus"></i> Create exam
                        </button>
                    </div>
            </div>
        </div>
    </div>

    <div class="bg-primary">
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-12 col-md-8 text-white ">
                    @ 2022 CyberUni <i class="fa-solid fa-trademark"></i> platform | All rights reserved
                </div>
            </div>
        </div>
    </div>

</body>

</html>