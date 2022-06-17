<?php

require_once("classes/user.php");
session_start();
?>

<!doctype html>
<html lang="en" dir="ltr">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-0evHe/X+R7YkIZDRvuzKMRqM+OrBnVFBL6DOitfPri4tjfHxaWutUpFmBp4vmVor" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/js/bootstrap.bundle.min.js" integrity="sha384-pprn3073KE6tl6bjs2QrFaJGz5/SUsLqktiwsUTF55Jfv3qYSDhgCecCxMW52nD2" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css" integrity="sha512-KfkfwYDsLkIlwQp6LFnl8zNdLGxu9YAA1QvwINks4PhcElQSvqcyVLLD9aMhXd13uQjoXtEKNosOWaZqXgel0g==" crossorigin="anonymous" referrerpolicy="no-referrer" />

    <title>ExamPortal - Homepage</title>
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
                <h3><i class="fa-solid fa-chalkboard-user"></i> Available services:</h3>
                <div class="list-group">
                    <a class="list-group-item list-group-item-action" href="exam_list.php"><i class="fa-solid fa-list-check"></i> List all exams</a>
                    <?php
                    if (isset($_SESSION["user"]) and $_SESSION["user"]->has2fa()) { ?>
                        <a class="list-group-item list-group-item-action" href="exam_create.php"><i class="fa-solid fa-file-circle-plus"></i> Create a new exam</a>
                    <? } ?>
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