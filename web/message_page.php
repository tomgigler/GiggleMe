<?php
include "login_check.php";
include "header.php";
require_once "DBConnection.php";
require_once "Message.php";

$db = new DBConnection();
if(!$db->get_user_guilds()){
  header("Location: home.php");
  exit;
}

date_default_timezone_set($_SESSION['timezone']);
if(isset($_GET['id'])) $msg_id = $_GET['id'];
else $msg_id = substr(md5(time()),0,8);

$message = Message::get_message_by_id($msg_id);

$channels = array();
$templates = array();
$servers = $db->get_user_guilds();

foreach($servers as $server){
  $server_channels = $db->get_guild_channels($server[0]);
  foreach($server_channels as $channel){
    $channels[$server[0]][] = array(strval($channel[0]), $channel[1]);
  }
  $templates[$server[0]][] = ["None", ""];
  $server_templates = $db->get_guild_templates($server[0]);
  foreach($server_templates as $template){
    $templates[$server[0]][] = [$template[0],": $template[1]"];
  }
}

print "<center>\n";
print "<button onclick=\"window.location.href='home.php'\" >Home</button>\n";
print "<button class='display_element' onclick=\"edit_button_click()\" >Edit</button>\n";
print "<button class='display_element' onclick=\"deleteMessage('".$msg_id."', 'message')\" >Delete</button>\n";
print "<button class='edit_element' onclick=\"save_message()\" >Save</button>\n";
print "<button class='edit_element' onclick=\"cancel_button_click()\" >Cancel</button>\n";
print "<button onclick=\"window.location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";


print "<table>\n";
print "  <tr id='message_type_row'>\n";
print "    <th>Type</th>\n";
print "    <td id='msg_type'>\n";
print "      <select id='message_type_select' style='display:table-cell; width:100%' onchange='message_type_updated()'>\n";
print "        <option selected value='message'>Message</option>\n";
print "        <option value='template'>Template</option>\n";
print "        <option value='batch'>Batch Process</option>\n";
print "        <option value='autoreply'>Auto Reply</option>\n";
print "      </select>\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='message_id_row'>\n";
print "    <th id='message_id_header_cell'>Message ID</th>\n";
print "    <td id='message_id_cell'>".$msg_id."</td>\n";
print "  </tr>\n";

print "  <tr>\n";
print "    <th>Author</th>\n";
if($_GET['action']=='create'){
  print "    <td>".$_SESSION['username']."</td>\n";
} else {
  print "    <td>".htmlspecialchars($message->author)."</td>\n";
}
print "  </tr>\n";

print "  <tr id='server_row'>\n";
print "    <th>Server</th>\n";
print "    <td id='display_server_cell' class='display_element'>".htmlspecialchars($message->server)."</td>\n";
print "    <td id='edit_server_cell' class='edit_element'>\n";
print "      <select id='server_select' style='display:table-cell; width:100%' onchange='server_select_updated()'>\n";
foreach($servers as $server){
  print "        <option value='".$server[0]."'>$server[1]</option>\n";
}
print "      </select>\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='channel_row'>\n";
print "    <th>Channel</th>\n";
print "    <td id='display_channel_cell' class='display_element'>".htmlspecialchars($message->channel)."</td>\n";
print "    <td id='edit_channel_cell' class='edit_element'>\n";
print "      <select id='channel_select' style='display:table-cell; width:100%' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='delivery_time_row'>\n";
print "    <th>Delivery Time</th>\n";
print "    <td id='display_delivery_time_cell' class='display_element'>".$message->delivery_time_format."</td>\n";
print "    <td id='edit_delivery_time_cell' class='edit_element'><input id='delivery_time' type=datetime-local /></td>\n";
print "  </tr>\n";

print "  <tr id='from_template_row'>\n";
print "    <th>From Template</th>\n";
print "    <td>\n";
print "      <select id='from_template' style='display:table-cell; width:100%' onchange='update_content_from_template()' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='repeats_row'>\n";
print "    <th id='repeats_header_cell'>Repeats</th>\n";
print "    <td id='display_repeats_cell' class='display_element'>".$message->repeats."</td>\n";
print "    <td id='edit_repeats_cell' class='edit_element'>\n";
print "      <select id='repeats_select' style='display:table-cell; width:50%' onchange='update_repeats_select()'>\n";
print "        <option selected value='None'>None</option>\n";
print "        <option value='minutes'>minutes</option>\n";
print "        <option value='hours'>hours</option>\n";
print "        <option value='daily'>daily</option>\n";
print "        <option value='weekly'>weekly</option>\n";
print "        <option value='monthly'>monthly</option>\n";
print "      </select>\n";
print "      <input id='repeats_num' style='display:table-cell; width:20%' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='trigger_row' hidden='true'>\n";
print "    <th id='trigger_header_cell'>Trigger</th>\n";
print "    <td id='display_trigger_cell' class='display_element'>".$message->repeats."</td>\n";
print "    <td id='edit_trigger_cell' class='edit_element'>\n";
print "      <input id='trigger_text' style='display:table-cell;' value='".$message->repeats."'/>\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='skip_if_row'>\n";
print "    <th>Skip if</th>\n";
print "    <td>\n";
print "      <input id='skip_if_checkbox' type='checkbox' onchange='toggle_skip_if_num()' />\n";
print "      <input id='skip_if_num' style='display:table-cell; width:20%' />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='repeat_until_row'>\n";
print "    <th>Repeat Until</th>\n";
print "    <td id='display_repeat_until_cell' class='display_element'>";
if($message->repeat_until) print $message->repeat_until_format;
print "</td>\n";
print "    <td id='edit_repeat_until_cell' class='edit_element'>\n";
print "      <input id='repeat_until_checkbox' type='checkbox' onchange='toggle_repeat_until_datetime()' />\n";
print "      <input id='repeat_until_datetime' type=datetime-local />\n";
print "    </td>\n";
print "  </tr>\n";

