<?php
error_reporting(0);
include 'classes/user.php';
include 'classes/nft.php';
session_start();


if (!isset($_SESSION['user'])) {
    header('Location: /login.php');
    die();
}

if (isset($_POST['title']) && isset($_POST['data']) && isset($_POST['price']) ) {
    if (strlen($_POST['title']) > 50) {
        die('NFT title must be smaller than 50 chars');
    }
    if (strlen($_POST['data']) > 2000) {
        die('NFT data must be smaller than 1000 chars');
    }
    
    $_POST['public'] = isset($_POST['public']) && $_POST['public'] === 'true';

    $nft = new NFT();
    $nft->setNFTData($_POST);
    $nft->setOwner($_SESSION['user']->getId());

    if ($nft->mint()) {
        $url = $nft->getURL();
    } else {
        die('error');
    }
}

?>

<!DOCTYPE html>
<html lang="en" class="h-100">

<head>
    <title>ClosedSea - Minter</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-0evHe/X+R7YkIZDRvuzKMRqM+OrBnVFBL6DOitfPri4tjfHxaWutUpFmBp4vmVor" crossorigin="anonymous" />
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/js/bootstrap.bundle.min.js" integrity="sha384-pprn3073KE6tl6bjs2QrFaJGz5/SUsLqktiwsUTF55Jfv3qYSDhgCecCxMW52nD2" crossorigin="anonymous"></script>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css" integrity="sha512-KfkfwYDsLkIlwQp6LFnl8zNdLGxu9YAA1QvwINks4PhcElQSvqcyVLLD9aMhXd13uQjoXtEKNosOWaZqXgel0g==" crossorigin="anonymous" referrerpolicy="no-referrer" />

    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js" integrity="sha384-7EyYLQZgWBi67fBtVxw60/OWl1kjsfrPFcaU0pp0nAh+i8FD068QogUvg85Ewy1k" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css" integrity="sha512-KfkfwYDsLkIlwQp6LFnl8zNdLGxu9YAA1QvwINks4PhcElQSvqcyVLLD9aMhXd13uQjoXtEKNosOWaZqXgel0g==" crossorigin="anonymous" referrerpolicy="no-referrer" />
</head>

<body class="bg-light h-100 d-flex align-items-center">

    <div class="container">
        <div class="row justify-content-center">
            <div class="col-12 col-lg-6">

                <div class="text-center py-3">
                    <h1><i class="fa-solid fa-ship"></i> ClosedSea</h1>
                </div>

                <div class="bg-white border p-4">
                    <? if (isset($url)) {
                        echo "<div class='text-center mb-3'><a class='btn btn-primary' href='${url}'><i class='fa-solid fa-eye'></i> Check your new NFT!</a></div>\n";
                    } ?>


                    <form method="POST">

                        <h3><i class="fa-solid fa-person-digging"></i> Mint an nft</h3>
                        <hr />
                        <div class="mt-3">
                            <label for="title" class="form-label"><i class="fa-solid fa-heading"></i> Title</label>
                            <input type="text" class="form-control" name="title" placeholder="title">
                        </div>

                        <div class="mt-3">
                            <label for="data" class="form-label"><i class="fa-solid fa-magnifying-glass"></i> Data</label>
                            <input type="text" class="form-control" name="data" placeholder="data">
                        </div>

                        <div class="mt-3">
                            <label for="price" class="form-label"><i class="fa-solid fa-coins"></i> Cost</label>
                            <input type="text" class="form-control" name="price" placeholder="cost">
                        </div>


                        <div class="mt-3 form-check">
                            <input class="form-check-input" type="checkbox" id="public" name="public" value="true" checked>
                            <label class="form-check-label" for="public">
                                <i class="fa-solid fa-eye-low-vision"></i> Public NFT
                            </label>
                        </div>

                        <div class="mt-3 text-center">
                            <button class="btn btn-success w-50" type="submit"><i class="fa-solid fa-person-digging"></i> Mint!</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

</body>

</html>