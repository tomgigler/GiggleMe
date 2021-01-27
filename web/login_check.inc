<?php
   include "settings.inc";

   session_start();

   if (!isset($_SESSION['USER']) || $_SESSION['DATABASE'] != $db_name) 
   {
      $host = $_SERVER['HTTP_HOST'];
      $uri = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
      header("Location: http://$host$uri/index.php");
      exit;
   }
?> 
