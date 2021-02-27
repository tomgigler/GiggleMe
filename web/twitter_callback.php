<?php

include 'settings.php';
require_once 'vendor/autoload.php';
use Abraham\TwitterOAuth\TwitterOAuth;
require_once 'DBConnection.php';

session_start();

$oauth_verifier = filter_input(INPUT_GET, 'oauth_verifier');

if (empty($oauth_verifier) ||
    empty($_SESSION['oauth_token']) ||
    empty($_SESSION['oauth_token_secret'])
) {
    // something's missing, go and login again
    header('Location: ' . 'twitter_login.php');
}

// connect with application token
$connection = new TwitterOAuth(
    $twitter_consumer_key,
    $twitter_consumer_secret,
    $_SESSION['oauth_token'],
    $_SESSION['oauth_token_secret']
);

// request user token
$token = $connection->oauth(
    'oauth/access_token', [
        'oauth_verifier' => $oauth_verifier
    ]
);

$db = new DBConnection();
$db->create_channel($token['user_id'], $_SESSION['new_channel_guild_id'], $_SESSION['new_channel_name'], 2, $token['oauth_token'], $token['oauth_token_secret'], $token['user_id'], $token['screen_name']);
unset($_SESSION['new_channel_guild_id']);
unset($_SESSION['new_channel_name']);
header('Location: ' . 'custom_channels.php');
