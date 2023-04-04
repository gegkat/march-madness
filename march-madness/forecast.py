import csv
import pdb
# import picks
import synonyms
from game import Game
from round import Round
from bracket import Bracket
from team import Team
import numpy as np
import pickle
import os

def fname_from_fullpath(fullpath):
    return os.path.splitext(os.path.basename(fullpath))[0]

def load_pickle(fname):
    with open(fname, 'rb') as fp:
        data = pickle.load(fp)
    return data['ids'], data['seed_diffs']

def write_pickle(fname, ids, seed_diffs):
    with open(fname, 'wb') as fp:
        pickle.dump({'ids':ids, 'seed_diffs':seed_diffs}, fp)

def sort_region(region):
    return [region[0], region[7], region[4], region[3], 
            region[5], region[2], region[6], region[1]]

def sort_first_games(first_games):
    first_games = sorted(first_games, key=lambda k:k[0].seed)
    first_games = sorted(first_games, key=lambda k:k[0].region)

    # Alphabetical
    East =    sort_region(first_games[0:8])
    Midwest = sort_region(first_games[8:16])
    South =   sort_region(first_games[16:24])
    West =    sort_region(first_games[24:32])
     
    ## UPDATE ##
    # Use order from actual bracket here
    return South + East + Midwest + West

def csv_row2dict(row, fieldnames):
    data = {}
    i = 0
    for field in row:
        field = field.strip()
        try:
            curr = float(field)
        except:
            if field == 'False':
                curr = False
            elif field == 'True':
                curr = True
            else:
                curr = field
        data[fieldnames[i]] = curr
        i = i + 1
    return data

class Forecast:
    def __init__(self, forecast_file, truth_file=''):
        self.forecast_file = forecast_file
        self.truth_file = truth_file
        self.idmap = {}
        self.teams = {} # dict id -> Team
        self.first_games = []

        self.read_forecast(forecast_file)
        self.make_name_to_id_lookup()
        if len(truth_file) > 0:
            self.add_truth(truth_file)
        self.hardcode_first_round() 
        self.find_first_games()
        self.write_truth_file('./truth/base.truth')

    def get_bracket(self):
        return Bracket(self.first_games)        

    def find_game(self, i_rnd, team_id):
        bracket = self.get_bracket()
        rnd = bracket.rounds[i_rnd-1]
        return rnd.find_game(team_id)

    def add_truth(self, truth_file):
        # Expects csv with a header row and then
        # two columns, Name and Final Round
        with open(truth_file, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            header = reader.__next__()
            while header[0][0] == '#':
                header = reader.__next__()
            for row in reader:
                name, final_round = row[0], int(row[1])
                curr_id = self.name_to_id(name)
                self.teams[curr_id].update_final_round(final_round)
    
    def hardcode_first_round(self):
        # 357   Texas A&M-Corpus Christi    1   South   16a
        # 2546  Southeast Missouri State    1   South   16b

        # 2640  Texas Southern  1   East    16a
        # 161   Fairleigh Dickinson 1   East    16b

        # 9     Arizona State   1   West    11a
        # 2440  Nevada  1   West    11b

        # 344   Mississippi State   1   Midwest 11a
        # 221   Pittsburgh  1   Midwest 11b

        playin_winners = [357, 161, 9, 221]
        playin_losers = [2546, 2640, 2440, 344]

        for t_id in playin_winners:
            self.teams[t_id].seed = float(self.teams[t_id].seed[0:2])
            self.teams[t_id].playin_flag = 0
        for t_id in playin_losers:
            self.teams.pop(t_id)

        for team_id, team in self.teams.items():
            if team.playin_flag > 0:
                print(team.seed, team_id, team.region, team.name)

    def find_first_games(self):
        games = []
        for _, team1 in self.teams.items():
            assert(not team1.playin_flag)
            if team1.seed <= 8:
                for _, team2 in self.teams.items():
                    if team1.region == team2.region and team2.seed == 17 - team1.seed:
                        games.append((team1, team2)) 
        first_games = sort_first_games(games)
        self.first_games = Round(first_games, rnd=1)

    def read_forecast(self, fname):
        teams = {}
        with open(fname, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            header = reader.__next__()
            id_idx = header.index('team_id')
            for row in reader:
                if row[0] == 'mens':
                    curr_id = int(row[id_idx])
                    team_dict = csv_row2dict(row, header)
                    teams[curr_id] = Team(team_dict)
        self.teams = teams

    def make_name_to_id_lookup(self):
        for teamid in self.teams:
            team = self.teams[teamid]
            self.idmap[team.name.lower()] = team.id

    def name_to_id(self, name):                
        name = name.lower().strip()
        if name in synonyms.synonyms:
            name = synonyms.synonyms[name].lower().strip()
        name = name.replace("st.", "state")
        if name in self.idmap:
            return int(self.idmap[name])
        else:
            print('"{}" not found in forecast bracket'.format(name)) 
            z = [x for x in self.idmap]
            z.sort()
            print(z)
            pdb.set_trace()
            # raise("Error")

    def write_truth_file(self, outfile, title=''):
        with open(outfile, 'wt') as fo:
            fo.write('# ' + title + '\n')
            fo.write('Name, Final Round\n')
            for game in self.first_games.games:
                game.teams[0].write_to_truth_file(fo)
                game.teams[1].write_to_truth_file(fo)

    # def baseline(self):
        # return Bracket(self.first_games).convert()

    def get_pickle_fname(self, N):
        forecast_file = fname_from_fullpath(self.forecast_file)
        truth_file = fname_from_fullpath(self.truth_file)
        return "./brackets/{}_{}_{}.p".format(forecast_file, truth_file, N)

    def gen_brackets(self, N, use_pickle=True, verbose=False):
        fname = self.get_pickle_fname(N)
        if os.path.isfile(fname) and use_pickle:
            print('Found existing pickle')
            return load_pickle(fname)

        print('Generating brackets')
        ids = np.zeros((N, 63), dtype='uint16')
        seed_diffs = np.zeros((N, 63), dtype='int8')
        for i in range(N):
            if verbose and i % 1000 == 0:
                print(i)
            ids[i,:], seed_diffs[i,:] = self.get_bracket().convert()
            
        if use_pickle:
            write_pickle(fname, ids, seed_diffs)
        print('Bracket generation complete.')
        return ids, seed_diffs

