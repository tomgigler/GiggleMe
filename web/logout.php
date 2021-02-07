<?php
   session_start();
   session_unset();
   session_destroy();

   setcookie("user_id", "", time() - 60 * 60);
   setcookie("username", "", time() - 60 * 60);
   setcookie("avatar", "", time() - 60 * 60);

   header("Location: index.php");
   exit();
?>
