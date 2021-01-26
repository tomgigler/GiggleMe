<?php
include "login_check.inc";
include "header.inc";
include "settings.inc";

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";
print "Template " . $_GET['id'] . "\n";

date_default_timezone_set($_SESSION['timezone']);
$connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
$connection->set_charset("utf8mb4");
$messages = $connection->query("SELECT content FROM messages WHERE id = '".$_GET['id']."'");

print "</center>\n";
while($row = $messages->fetch_row()) {
  print "<pre>".htmlspecialchars($row[0])."</pre>\n";
}

$connection->close();
?>
