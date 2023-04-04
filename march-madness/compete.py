import numpy as np
import pdb
from scipy.stats import rankdata
import os
from picks import Picks
from forecast import Forecast
import glob
import yahoo_parsing

def get_pick_ids(picks_dir, forecast):
    all_picks = []
    picks_files = glob.glob(picks_dir + '/*.picks')
    if len(picks_files) > 0:
        for file in picks_files:
            all_picks.append(Picks(file))
    else:
        all_picks = yahoo_parsing.run_yahoo_parsing(picks_dir)

    names = []
    pick_ids = np.zeros((len(all_picks), 63), dtype='uint16')
    for j, curr_picks in enumerate(all_picks):
        pick_ids[j,:] = curr_picks.convert_to_id(forecast)
        names.append(curr_picks.name)
    return pick_ids, names

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

def probability_matrix(ranks):
    shp = np.shape(ranks)
    pmat = np.zeros((shp[1], shp[1]))
    for i in range(0, shp[1]): # competitor
        curr = ranks[:,i]
        for j in range(0, shp[1]): # rank
            pmat[i][j] = len(curr[curr==j+1])
    pmat = pmat/shp[0]
    return pmat

def score_per_round_to_score_per_game(score):
    score_array = np.zeros(63)
    n = 32
    i = 0
    j = 0
    while n >= 1:
        n = int(n)
        score_array[i:i+n] = score[j]
        j += 1
        i += n
        n = n/2
    return score_array

def score_brackets(pick_ids, bracket_ids, bracket_seed_diffs, scoring_type):

    pick_ids = np.expand_dims(pick_ids, axis=0)
    bracket_ids = np.expand_dims(bracket_ids, axis=1)
    check = pick_ids == bracket_ids

    score_per_round = [10, 20, 40, 80, 120, 160]
    bonus_multiplier = [3, 5, 10, 20, 30, 40]
    # bonus_multiplier = [0, 0, 0, 0, 0, 0]

    score_per_game = score_per_round_to_score_per_game(score_per_round)
    bonus_multiplier_per_game = score_per_round_to_score_per_game(bonus_multiplier)
    score = score_per_game * check

    bracket_seed_diffs[bracket_seed_diffs < 0] = 0
    bracket_seed_diffs = np.expand_dims(bracket_seed_diffs, axis=1)
    bonus = bracket_seed_diffs * check * bonus_multiplier_per_game

    score = np.sum(score, axis=2).squeeze()
    bonus = np.sum(bonus, axis=2).squeeze()
    total = score + bonus
    return total, score, bonus

