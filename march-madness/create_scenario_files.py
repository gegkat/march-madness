import os
import copy
from compete import Compete, get_pick_ids
from forecast import Forecast
from bracket import Bracket
# from picks import Picks
import numpy as np
import glob
import pdb

def create_scenario_files(n_rnd, out_dir, forecast):
    initial_truth_file = forecast.truth_file
    forecast_file = forecast.forecast_file
    bracket = Bracket(forecast.first_games)
    rnd = bracket.rounds[n_rnd-1]
    scenario_count = 1
    game_count = 1
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    outfile = os.path.join(out_dir, 'scenario00.truth')
    forecast.write_truth_file(outfile, initial_truth_file)
    for game in rnd.games:
        team1 = forecast.teams[game.teams[0].id]
        team2 = forecast.teams[game.teams[1].id]
        if team1.final_round == -1 and team2.final_round == -1:
            outfile = os.path.join(out_dir, 'scenario{:02d}.truth'.format(scenario_count))
            forecast = Forecast(forecast_file, initial_truth_file)
            winner = game.teams[0].name
            loser  = game.teams[1].name
            forecast.teams[game.teams[1].id].final_round = n_rnd
            title = 'Round {} Game {}A: {} defeats {}'.format(n_rnd, game_count, winner, loser)
            forecast.write_truth_file(outfile, title)
            scenario_count += 1

            outfile = os.path.join(out_dir, 'scenario{:02d}.truth'.format(scenario_count))
            forecast = Forecast(forecast_file, initial_truth_file)
            winner = game.teams[1].name
            loser  = game.teams[0].name
            forecast.teams[game.teams[0].id].final_round = n_rnd
            title = 'Round {} Game {}B: {} defeats {}'.format(n_rnd, game_count, winner, loser)
            forecast.write_truth_file(outfile, title) 
            scenario_count += 1
        game_count += 1
        


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Find best picks')

    parser.add_argument('--forecast_file', type=str, 
                        default='./forecast/fivethirtyeight_ncaa_forecasts.csv',
                        help='truth_file file for bracket simulations')
    parser.add_argument('--truth_file', type=str, 
                        default='',
                        help='forecast file for generating picks')
    parser.add_argument('--out_dir', type=str, default='./truth/scenarios/',
                        help='Directory to write truth files')
    parser.add_argument('--round', type=int, default=1,
                        help='Round for which to generate scenarios')
    args = parser.parse_args()


# python create_scenario_files.py --truth_file ./truth/rd2.truth --out_dir ./truth/scenarios/rnd3 --round 3
# python create_scenario_files.py --truth_file ./truth/history/round3_game04.truth --out_dir ./truth/scenarios/rnd3_3 --round 3
# python create_scenario_files.py --truth_file ./truth/final4.truth --out_dir ./truth/scenarios/rnd5 --round 5

    forecast = Forecast(args.forecast_file, args.truth_file)
    create_scenario_files(args.round, args.out_dir, forecast)


