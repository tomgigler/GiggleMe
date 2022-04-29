<?php
include "login_check.php";
include "header.php";
include "settings.php";
require_once "Message.php";
require_once "DBConnection.php";

print "<center>\n";
print "<button id='new_message_button' onclick=\"location.href='message_page.php?action=create'\">New Message</button>\n";
print "<button id='custom_channels_button' onclick=\"location.href='custom_channels.php'\" >Custom Channels</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";

if(isset($_SESSION['message']))
{
  print $_SESSION['message'];
  unset($_SESSION['message']);
} else {
  print "<br><br>\n";
}

date_default_timezone_set($_SESSION['timezone']);

$messages = Message::get_messages();

print "<br>\n";

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
  foreach($messages as $message) {
    if($message->message_type() != 'message') continue;
    print "  <tr class='link-row' onclick=\"location.href='message_page.php?id=$message->id'\">\n";
    // 7:00:00 PM Mon Jan 25, 2021 PST
    print "    <td>$message->id</td>\n";
    print "    <td>".htmlspecialchars($message->server)."</td>\n";
    print "    <td>".htmlspecialchars($message->channel)."</td>\n";
    print "    <td>".htmlspecialchars($message->author)."</td>\n";
    print "    <td>$message->delivery_time_format</td>\n";
    print "    <td>$message->repeats</td>\n";
    print "    <td>$message->repeat_until_format</td>\n";
    print "    <td>".htmlspecialchars($message->description)."</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
  print "<br><br>\n";
}

if(count($messages)){
  print "<table border=1>\n";
  print "  <tr><th colspan=5><b>Templates</b></th></tr>\n";
  print "  <tr>\n";
  print "    <th>Template ID</th>\n";
  print "    <th>Server Name</th>\n";
  print "    <th>Channel</th>\n";
  print "    <th>Author</th>\n";
  print "    <th>Description</th>\n";
  print "  </tr>\n";
  foreach($messages as $template) {
    if($template->message_type() != 'template') continue;
    print "  <tr class='link-row' onclick=\"location.href='message_page.php?id=$template->id'\">\n";
    print "    <td>$template->id</td>\n";
    print "    <td>".htmlspecialchars($template->server)."</td>\n";
    print "    <td>".htmlspecialchars($template->channel)."</td>\n";
    print "    <td>".htmlspecialchars($template->author)."</td>\n";
    print "    <td>".htmlspecialchars($template->description)."</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
  print "<br><br>\n";
}

if(count($messages)){
  print "<table border=1>\n";
  print "  <tr><th colspan=6><b>AutoReplies</b></th></tr>\n";
  print "  <tr>\n";
  print "    <th>AutoReply ID</th>\n";
  print "    <th>Server Name</th>\n";
  print "    <th>Trigger</th>\n";
  print "    <th>Wildcard</th>\n";
  print "    <th>Author</th>\n";
  print "    <th>Description</th>\n";
  print "  </tr>\n";
  foreach($messages as $autoreply) {
    if($autoreply->message_type() != 'autoreply') continue;
    print "  <tr class='link-row' onclick=\"location.href='message_page.php?id=$autoreply->id'\">\n";
    print "    <td>$autoreply->id</td>\n";
    print "    <td>".htmlspecialchars($autoreply->server)."</td>\n";
    print "    <td>".htmlspecialchars($autoreply->repeats)."</td>\n";
    if($autoreply->special_handling == 1)
      print "    <td>True</td>\n";
    else
      print "    <td>False</td>\n";
    print "    <td>".htmlspecialchars($autoreply->author)."</td>\n";
    print "    <td>".htmlspecialchars($autoreply->description)."</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
}

$db = new DBConnection();
if(!$db->get_user_guilds()){
  print "<br><br><br>\n";
  print "<div class='footer'>\n";
  print "<center>\n";
  print "Hi " . $_SESSION['username'] . "!<br><br>\n";
  print "It looks like you don't have access to anything here<br><br>If you've already invited the " .
      "<a href='https://discord.com/api/oauth2/authorize?client_id=".$CLIENT_ID."&permissions=477248&scope=bot'>".$CLIENT_NAME."</a> bot to your server, DM the bot to request access\n";
  print "</center>\n";
  print "</div>\n";
  print "<script>\n";
  print "$('#new_message_button').toggle(false)\n";
  print "$('#custom_channels_button').toggle(false)\n";
  print "</script>\n";
}

?>
