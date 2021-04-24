#!/usr/bin/env python
import settings
import mysql.connector

def db_connect():
    return mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
            )

def db_execute_sql(sql, fetch, **kwargs):
    mydb = db_connect()

    mycursor = mydb.cursor(buffered=True)

    mycursor.execute(sql, tuple(kwargs.values()))

    rows = None
    if fetch:
        rows = mycursor.fetchall()

    mydb.commit()
    mycursor.close()
    mydb.disconnect()

    return rows

def get_all(table):
    return db_execute_sql(f"SELECT * FROM {table}", True)

def get_message(msg_id):
    return db_execute_sql("SELECT * FROM messages WHERE id = %s", True, msg_id=msg_id)[0]

def get_votes(proposal_id):
    return db_execute_sql("SELECT * FROM votes WHERE proposal_id = %s", True, proposal_id=proposal_id)

def update_message(message_id, guild_id, delivery_channel_id, delivery_time, author_id, repeat, last_repeat_message, content, description, repeat_until, special_handling):
    db_execute_sql("INSERT INTO messages values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE guild_id = %s, delivery_channel_id = %s, "
        "delivery_time =  %s, author_id = %s, repeats = %s, last_repeat_message = %s, content = %s, description = %s, repeat_until = %s, special_handling = %s",
        False, message_id=message_id, guild_id=guild_id, delivery_channel_id=delivery_channel_id, delivery_time=delivery_time, author_id=author_id,
        repeat=repeat, last_repeat_message=last_repeat_message, content=content, description=description, repeat_until=repeat_until, special_handling=special_handling, guild_id_2=guild_id, delivery_channel_id_2=delivery_channel_id,
        delivery_time_2=delivery_time, author_id_2=author_id, repeat_2=repeat, last_repeat_message_2=last_repeat_message, content_2=content, description_2=description, repeat_until_2=repeat_until, special_handling_2=special_handling)

def delete_message(message_id):
    db_execute_sql("DELETE FROM messages WHERE id=%s", False, message_id=message_id)

def delete_proposal_votes(proposal_id):
    db_execute_sql("DELETE FROM votes WHERE proposal_id = %s", False, proposal_id=proposal_id)

def replace_vote(proposal_id, user_id, vote):
    db_execute_sql("INSERT INTO votes (proposal_id, user_id, vote) VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE vote=%s", False, proposal_id=proposal_id, user_id=user_id, vote_1=vote, vote_2=vote)
            
def remove_vote(proposal_id, user_id):
    db_execute_sql("DELETE FROM votes WHERE proposal_id = %s and user_id = %s", False, proposal_id=proposal_id, user_id=user_id)

def get_timezones():
    return db_execute_sql("SELECT * FROM timezones ORDER BY name", True)

def save_vip(vip_id, guild_id, template_id, grace_period, last_sent):
    db_execute_sql("INSERT INTO vips (vip_id, guild_id, template_id, grace_period, last_sent) VALUES(%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE template_id=%s, grace_period=%s, last_sent=%s",
            False, vip_id=vip_id, guild_id=guild_id, template_id_1=template_id, grace_period_1=grace_period, last_sent_1=last_sent, template_id_2=template_id, grace_period_2=grace_period, last_sent_2=last_sent)

def update_vip_last_sent(last_sent, vip_id, guild_id):
    db_execute_sql("UPDATE vips SET last_sent = %s WHERE vip_id = %s and guild_id = %s", False, last_sent=last_sent, vip_id=vip_id, guild_id=guild_id)

def delete_vip(vip_id, guild_id):
    db_execute_sql("DELETE FROM vips WHERE vip_id = %s and guild_id = %s", False, vip_id=vip_id, guild_id=guild_id )

def save_user(user_id, name):
    db_execute_sql("INSERT INTO users ( user, name, last_active ) values ( %s, %s, 0 ) ON DUPLICATE KEY UPDATE name = %s", False, user_id=user_id, name_1=name, name_2=name)

def save_user_guild(user_id, guild_id, guild_name):
    db_execute_sql("INSERT INTO user_guilds ( user_id, guild_id, guild_name ) values (%s, %s, %s) ON DUPLICATE KEY UPDATE guild_name = %s",
            False, user_id=user_id, guild_id=guild_id, guild_name_1=guild_name, guild_name_2=guild_name)

def set_user_last_active(last_active, user_id):
    db_execute_sql("UPDATE users SET last_active = %s WHERE user = %s", False, last_active=last_active, user_id=user_id)

def set_user_last_message(message_id, user_id):
    db_execute_sql("UPDATE users SET last_message_id = %s WHERE user = %s", False, message_id=message_id, user_id=user_id)

def set_user_format_24(format_24, user_id):
    db_execute_sql("UPDATE users SET format_24 = %s WHERE user = %s", False, format_24=format_24, user_id=user_id)

def set_user_timezone(tz_id, name, user_id):
    db_execute_sql("UPDATE users SET timezone = %s, name = %s WHERE user = %s", False, tz_id=tz_id, name=name, user_id=user_id)

def save_guild(id, guild_name, proposal_channel_id, approval_channel_id, delivery_channel_id, tweet_channel_id, twitter_access_token_key, twitter_access_token_secret):
    db_execute_sql("INSERT INTO guilds ( id, guild_name, proposal_channel_id, approval_channel_id, delivery_channel_id, tweet_channel_id, twitter_access_token_key, twitter_access_token_secret ) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE guild_name = %s, proposal_channel_id = %s, approval_channel_id = %s, delivery_channel_id = %s, "
            "tweet_channel_id = %s, twitter_access_token_key = %s, twitter_access_token_secret = %s",
            False, id=id, guild_name=guild_name, proposal_channel_id=proposal_channel_id, approval_channel_id=approval_channel_id, delivery_channel_id=delivery_channel_id,
            tweet_channel_id=tweet_channel_id, twitter_access_token_key=twitter_access_token_key, twitter_access_token_secret=twitter_access_token_secret,
            guild_name_2=guild_name, proposal_channel_id_2=proposal_channel_id, approval_channel_id_2=approval_channel_id, delivery_channel_id_2=delivery_channel_id,
            tweet_channel_id_2=tweet_channel_id, twitter_access_token_key_2=twitter_access_token_key, twitter_access_token_secret_2=twitter_access_token_secret)

def save_channel(id, guild_id, name, channel_type, token_key, token_secret, user_id, screen_name):
    db_execute_sql("INSERT INTO channels ( id, guild_id, name, channel_type, token_key, token_secret, user_id, screen_name) values (%s, %s, %s, %s, %s, %s, %s, %s) "
    "ON DUPLICATE KEY UPDATE name = %s, channel_type = %s, token_key = %s, token_secret = %s, user_id = %s, screen_name = %s",
    False, id=id, guild_id=guild_id, name=name, channel_type=channel_type, token_key=token_key, token_secret=token_secret, user_id=user_id, screen_name=screen_name,
    name_2=name, channel_type_2=channel_type, token_key_2=token_key, token_secret_2=token_secret, user_id_2=user_id, screen_name_2=screen_name)

def pop_request_queue():
    row = db_execute_sql("SELECT id, action FROM request_queue WHERE request_time = (SELECT MIN(request_time) FROM request_queue)", True)
    if row:
        db_execute_sql("DELETE FROM request_queue WHERE id = %s AND action = %s", False, id=row[0][0], action=row[0][1])
        return ( row[0][0], row[0][1] )
    else:
        return ( None, None )
