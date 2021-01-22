#!/usr/bin/env python
import gigdb

class GigVote:
    def __init__(self):
        self.votes = {}

    def load_proposal_votes(self, proposal_id):
        for row in gigdb.get_votes(proposal_id):
            if row[0] in self.votes:
                self.votes[row[0]].update({ row[1]: row[2] })
            else:
                self.votes[row[0]] = { row[1]: row[2] }

    def vote(self, proposal_id, user_id, vote):
        if vote:
            if proposal_id in self.votes:
                self.votes[proposal_id].update({user_id: vote})
            else:
                self.votes[proposal_id] = {user_id: vote}

            gigdb.replace_vote(proposal_id, user_id, vote)
            
        else:
            if proposal_id in self.votes:
                self.votes[proposal_id].pop(user_id, None)
            gigdb.remove_vote(proposal_id, user_id)

    def remove_proposal(self, proposal_id):
        gigdb.delete_proposal_votes(proposal_id)
        self.votes.pop(proposal_id, None)

    def vote_count(self, proposal_id):
        return len(self.votes[proposal_id]) - 1

    def get_required_approvals(self, proposal_id):
        return self.votes[proposal_id][-1]
