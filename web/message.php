<?php
include "login_check.php";
include "header.php";
require_once "DBConnection.php";

date_default_timezone_set($_SESSION['timezone']);
$msg_id = $_GET['id'];

$db = new DBConnection();
$message = $db->get_message_display($msg_id);

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button onclick=\"location.href='edit_message.php?id=".$msg_id."'\" >Edit</button>\n";
if($message[5]){
  print "<button onclick=\"deleteMessage('".$msg_id."', 'message')\" >Delete</button>\n";
} else {
  print "<button onclick=\"deleteMessage('".$msg_id."', 'template')\" >Delete</button>\n";
}
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";


print "<table>\n";
print "  <tr>\n";
if($message[5]){
  print "    <th>Message ID</th>\n";
} else {
  print "    <th>Template ID</th>\n";
}
print "    <td>".$message[0]."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Author</th>\n";
print "    <td>".htmlspecialchars($message[1])."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Server</th>\n";
print "    <td>".htmlspecialchars($message[2])."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Channel</th>\n";
print "    <td>".htmlspecialchars($message[3])."</td>\n";
print "  </tr>\n";
if($message[4]){
  print "  <tr>\n";
  print "    <th>Delivery Time</th>\n";
  print "    <td>".date("g:i:s A D M j, Y T",$message[4])."</td>\n";
  print "  </tr>\n";
}
if($message[5]){
  print "  <tr>\n";
  print "    <th>Repeats</th>\n";
  print "    <td>".$message[5]."</td>\n";
  print "  </tr>\n";
  if($message[6]){
    print "  <tr>\n";
    print "    <th>Repeat Until</th>\n";
    print "    <td>".date("g:i:s A D M j, Y T",$message[6])."</td>\n";
    print "  </tr>\n";
  }
}
if($message[7]){
  print "  <tr>\n";
  print "    <th>Description</th>\n";
  print "    <td>".htmlspecialchars($message[7])."</td>\n";
  print "  </tr>\n";
}
print "</table>\n";
print "</center><br>\n";
print "<div class='content-div'>\n";
print "  <pre>".htmlspecialchars($message[8])."</pre>\n";
print "</div>\n";
$connection->close();
?>
