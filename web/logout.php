<?php

   session_start();
   if (isset($_COOKIE['USER']))
     setcookie('USER');
   session_destroy();

  header("Location: index.php");
  exit;

?>
