<?php
   session_start();
   if (isset($_SESSION['USER']) || isset($_SESSION['PASS']))
   {
      $message = "    <font color='green'><b>You have been successfully logged out.</b></font>\n";
   }
   $_SESSION = array();
   if (isset($_COOKIE[session_name()]))
     setcookie(session_name(), '', time()-42000, '/');
   session_destroy();

  $host = $_SERVER['HTTP_HOST'];
  $uri = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
  header("Location: index.php");
  exit;

?>


