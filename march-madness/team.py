import pdb
import numpy as np

class Team:
    def __init__(self, data):
        self.playin_flag = data['playin_flag']
        self.id = int(data['team_id'])
        self.name = data['team_name']
        self.rating = data['team_rating']
        self.region = data['team_region']
        self.seed = data['team_seed']

        self.rd_win = np.zeros((6))
        for i in range(6):
            self.rd_win[i] = data['rd' + str(i+2) + '_win']

        self.final_round = -1

    def summary(self):
        return '{:<3}{:8}{:12} {:<5}'.format(
            int(self.seed), self.region, self.name[0:12], self.id)

    def __str__(self):
        out = ""
        out += "{} {}\n".format(self.name, self.id)
        for item in vars(self).items():
            if item[0] is 'rd_win':
                s = '  {:12} '.format(item[0])
                for x in item[1]:
                    s += '{:.03f} '.format(x)
                out += s + '\n'
            else:
                out += '  {:12} {}\n'.format(item[0], item[1])
        return out

    def write_to_truth_file(self, fo):
        fo.write('{},{}\n'.format(self.name, self.final_round))

    def update_final_round(self, final_round):
        self.final_round = final_round