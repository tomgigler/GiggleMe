#!/usr/bin/env python
import gigdb

class GigVote:
    def __init__(self):
        self.votes = {}

    def load_proposal_votes(self, proposal_id):
        mydb = gigdb.db_connect()
        mycursor = mydb.cursor()

        sql = "SELECT * FROM votes WHERE proposal_id = %s"

        mycursor.execute(sql, (proposal_id,))

        for row in mycursor.fetchall():
            if row[0] in self.votes:
                self.votes[row[0]].update({ row[1]: row[2] })
            else:
                self.votes[row[0]] = { row[1]: row[2] }

        mydb.commit()
        mycursor.close()
        mydb.disconnect()

    def vote(self, proposal_id, user_id, vote):
        mydb = gigdb.db_connect()
        mycursor = mydb.cursor()

        if vote:
            if proposal_id in self.votes:
                self.votes[proposal_id]].update({user_id: vote})
            else:
                self.votes[proposal_id]] = {user_id: vote}

            sql = "INSERT INTO votes (proposal_id, user_id, vote) VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE vote=%s"
            mycursor.execute(sql, (proposal_id, user_id, vote, vote))
            
        else:
            if proposal_id in self.votes:
                self.votes[proposal_id]].pop(user_id, None)
            sql = "DELETE FROM votes WHERE proposal_id = %s and user_id = %s"
            mycursor.execute(sql, (proposal_id, user_id, vote, vote))

        mydb.commit()
        mycursor.close()
        mydb.disconnect()

    def remove_proposal(self, proposal_id):
        mydb = gigdb.db_connect()
        mycursor = mydb.cursor()

        sql = "DELETE FROM votes WHERE proposal_id = %s"
        mycursor.execute(sql, (proposal_id,))

        mydb.commit()
        mycursor.close()
        mydb.disconnect()
