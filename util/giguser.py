#!/usr/bin/env python
import gigdb

users = {}
user_guilds = {}

class User:
    def __init__(self, id, name, timezone, last_active, last_message_id, format_24):
        self.id = id
        self.name = name
        self.timezone = timezone
        self.last_active = last_active
        self.last_message_id = last_message_id
        self.format_24 = format_24

    def set_last_active(self, last_active):
        mydb = gigdb.db_connect()

        sql = "UPDATE users SET last_active = %s WHERE user = %s"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (last_active, self.id))
        self.last_active = last_active
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

    def set_last_message(self, message_id):
        mydb = gigdb.db_connect()

        sql = "UPDATE users SET last_message_id = %s WHERE user = %s"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (message_id, self.id))
        self.last_message_id = message_id
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

    def set_time_format(self, time_format):
        if time_format == "24":
            self.format_24 = 1
        else:
            self.format_24 = 0

        mydb = gigdb.db_connect()

        sql = "UPDATE users SET format_24 = %s WHERE user = %s"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (self.format_24, self.id))
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

def load_users():
    mydb = gigdb.db_connect()

    mycursor = mydb.cursor()

    mycursor.execute("select * from users")
    for user in mycursor.fetchall():
        users[user[0]] = User(user[0], user[1], user[2], user[3], user[4], user[5])

    mycursor.execute("select * from user_guilds")

    for row in mycursor.fetchall():
        if row[0] in user_guilds.keys():
            user_guilds[row[0]].append(row[1])
        else:
            user_guilds[row[0]] = [ row[1] ]

    mycursor.close()
    mydb.disconnect()

def save_user(user_id, name, guild_id, guild_name):

    mydb = gigdb.db_connect()
    mycursor = mydb.cursor(buffered=True)

    sql = "SELECT * FROM users WHERE user = %s"

    mycursor.execute(sql, ( user_id, ))

    if mycursor.rowcount > 0:
        update = True
    else:
        update = False

    if update:
        sql = "UPDATE users SET name = %s WHERE user = %s"
    else:
        sql = "INSERT INTO users ( name, user, last_active ) values ( %s, %s, 0 )"

    mycursor.execute(sql, ( name, user_id ) )

    sql = "SELECT * FROM user_guilds WHERE user_id = %s and guild_id = %s"

    mycursor.execute(sql, ( user_id, guild_id ) )

    if mycursor.rowcount > 0:
        update = True
    else:
        update = False

    if update:
        sql = "UPDATE user_guilds SET guild_name = %s WHERE user_id = %s and guild_id = %s"
    else:
        sql = "INSERT INTO user_guilds ( guild_name, user_id, guild_id ) values ( %s, %s, %s )"

    mycursor.execute(sql, ( guild_name, user_id, guild_id ) )

    mydb.commit()

    mycursor.close()
    mydb.disconnect()

    if user_id not in users.keys():
        users[user_id] = User(user_id, name, None, 0, None, None)

    if user_id in user_guilds.keys():
        user_guilds[user_id].append(guild_id)
    else:
        user_guilds[user_id] = [ guild_id ]