print "  <tr id='description_row'>\n";
print "    <th>Description</th>\n";
print "    <td id='display_description_cell' class='display_element'>".htmlspecialchars($message->description)."</td>\n";
print "    <td  id='edit_description_cell' class='edit_element'><input id='description' style='display:table-cell; width:100%' /></td>\n";
print "  </tr>\n";

print "  <tr id='special_handling_row'>\n";
if($message->delivery_time == -2) print "    <th id='special_handling_header'>Wildcard</th>\n";
elseif($message->special_handling == 2) print "    <th id='special_handling_header'>Set Topic</th>\n";
elseif($message->special_handling == 3) print "    <th id='special_handling_header'>Set Channel Name</th>\n";
else print "    <th id='special_handling_header'>Pin</th>\n";
print "    <td id='display_special_handling_cell' class='display_element'>";
if($message->special_handling > 0) print "True";
else print "False";
print "</td>\n";
print "    <td id='edit_special_handling_cell' class='edit_element'>\n";
print "      <input id='pin_message_checkbox' type='checkbox' ";
if($message->special_handling == 1) print "checked ";
print "/>\n";
print "    </td>\n";
print "  </tr>\n";

print "</table>\n";
print "<br>\n";
print "<p class='display_element' style='font-family:\"Calibri\"'><input type='checkbox' id='show_as_command_chkbx' onclick='show_as_command_click()'/>&nbsp;Show as command</p>\n";
print "<textarea id='edit_content' class='edit_element' cols='124' rows='24' maxlength='1992'>\n";
print $message->content;
print "</textarea>\n";
print "</center>";
print "<div id='display_content_div' class='display_element content-div'>\n";
print "  <pre id='display_content_pre'>".htmlspecialchars($message->content)."</pre>\n";
print "</div>\n";

print "<script>\n";
$js_channels = json_encode($channels);
echo "var channels = ". $js_channels . ";\n";
$js_templates = json_encode($templates);
echo "var templates = ". $js_templates . ";\n";
print "var guild_id = '" . $message->guild_id . "'\n";
print "var channel_id = '" . $message->delivery_channel_id . "'\n";
print "var delivery_time_java_format = '" . $message->delivery_time_java_format . "'\n";
print "var repeat_until_java_format = '" . $message->repeat_until_java_format . "'\n";

print "var repeat_frequency = '" . $message->repeat_frequency . "'\n";
print "var repeat_frequency_num = '" . $message->repeat_frequency_num . "'\n";
print "var repeat_skip_if = '" . $message->repeat_skip_if . "'\n";

if(!$_GET['action']=='create'){
  if(!$message->delivery_time){
    print "$('#message_id_header_cell').text('Template ID')\n";
    print "$('#delivery_time_row').toggle(false)\n";
    print "$('#message_type_select').val('template')\n";
  } elseif($message->delivery_time == -2){
    print "$('#delivery_time_row').hide()\n";
    print "$('#message_id_header_cell').text('AutoReply ID')\n";
    print "$('#trigger_row').show()\n";
    print "$('skip_if_row').hide()\n";
    print "$('#repeats_row').hide()\n";
    print "$('#channel_row').hide()\n";
    print "$('#message_type_select').val('autoreply')\n";
  }
  print "$('#message_type_row').toggle(false)\n";
}

if($_GET['action']=='create' || $_GET['action']=='edit'){
  print "$('.display_element').toggle(false)\n";
  print "$('.edit_element').toggle(true)\n";
} else {
  print "$('.display_element').toggle(true)\n";
  print "$('.edit_element').toggle(false)\n";
  print "$('#from_template_row').toggle(false)\n";
}
if($_GET['action']=='create') print "var creating_new_message=true\n";
else print "var creating_new_message=false\n";

print "$(function(){\n";
print "  load_message_page('".$_GET['action']."', '".$message->repeat_until."');\n";
print "});\n";
?>
setInputFilter(document.getElementById("repeats_num"), function(value) {
  return /^\d?\d?\d?$/.test(value); // Allow digits and '.' only, using a RegExp
});
setInputFilter(document.getElementById("skip_if_num"), function(value) {
  return /^\d?\d?\d?$/.test(value); // Allow digits and '.' only, using a RegExp
});
</script>
