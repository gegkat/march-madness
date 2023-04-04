import os
import copy
from compete import Compete, get_pick_ids
from forecast import Forecast, fname_from_fullpath
from bracket import Bracket
# from picks import Picks
import numpy as np
import glob
import pdb

class Scenarios:
    def __init__(self, Nbrackets, pick_ids, forecast, bonus_type, truth_files_dir, names=''):
        self.truth_files_dir = truth_files_dir
        self.forecast = forecast
        self.initial_truth_file = self.forecast.truth_file
        self.forecast_file = self.forecast.forecast_file

        self.competitions = []
        self.truth_files = []

        truth_files = os.listdir(truth_files_dir)
        truth_files.sort()
        for truth_file in truth_files:
            if truth_file.endswith(".truth"):
                tf = os.path.join(truth_files_dir, truth_file)
                print(tf)
                self.truth_files.append(tf)
                forecast = Forecast(self.forecast_file, tf)
                curr = Compete(pick_ids, forecast, bonus_type, names)
                curr.run_MC(Nbrackets)
                curr.do_calcs()

                self.competitions.append(copy.copy(curr))

    def get_game(self, competition):
        truth_file = competition.forecast.truth_file
        with open(truth_file, 'rt') as fp:
            line = fp.readline()
        return line[2:-1]
 
    def write_to_file(self, out_file, order=None):
        if order is None:
            # order = range(0, len(self.competitions[0].pick_names))
            order = self.competitions[0].sort_order()
        out = ''
        with open(out_file, 'wt') as f:
            out += 'Probability of Winning\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:10.4f},'.format(c.pwin[i]*100)     
                out += '\n'
            out += '\n'
            out += 'Probability of Losing\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:10.4f},'.format(c.plose[i]*100)
                out += '\n'
            out += '\n'
            out += 'Best Finish\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.best_finish[i])
                out += '\n'
            out += '\n'
            out += 'Worst Finish\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.worst_finish[i])
                out += '\n'
            out += '\n'
            out += 'Min Score\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.min_scores[i])
                out += '\n'
            out += '\n'
            out += 'Max Score\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.max_scores[i])     
                out += '\n'
            f.write(out)

    def names(self,order):
        out = ','
        for i in order:
            name = fname_from_fullpath(self.competitions[0].pick_names[i])
            out += '{},'.format(name)
        out += '\n'
        return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Find best picks')
    parser.add_argument('--scoring_type', type=str, default='',
                        help='family or spacex. If not given, then picks_dir is used')
    parser.add_argument('--forecast_file', type=str, 
                        default='./forecast/fivethirtyeight_ncaa_forecasts.csv',
                        help='')
    parser.add_argument('--initial_truth_file', type=str, 
                        default='',
                        help='')
    parser.add_argument('--Nbrackets', type=int, default=10000,
                        help='number of brackets to generate')
    parser.add_argument('--picks_dir', type=str, default='family',
                        help='family or spacex')
    parser.add_argument('--truth_files_dir', type=str, default='./truth/scenarios/',
                        help='Directory to write truth files')
    # parser.add_argument('--results_out_file', type=str, default='scenarios.results',
                        # help='Directory to write truth files')
    args = parser.parse_args()

# python scenarios.py --truth_files_dir ./truth/history/
# python scenarios.py --truth_files_dir ./truth/scenarios/rnd3/

    if len(args.scoring_type) == 0:
        scoring_type = args.picks_dir
    else:
        scoring_type = args.scoring_type

    forecast = Forecast(args.forecast_file, args.initial_truth_file)

    pick_ids, names = get_pick_ids(args.picks_dir, forecast)
    sce = Scenarios(args.Nbrackets, pick_ids, forecast, scoring_type, args.truth_files_dir, names)
    results_out_file = args.truth_files_dir + '/' + args.picks_dir + '.results'
    sce.write_to_file(results_out_file)