class Compete:
    def __init__(self, pick_ids, forecast, scoring_type, pick_names=[]):
        self.forecast = forecast
        self.pick_ids = pick_ids
        self.scoring_type = scoring_type
        self.pick_names = pick_names


        self.Npicks = self.pick_ids.shape[0]
        if len(self.pick_names) == 0:
            self.pick_names = [x for x in range(self.Npicks)]

        assert(len(self.pick_names) == self.Npicks)

    def run_MC(self, Nbrackets):
        self.Nbrackets = Nbrackets
        self.bracket_ids, self.bracket_seed_diffs = self.forecast.gen_brackets(Nbrackets)
        self.scores, self.no_bonus, self.bonus = self.score_all_picks()

    def do_calcs(self):
        scores, no_bonus, bonus = self.scores, self.no_bonus, self.bonus

        ranks = np.zeros((self.Nbrackets, self.Npicks))
        ranks2 = np.zeros((self.Nbrackets, self.Npicks))
        for i in range(scores.shape[0]):
            ranks[i,:]  = self.Npicks + 1 - rankdata(scores[i,:], 'max')
            ranks2[i,:] = self.Npicks + 1 - rankdata(scores[i,:], 'min')

        print('Start Calcs')
        medians = np.median(scores, axis=0)
        pmat = probability_matrix(ranks)
        min_scores = np.min(scores, axis=0)
        min_no_bonus = np.min(no_bonus, axis=0)
        min_bonus = np.min(bonus, axis=0)
        max_scores = np.max(scores, axis=0)
        max_no_bonus = np.max(no_bonus, axis=0)
        max_bonus = np.max(bonus, axis=0)
        pwin = pmat[:,0]
        pmat2 = probability_matrix(ranks2)
        plose = pmat2[:,-1]
        best_finish = np.min(ranks, axis=0)
        worst_finish = np.max(ranks2,axis=0)
        curr_order = np.argsort(min_scores)
        curr_order = curr_order[::-1]
        mean_finish = np.mean(ranks, axis=0)
        median_finish = np.median(ranks, axis=0)
        print('Finish Calcs')

        self.scores = scores
        self.no_bonus = no_bonus
        self.bonus = bonus
        self.ranks = ranks
        self.medians = medians
        self.pmat = pmat
        self.min_scores = min_scores
        self.min_no_bonus = min_no_bonus
        self.min_bonus = min_bonus
        self.max_scores = max_scores
        self.max_no_bonus = max_no_bonus
        self.max_bonus = max_bonus
        self.pwin = pwin
        self.pmat2 = pmat2
        self.plose = plose
        self.best_finish = best_finish
        self.worst_finish = worst_finish
        self.curr_order = curr_order
        self.mean_finish = mean_finish
        self.median_finish = median_finish


    def score_all_picks(self):
        total = np.zeros((self.Nbrackets, self.Npicks))
        score = np.zeros((self.Nbrackets, self.Npicks))
        bonus = np.zeros((self.Nbrackets, self.Npicks))
        for i in range(self.Npicks):
            total[:,i], score[:,i], bonus[:,i] = score_brackets(
                self.pick_ids[i,:], self.bracket_ids, self.bracket_seed_diffs, self.scoring_type)
        return total, score, bonus

    def sort_order(self):
        return argsort(self.pick_names)

    def summary(self):
        self.do_calcs()
        print(self.forecast.forecast_file)
        print(self.forecast.truth_file)
        print(self.Nbrackets)
        print('{:30},{:10},{:10},{:10},{:10},{:10},{:10}'.format(
            'Bracket Name', 'min score', 'max score', 'P lose', 'P win', 'min rank', 'max rank'))
        # for i in self.curr_order:
        # for i in range(self.Npicks):
        for i in argsort(self.pick_names):
            print('{:30},{:10.0f},{:10.0f},{:10.2f},{:10.3f},{:10.0f},{:10.0f}'.format(
                self.pick_names[i], self.min_scores[i], self.max_scores[i], self.plose[i]*100, self.pwin[i]*100,
                self.worst_finish[i], self.best_finish[i]))



if __name__ == "__main__":
    import random
    random.seed(0)
    import argparse

    parser = argparse.ArgumentParser(description='Find best picks')
    parser.add_argument('--scoring_type', type=str, default='family',
                        help='family or spacex')
    parser.add_argument('--forecast_file', type=str,
                        default='./forecast/fivethirtyeight_ncaa_forecasts.csv',
                        help='truth_file file for bracket simulations')
    parser.add_argument('--truth_file', type=str,
                        default='',
                        help='forecast file for generating picks')

    parser.add_argument('--Nbrackets', type=int, default=10000,
                        help='number of brackets to generate')

    parser.add_argument('--picks_dir', type=str, default='family',
                        help='family or spacex')
    args = parser.parse_args()

# python compete.py --truth_file truth/history/round3_game02.truth


    if len(args.scoring_type) == 0:
        scoring_type = args.picks_dir
    else:
        scoring_type = args.scoring_type

    forecast = Forecast(args.forecast_file, args.truth_file)
    pick_ids, names = get_pick_ids(args.picks_dir, forecast)

    mcc = Compete(pick_ids, forecast, scoring_type, names)
    mcc.run_MC(args.Nbrackets)
    mcc.summary()
    # pdb.set_trace()
