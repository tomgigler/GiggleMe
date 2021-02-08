<?php
include "login_check.php";
include "header.php";
require_once "DBConnection.php";

date_default_timezone_set($_SESSION['timezone']);
if(isset($_GET['id'])) $msg_id = $_GET['id'];
else $msg_id = substr(md5(time()),0,8);

$db = new DBConnection();
$message = $db->get_message($msg_id);

$channels = array();
$templates = array();
$servers = $db->get_user_guilds();

foreach($servers as $server){
  $server_channels = $db->get_guild_channels($server[0]);
  foreach($server_channels as $channel){
    $channels[$server[0]][] = array(strval($channel[0]), $channel[1]);
  }
  $templates[$server[0]][] = "None";
  $server_templates = $db->get_guild_templates($server[0]);
  foreach($server_templates as $template){
    $templates[$server[0]][] = $template[0];
  }
}

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button class='display_element' onclick=\"edit_button_click()\" >Edit</button>\n";
print "<button class='display_element' onclick=\"deleteMessage('".$msg_id."', 'message')\" >Delete</button>\n";
print "<button class='edit_element' onclick=\"edit_message()\" >Save</button>\n";
print "<button class='edit_element' onclick=\"cancel_button_click()\" >Cancel</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";


print "<table>\n";
if($_GET['action']=='create'){
  print "  <tr>\n";
  print "    <th>Type</th>\n";
  print "    <td id='msg_type'>\n";
  print "      <select id='msg_type_select' style='display:table-cell; width:100%' onchange='message_type_updated()'>\n";
  print "        <option value='message'>Message</option>\n";
  print "        <option value='template'>Template</option>\n";
  print "        <option value='template'>Batch Process</option>\n";
  print "      </select>\n";
  print "    </td>\n";
  print "  </tr>\n";
}

print "  <tr id='message_id_row'>\n";
if($message[4] || $_GET['action']=='create'){
  print "    <th>Message ID</th>\n";
} else {
  print "    <th>Template ID</th>\n";
}
print "    <td>".$msg_id."</td>\n";
print "  </tr>\n";

print "  <tr>\n";
print "    <th>Author</th>\n";
if($_GET['action']=='create'){
  print "    <td>".$_SESSION['username']."</td>\n";
} else {
  print "    <td>".htmlspecialchars($message[1])."</td>\n";
}
print "  </tr>\n";

print "  <tr id='display_server_row'>\n";
print "    <th>Server</th>\n";
print "    <td id='display_server_cell' class='display_element'>".htmlspecialchars($message[2])."</td>\n";
print "    <td id='edit_server_cell' class='edit_element'>\n";
print "      <select id='server' name='server' style='display:table-cell; width:100%' onchange='server_select_updated()'>\n";
foreach($servers as $server){
  print "        <option value='".$server[0]."'>$server[1]</option>\n";
}
print "      </select>\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='display_channel_row'>\n";
print "    <th>Channel</th>\n";
print "    <td id='display_channel_cell' class='display_element'>".htmlspecialchars($message[3])."</td>\n";
print "    <td id='edit_channel_cell' class='edit_element'>\n";
print "      <select id='channel' name='channel' style='display:table-cell; width:100%' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='display_delivery_time_row'>\n";
print "    <th>Delivery Time</th>\n";
print "    <td id='display_delivery_time_cell' class='display_element'>".date("g:i:s A D M j, Y T",$message[4])."</td>\n";
print "    <td id='edit_delivery_time_cell' class='edit_element'><input id='delivery_time' type=datetime-local /></td>\n";
print "  </tr>\n";

print "  <tr id='edit_from_template_row' class='edit_element'>\n";
print "    <th>From Template</th>\n";
print "    <td>\n";
print "      <select id='from_template' style='display:table-cell; width:100%' onchange='update_content_from_template()' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='display_repeats_row'>\n";
print "    <th>Repeats</th>\n";
print "    <td id='display_repeats_cell' class='display_element'>".$message[5]."</td>\n";
print "    <td id='edit_repeats_cell' class='edit_element'>\n";
print "      <select id='repeats_select' style='display:table-cell; width:50%' onchange='update_repeats_select()'>\n";
print "        <option value='None'>None</option>\n";
print "        <option value='minutes'>minutes</option>\n";
print "        <option value='hours'>hours</option>\n";
print "        <option value='daily'>daily</option>\n";
print "        <option value='weekly'>weekly</option>\n";
print "        <option value='monthly'>monthly</option>\n";
print "      </select>\n";
print "      <input id='repeats_num' style='display:table-cell; width:20%' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='edit_skip_if_row' class='edit_element'>\n";
print "    <th>Skip if</th>\n";
print "    <td>\n";
print "      <input id='skip_if_checkbox' type='checkbox' onchange='toggle_skip_if_num()' />\n";
print "      <input id='skip_if_num' style='display:table-cell; width:20%' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='display_repeat_until_row'>\n";
print "    <th>Repeat Until</th>\n";
print "    <td id='display_repeat_until_cell' class='display_element'>".date("g:i:s A D M j, Y T",$message[6])."</td>\n";
print "    <td id='edit_repeat_until_cell' class='edit_element'>\n";
print "      <input id='repeat_until_checkbox' type='checkbox' onchange='toggle_repeat_until_datetime()' />\n";
print "      <input id='repeat_until_datetime' type=datetime-local />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='display_description_row'>\n";
print "    <th>Description</th>\n";
print "    <td id='display_description_cell' class='display_element'>".htmlspecialchars($message[7])."</td>\n";
print "    <td  id='edit_description_cell' class='edit_element'><input id='description' style='display:table-cell; width:100%' /></td>\n";
print "  </tr>\n";

print "</table>\n";

print "</center><br>\n";
print "<div id='display_content_div' class='display_element content-div'>\n";
print "  <pre>".htmlspecialchars($message[8])."</pre>\n";
print "</div>\n";

include "footer.php";

print "<script>\n";
$js_channels = json_encode($channels);
echo "var channels = ". $js_channels . ";\n";
$js_templates = json_encode($templates);
echo "var templates = ". $js_templates . ";\n";

if($_GET['action']=='create' || $_GET['action']=='edit'){
  print "$('.display_element').toggle(false)\n";
  print "$('.edit_element').toggle(true)\n";
} else {
  print "$('.display_element').toggle(true)\n";
  print "$('.edit_element').toggle(false)\n";
}
if($_GET['action']=='create') print "var creating_new_message=true\n";
else print "var creating_new_message=false\n";

print "$(function(){\n";
print "  load_message_page('".$_GET['action']."', '".$message[6]."');\n";
print "});\n";
print "</script>\n";
?>
