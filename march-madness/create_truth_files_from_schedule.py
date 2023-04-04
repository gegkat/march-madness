import os
import copy
from compete import Compete, get_pick_ids
from forecast import Forecast
from bracket import Bracket
# from picks import Picks
import numpy as np
import glob
import pdb
        

def create_truth_files_from_schedule(schedule_file, forecast, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    i = -1
    count = 1
    results = []
    result_ids = []
    outfile = os.path.join(out_dir, 'round0_game00.truth')
    forecast.write_truth_file(outfile, 'initial_truth_file ' + forecast.truth_file)
    with open(schedule_file, 'r') as f:
        for line in f:
            if line[0] == '-':
                results.append([])
                result_ids.append([])
                i += 1
                count = 1
            else:
                results[i].append(line.strip())
                curr_id = forecast.name_to_id(line)
                result_ids[i].append(curr_id)
                if curr_id:
                    forecast.teams[curr_id].final_round = i+1
                    outfile = os.path.join(out_dir, 'round{}_game{:02d}.truth'.format(i+1,count))
                    game = forecast.find_game(i+1, curr_id)
                    title = 'Round {} Game {:02d}: {} defeats {}'.format(i+1,count,
                        game.get_winner().name, game.get_loser().name)
                    forecast.write_truth_file(outfile, title)
                    count += 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Find best picks')
    parser.add_argument('--forecast_file', type=str, 
                        default='./forecast/fivethirtyeight_ncaa_forecasts.csv',
                        help='forecast file for name to id')
    parser.add_argument('--initial_truth_file', type=str, 
                        default='')
    parser.add_argument('--out_dir', type=str, default='./truth/history/',
                        help='Directory to write truth files')
    parser.add_argument('--schedule_file', type=str, default='./schedules/losers.schedule',
                        help='File containing losing teams in order')
    args = parser.parse_args()

    forecast = Forecast(args.forecast_file, args.initial_truth_file)
    create_truth_files_from_schedule(args.schedule_file, forecast, args.out_dir)

