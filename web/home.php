<?php
include "login_check.php";
include "header.php";
include "settings.php";
require_once "Message.php";
require_once "DBConnection.php";

print "<center>\n";
?>
<!--Dayspedia.com widget--><div class="DPDC" cityid="2007" lang="en" id="dayspedia_widget_13540eca4615397a" host="https://dayspedia.com" ampm="true" nightsign="true" sun="false">

	<style media="screen" id="dayspedia_widget_13540eca4615397a_style">
				/*COMMON*/
		.DPDC{display:table;position:relative;box-sizing:border-box;font-size:100.01%;font-style:normal;font-family:Arial;background-position:50% 50%;background-repeat:no-repeat;background-size:cover;overflow:hidden;user-select:none}
		.DPDCh,.DPDCd{width:fit-content;line-height:1.4}
		.DPDCh{margin-bottom:1em}
		.DPDCd{margin-top:.24em}
		.DPDCt{line-height:1}
		.DPDCth,.DPDCtm,.DPDCts{display:inline-block;vertical-align:text-top;white-space:nowrap}
		.DPDCth{min-width:1.15em}
		.DPDCtm,.DPDCts{min-width:1.44em}
		.DPDCtm::before,.DPDCts::before{display:inline-block;content:':';vertical-align:middle;margin:-.34em 0 0 -.07em;width:.32em;text-align:center;opacity:.72;filter:alpha(opacity=72)}
		.DPDCt12{display:inline-block;vertical-align:text-top;font-size:40%}
		.DPDCdm::after{content:' '}
		.DPDCda::after{content:', '}
		.DPDCdt{margin-right:.48em}
		.DPDCtn{display:inline-block;position:relative;width:13px;height:13px;border:2px solid;border-radius:50%;overflow:hidden}
		.DPDCtn>i{display:block;content:'';position:absolute;right:33%;top:-5%;width:85%;height:85%;border-radius:50%}
		.DPDCs{margin:.96em 0 0 -3px;font-size:90%;line-height:1;white-space:nowrap}
		.DPDCs sup{padding-left:.24em;font-size:65%}
		.DPDCsl::before,.DPDCsl::after{display:inline-block;opacity:.4}
		.DPDCsl::before{content:'~';margin:0 .12em}
		.DPDCsl::after{content:'~';margin:0 .24em}
		.DPDCs svg{display:inline-block;vertical-align:bottom;width:1.2em;height:1.2em;opacity:.48}
		/*CUSTOM*/
		
		.DPDC{width:auto;padding:24px;background-color:#ffffff;border:1px solid #343434;border-radius:8px} /* widget width, padding, background, border, rounded corners */
		.DPDCh{color:#007DBF;font-weight:normal} /* headline color, font-weight*/
		.DPDCt,.DPDCd{color:#343434;font-weight:bold} /* time & date color, font-weight */
		.DPDCtn{border-color:#343434} /* night-sign color = time & date color */
		.DPDCtn>i{background-color:#343434} /* night-sign color = time & date color */
		.DPDCt{font-size:48px} /* time font-size */
		.DPDCh,.DPDCd{font-size:16px} /* headline & date font-size */
	</style>

	<a class="DPl" href="https://dayspedia.com/time/us/Redlands/" target="_blank" style="display:block!important;text-decoration:none!important;border:none!important;cursor:pointer!important;background:transparent!important;line-height:0!important;text-shadow:none!important;position:absolute;z-index:1;top:0;right:0;bottom:0;left:0">
		<svg xmlns="http://www.w3.org/2000/svg" viewbox="0 0 16 16" style="position:absolute;right:8px;bottom:0;width:16px;height:16px">
			<path style="fill:/*defined*/#007DBF" d="M0,0v16h1.7c-0.1-0.2-0.1-0.3-0.1-0.5c0-0.9,0.8-1.6,1.6-1.6c0.9,0,1.6,0.8,1.6,1.6c0,0.2,0,0.3-0.1,0.5h1.8 c-0.1-0.2-0.1-0.3-0.1-0.5c0-0.9,0.8-1.6,1.6-1.6s1.6,0.8,1.6,1.6c0,0.2,0,0.3-0.1,0.5h1.8c-0.1-0.2-0.1-0.3-0.1-0.5 c0-0.9,0.8-1.6,1.6-1.6c0.9,0,1.6,0.8,1.6,1.6c0,0.2,0,0.3-0.1,0.5H16V0H0z M4.2,8H2V2h2.2c2.1,0,3.3,1.3,3.3,3S6.3,8,4.2,8z M11.4,6.3h-0.8V8H9V2h2.5c1.4,0,2.4,0.8,2.4,2.1C13.9,5.6,12.9,6.3,11.4,6.3z M4.4,3.5H3.7v3h0.7C5.4,6.5,6,6,6,5 C6,4.1,5.4,3.5,4.4,3.5z M11.3,3.4h-0.8V5h0.8c0.6,0,0.9-0.3,0.9-0.8C12.2,3.7,11.9,3.4,11.3,3.4z">
			</path>
		</svg>
		<span title="DaysPedia.com" style="position:absolute;right:28px;bottom:6px;height:10px;width:60px;overflow:hidden;text-align:right;font:normal 10px/10px Arial,sans-serif!important;color:/*defined*/#007DBF">Powered&nbsp;by DaysPedia.com</span>
	</a>
	<div class="DPDCh">Current Time in Redlands</div>
	<div class="DPDCt">
		<span class="DPDCth">05</span><span class="DPDCtm">24</span><span class="DPDCts">59</span><span class="DPDCt12">pm</span>
	</div>
	<div class="DPDCd">
		<span class="DPDCdt">Wed, June 29</span><span class="DPDCtn" style="display: none;"><i></i></span>
	</div>
	
	<div class="DPDCs" style="display:none">
		<span class="DPDCsr">
			<svg xmlns="http://www.w3.org/2000/svg" viewbox="0 0 24 24"><path d="M12,4L7.8,8.2l1.4,1.4c0,0,0.9-0.9,1.8-1.8V14h2c0,0,0-3.3,0-6.2l1.8,1.8l1.4-1.4L12,4z"></path><path d="M6.8,15.3L5,13.5l-1.4,1.4l1.8,1.8L6.8,15.3z M4,21H1v2h3V21z M20.5,14.9L19,13.5l-1.8,1.8l1.4,1.4L20.5,14.9z M20,21v2h3 v-2H20z M6.1,23C6,22.7,6,22.3,6,22c0-3.3,2.7-6,6-6s6,2.7,6,6c0,0.3,0,0.7-0.1,1H6.1z"></path></svg>
			05:40<sup>am</sup>
		</span>
		<span class="DPDCsl">14:24</span>
		<span class="DPDCss">
			<svg xmlns="http://www.w3.org/2000/svg" viewbox="0 0 24 24"><path d="M12,14L7.8,9.8l1.4-1.4c0,0,0.9,0.9,1.8,1.8V4h2c0,0,0,3.3,0,6.2l1.8-1.8l1.4,1.4L12,14z"></path><path d="M6.8,15.3L5,13.5l-1.4,1.4l1.8,1.8L6.8,15.3z M4,21H1v2h3V21z M20.5,14.9L19,13.5l-1.8,1.8l1.4,1.4L20.5,14.9z M20,21v2h3 v-2H20z M6.1,23C6,22.7,6,22.3,6,22c0-3.3,2.7-6,6-6s6,2.7,6,6c0,0.3,0,0.7-0.1,1H6.1z"></path></svg>
			08:04<sup>pm</sup>
		</span>
	</div>
	<script>
		var s, t; s = document.createElement("script"); s.type = "text/javascript";
		s.src = "//cdn.dayspedia.com/js/dwidget.min.vb46adaa2.js";
		t = document.getElementsByTagName('script')[0]; t.parentNode.insertBefore(s, t);
		s.onload = function() {
			window.dwidget = new window.DigitClock();
			window.dwidget.init("dayspedia_widget_13540eca4615397a");
		};
	</script>
	<!--/DPDC-->
	</div><!--Dayspedia.com widget ENDS-->
<?php
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
  print "    <th>Publish</th>\n";
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
    if($message->publish()) print "    <td>Yes</td>\n";
    else print "    <td/>\n";
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
