<?php

   session_start();
   if (isset($_COOKIE[$_SESSION['DATABASE']]))
     setcookie($_SESSION['DATABASE']);
   session_destroy();

  header("Location: index.php");
  exit;

?>
