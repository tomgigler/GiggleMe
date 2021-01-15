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

def get_messages():
    return db_execute_sql("SELECT * FROM messages", True)

def get_votes(proposal_id):
    return db_execute_sql("SELECT * FROM votes WHERE proposal_id = %s", True, proposal_id=proposal_id)

def delete_proposal_votes(proposal_id):
    db_execute_sql("DELETE FROM votes WHERE proposal_id = %s", False, proposal_id=proposal_id)

def replace_vote(proposal_id, user_id, vote):
    db_execute_sql("INSERT INTO votes (proposal_id, user_id, vote) VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE vote=%s", False, proposal_id=proposal_id, user_id=user_id, vote_1=vote, vote_2=vote)
            
def remove_vote(proposal_id, user_id):
    db_execute_sql("DELETE FROM votes WHERE proposal_id = %s and user_id = %s", False, proposal_id=proposal_id, user_id=user_id)

def get_timezones():
    return db_execute_sql("SELECT * FROM timezones ORDER BY name", True)
