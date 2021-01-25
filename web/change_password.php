<?php

  require_once "Login.php";
  require_once "User.php";

   session_start();
   $host = $_SERVER['HTTP_HOST'];
   $uri = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');

   if(isset($_POST['CURRENT_PASS']))
   {
      $log = new Login();
      if(!$log->verify($_SESSION['USER'], $_POST['CURRENT_PASS']))
      {
         $_SESSION['message'] = "<br><br><font color='red'><b>--Incorrect password--</b></font>\n";
      }
      else if($_POST['NEW_PASS'] != $_POST['CONFIRM_PASS'])
      {
         $_SESSION['message'] = "<br><br><font color='red'><b>--Passwords do not match--</b></font>\n";
      }
      else
      {
         $user = new User();
         $user->change_password($_POST['NEW_PASS']);
         $_SESSION['message'] = "<br><br><font color='green'><b>Changed password for user ".$_SESSION['USER']."</b></font>\n";
      }
   }


   include "login_check.inc";
   include "header.inc";

   print "<center>\n";
   print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
   print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";

   if(isset($_SESSION['message'])){
      print $_SESSION['message'];
      unset($_SESSION['message']);
   } else {
      print "<br>\n";
      print "<br>\n";
      print "<br>\n";
   }

   print "</center>\n";

   print "      <center>\n";
   print "      <h2>Change Password</h2>\n";
   print "      <form name='form' method='POST' enctype='multipart/form-data'>\n";
   print "      <table border=1>\n";
   print "      <tr>\n";
   print "      <td align=right>\n";
   print "      <b>Current Password:</b>\n";
   print "      </td>\n";
   print "      <td>\n";
   print "      <input type='password' name='CURRENT_PASS'/>\n";
   print "      </td>\n";
   print "      </tr>\n";
   print "      <tr>\n";
   print "      <td align=right>\n";
   print "      <b>New Password:</b>\n";
   print "      </td>\n";
   print "      <td>\n";
   print "      <input type='password' name='NEW_PASS'/>\n";
   print "      </td>\n";
   print "      </tr>\n";
   print "      <tr>\n";
   print "      <td align=right>\n";
   print "      <b>Confirm Password:</b>\n";
   print "      </td>\n";
   print "      <td>\n";
   print "      <input type='password' name='CONFIRM_PASS'/>\n";
   print "      </td>\n";
   print "      </tr>\n";
   print "      <tr>\n";
   print "      <td>\n";
   print "      </td>\n";
   print "      <td>\n";
   print "      <input type='submit' value='Change Password'/>\n";
   print "      </td>\n";
   print "      </tr>\n";
   print "      </table>\n";
   print "      </form>\n";
   print "      </center>\n";

   // include "footer.inc";

   print "</body>\n";
   print "</html>";

?>
