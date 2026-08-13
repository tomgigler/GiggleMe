-- GiggleMe database schema
-- Baseline schema for GiggleMe.
-- Existing deployments may require a migration when columns or tables are
-- intentionally retired.

CREATE DATABASE IF NOT EXISTS `giggleme`
    DEFAULT CHARACTER SET utf8mb4;

USE `giggleme`;

CREATE TABLE IF NOT EXISTS `channels` (
  `id` bigint(20) NOT NULL,
  `guild_id` bigint(20) DEFAULT NULL,
  `name` varchar(200) DEFAULT NULL,
  `channel_type` int(11) DEFAULT NULL,
  `token_key` varchar(60) DEFAULT NULL,
  `token_secret` varchar(60) DEFAULT NULL,
  `user_id` varchar(20) DEFAULT NULL,
  `screen_name` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `guilds` (
  `id` bigint(20) NOT NULL,
  `guild_name` varchar(200) DEFAULT NULL,
  `approval_channel_id` bigint(20) DEFAULT NULL,
  `plan_level` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `messages` (
  `id` varchar(20) NOT NULL,
  `guild_id` bigint(20) DEFAULT NULL,
  `delivery_channel_id` bigint(20) DEFAULT NULL,
  `delivery_time` double DEFAULT NULL,
  `author_id` bigint(20) DEFAULT NULL,
  `repeats` varchar(50) DEFAULT NULL,
  `last_repeat_message` bigint(20) DEFAULT NULL,
  `content` text,
  `description` text,
  `repeat_until` double DEFAULT NULL,
  `special_handling` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `mute_members` (
  `guild_id` bigint(20) NOT NULL,
  `member_id` bigint(20) NOT NULL,
  `member_name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`guild_id`,`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `request_queue` (
  `id` varchar(20) NOT NULL,
  `action` varchar(10) NOT NULL,
  `request_time` double DEFAULT NULL,
  PRIMARY KEY (`id`,`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `timezones` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `url` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `user_guilds` (
  `user_id` bigint(20) NOT NULL,
  `guild_id` bigint(20) NOT NULL,
  `guild_name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`user_id`,`guild_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `users` (
  `user` bigint(20) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `timezone` int(11) DEFAULT NULL,
  `last_active` double DEFAULT NULL,
  `last_message_id` varchar(20) DEFAULT NULL,
  `format_24` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `vips` (
  `vip_id` bigint(20) NOT NULL,
  `guild_id` bigint(20) NOT NULL,
  `template_id` varchar(20) DEFAULT NULL,
  `grace_period` int(11) DEFAULT NULL,
  `last_sent` double DEFAULT NULL,
  PRIMARY KEY (`vip_id`,`guild_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


-- Required timezone seed data.
--
-- The numeric IDs are persisted by the application, so keep these IDs stable.
-- INSERT ... ON DUPLICATE KEY UPDATE makes this section safe to run again.

INSERT INTO `timezones` (`id`, `name`, `url`) VALUES
  (1, 'UTC',         'https://free.timeanddate.com/clock/i8ec1q3x'),
  (2, 'US/Pacific',  'https://free.timeanddate.com/clock/i8ec1q3x/n137'),
  (3, 'US/Eastern',  'https://free.timeanddate.com/clock/i8ec1q3x/n179'),
  (4, 'US/Central',  'https://free.timeanddate.com/clock/i8ec1q3x/n64'),
  (5, 'US/Mountain', 'https://free.timeanddate.com/clock/i8ec1q3x/n75')
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `url` = VALUES(`url`);
