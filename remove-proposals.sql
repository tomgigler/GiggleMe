-- One-time cleanup for an existing GiggleMe database after deploying the
-- source-code proposal removal.
--
-- The new code is compatible with the old guilds table shape, so this can be
-- run after the code change has been tested successfully.

USE `giggleme`;

-- Remove stored proposal messages (historically delivery_time = -1).
DELETE FROM `messages`
WHERE `delivery_time` = -1;

-- Remove proposal voting data.
DROP TABLE IF EXISTS `votes`;

-- Remove guild-level settings used only by proposals.
ALTER TABLE `guilds`
    DROP COLUMN `proposal_channel_id`,
    DROP COLUMN `delivery_channel_id`;
