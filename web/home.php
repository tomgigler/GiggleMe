<?php
include "login_check.inc";
include "header.inc";
include "settings.inc";
require_once "DBConnection.php";

print "<center>\n";
print "<button onclick=\"alert('TODO: Implement New Message')\">New Message</button>\n";
print "<button onclick=\"location.href='change_password.php'\" >Change Password</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";

date_default_timezone_set($_SESSION['timezone']);

$db = new DBConnection();
$messages = $db->get_messages();

$templates = $db->get_templates();

?>
<br>
<?php
if(count($messages)){
  print "<table border=1>\n";
  print "  <tr><th colspan=8><b>Messages</b></th></tr>\n";
  print "  <tr>\n";
  print "    <th>Message ID</th>\n";
  print "    <th>Server Name</th>\n";
  print "    <th>Channel</th>\n";
  print "    <th>Author</th>\n";
  print "    <th>Delivery Time</th>\n";
  print "    <th>Repeats</th>\n";
  print "    <th>Repeat Until</th>\n";
  print "    <th>Description</th>\n";
  print "  </tr>\n";
  foreach($messages as $row) {
    print "  <tr>\n";
    // 7:00:00 PM Mon Jan 25, 2021 PST
    $delivery_time = date("g:i:s A D M j, Y T",$row[4]);
    if($row[6]) { $repeat_until = date("g:i:s A D M j, Y T",$row[6]); } else { $repeat_until = $row[6]; }
    print "    <td class='link-cell' onclick=\"location.href='message.php?id=$row[0]'\">$row[0]</td>\n";
    print "    <td>$row[1]</td>\n";
    print "    <td>$row[2]</td>\n";
    print "    <td>$row[3]</td>\n";
    print "    <td>$delivery_time</td>\n";
    print "    <td>$row[5]</td>\n";
    print "    <td>$repeat_until</td>\n";
    print "    <td>$row[7]</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
  print "<br><br>\n";
}

if(count($templates)){
  print "<table border=1>\n";
  print "  <tr><th colspan=5><b>Templates</b></th></tr>\n";
  print "  <tr>\n";
  print "    <th>Template ID</th>\n";
  print "    <th>Server Name</th>\n";
  print "    <th>Channel</th>\n";
  print "    <th>Author</th>\n";
  print "    <th>Description</th>\n";
  print "  </tr>\n";
  foreach($templates as $row) {
    print "  <tr>\n";
    print "    <td class='link-cell' onclick=\"location.href='template.php?id=$row[0]'\">$row[0]</td>\n";
    print "    <td>$row[1]</td>\n";
    print "    <td>$row[2]</td>\n";
    print "    <td>$row[3]</td>\n";
    print "    <td>$row[4]</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
}

?>
</center>
</body>
</html>
