<?php
error_reporting(0);
include 'classes/user.php';
session_start();

if (isset($_POST['username']) && isset($_POST['password'])) {
  try {
    $user = new User($_POST['username'], $_POST['password']);
    $_SESSION['user'] = $user;
    header('Location: /index.php');
    die();
  } catch (Exception $e) {
    $error = 'Wrong username or password';
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



        <!-- Login Form -->
        <form method="POST" class="bg-white border p-4">

          <h3><i class="fa-solid fa-right-to-bracket"></i> Login</h3>
          <hr />

          <?php
          if (isset($error)) {
          ?>
            <div class="alert alert-danger mt-3">
              <i class="fa-solid fa-triangle-exclamation"></i> <?= $error ?>
            </div>
          <?php
          }
          ?>

          <div class="mt-3">
            <label for="username" class="form-label"><i class="fa-solid fa-user"></i> Login</label>
            <input type="text" id="login" class="form-control" name="username" placeholder="login">
          </div>

          <div class="mt-3">
            <label for="password" class="form-label"><i class="fa-solid fa-asterisk"></i> Password</label>
            <input type="text" id="password" class="form-control" name="password" placeholder="password">
          </div>

          <div class="mt-3 text-center">
            <button class="btn btn-success w-50" type="submit">
              <i class="fa-solid fa-right-to-bracket"></i> Login
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>




</body>

</html>