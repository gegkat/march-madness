from scipy.special import erfinv, erf
from random import uniform
import pdb

def resolve_game_result(sample, t1_frnd, t2_frnd, p_win, rnd):
    # No truth value for this game
    if t1_frnd == -1 and t2_frnd == -1:
        return sample >= p_win

    # Check for conflict in final round truth value
    assert(t1_frnd != t2_frnd)

    # t1 advanced
    if t1_frnd > rnd:
        assert(t2_frnd == rnd or t2_frnd == -1)
        return 0

    # t1 lost
    elif t1_frnd != -1:
        assert(t1_frnd == rnd)
        assert(t2_frnd > rnd or t2_frnd == -1)
        return 1

    # t2 advanced
    elif t2_frnd > rnd:
        return 1
    # t2 lost
    else:
        assert(t2_frnd == rnd)
        return 0

class Game:
    def __init__(self, teams, rnd, favorite=False):
        self.teams = teams
        self.round = rnd
        self.favorite = favorite
        self.p_win = self.calc_win_prob()
        self.result = None
        # self.check_fit()

    def get_winner(self):
        return self.teams[self.result]

    def get_loser(self):
        return self.teams[not self.result]

    def get_seed_diff(self):
        return self.get_winner().seed - self.get_loser().seed

    def check_fit(self):
        # @TODO: This only makes sense for first round
        # Should add code for actual fit check across Monte Carlo
        diff = self.teams[0].rating - self.teams[1].rating
        p_win538 = self.teams[0].rd_win[self.round - 1]

        # nsigma = 2**0.5*erfinv(2*p_win538-1)
        # sigma = diff/nsigma
        error = self.p_win - p_win538 

        self.error = error

    def calc_win_prob(self):
        diff = self.teams[0].rating - self.teams[1].rating
        return 0.5*(1+erf(diff/10/2**0.5))

    def resolve(self):
        # returns index of winning team
        # sample must be between 0 and 1
        # For monte carlo, sample should be uniformly distributed
        # For favorite to win use 1
        # For higher rated to win use 0.5
        
        sample = 0.5 if self.favorite else uniform(0,1)

        # Get final round truth values
        t1_frnd = self.teams[0].final_round
        t2_frnd = self.teams[1].final_round

        self.result = resolve_game_result(sample, t1_frnd, t2_frnd, self.p_win, self.round)

    def __str__(self):
        out = ""
        out += self.summary() + '\n'
        for item in vars(self).items():
            if isinstance(item[1], list):
                out += '  {:12} [({})]\n'.format(item[0], len(item[1]))
            else:
                out += '  {:12} {}\n'.format(item[0], item[1])
        return out


    def summary(self):
        winner = self.get_winner().summary()
        loser = self.get_loser().summary()                
        return winner + " over " + loser
