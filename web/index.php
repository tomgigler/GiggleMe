<?php

session_start();

include "settings.php";

if (isset($_SESSION['user_id']) && isset($_SESSION['username']))
{
    header("Location: home.php");
    exit();
}
elseif (isset($_COOKIE['user_id']) && isset($_COOKIE['username']))
{
    $_SESSION['user_id'] = $_COOKIE['user_id'];
    $_SESSION['username'] = $_COOKIE['username'];
    header("Location: home.php");
    exit();
}
else
{
    include "header.php";

    print "<br><br>\n";

    print "<center>\n";
    print "   <button onclick='login_click()'>Login</button><br><br>\n";
    print "   <input type='checkbox' id='persist' />&nbsp;<b class='footer'>Keep me signed in</b>\n";
    include "footer.php";
}
?> 
<script>
<?php print "auth_url=\"https://discord.com/api/oauth2/authorize?client_id=".$CLIENT_ID."&response_type=code&scope=identify\"\n"; ?>
<?php print "redir_url=\"&redirect_uri=https%3A%2F%2F".$_SERVER['HTTP_HOST'].rtrim(dirname($_SERVER['PHP_SELF']), '/\\')."%2Fget_token.php\"\n"; ?>
function login_click(){
  location.href=auth_url+redir_url+'&state='+$('#persist').is(":checked");
}
</script>
