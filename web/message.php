<?php
include "login_check.inc";
include "header.inc";
include "settings.inc";

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";
print "Show message " . $_GET['id'] . "\n";
print "</center>\n";

