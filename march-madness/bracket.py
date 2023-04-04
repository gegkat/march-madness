import pdb
import numpy as np

class Bracket:
    def __init__(self, first_round):
        self.rounds = [first_round]
        rnd = first_round
        while True:
            rnd.resolve()
            rnd = rnd.next_round()
            if not rnd:
                break
            self.rounds.append(rnd)

    def summary(self):
        out = ""
        for rnd in self.rounds:
            out += '--------------------------------------------------------\n'
            out += rnd.summary()
        return out

    def __str__(self):
        out = ""
        for item in vars(self).items():
            if isinstance(item[1], list):
                out += '  {:12} [({})]\n'.format(item[0], len(item[1]))
            else:
                out += '  {:12} {}\n'.format(item[0], item[1])
        return out

    def convert(self):
        ids = np.zeros(63, dtype='uint16')
        seed_diffs = np.zeros(63, dtype='int8')
        i = 0
        for rnd in self.rounds:
            for game in rnd.games:
                ids[i] = game.get_winner().id
                seed_diffs[i] = game.get_seed_diff()
                i += 1 
        return ids, seed_diffs