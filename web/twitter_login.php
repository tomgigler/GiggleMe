<?php

include 'settings.php';
require_once 'vendor/autoload.php';
use Abraham\TwitterOAuth\TwitterOAuth;

session_start();
$_SESSION['new_channel_guild_id'] = $_GET['guild_id'];
$_SESSION['new_channel_name'] = $_GET['channel_name'];

// create TwitterOAuth object
$twitteroauth = new TwitterOAuth($twitter_consumer_key, $twitter_consumer_secret);

// request token of application
$request_token = $twitteroauth->oauth(
    'oauth/request_token', [
        'oauth_callback' => $twitter_url_callback
    ]
);

// throw exception if something gone wrong
    if($twitteroauth->getLastHttpCode() != 200) {
        throw new \Exception('There was a problem performing this request');
}

// save token of application to session
$_SESSION['oauth_token'] = $request_token['oauth_token'];
$_SESSION['oauth_token_secret'] = $request_token['oauth_token_secret'];

// generate the URL to make request to authorize our application
$url = $twitteroauth->url(
    'oauth/authorize', [
        'oauth_token' => $request_token['oauth_token']
    ]
);

// and redirect
header('Location: '. $url);

?>
