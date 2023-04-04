#!/usr/bin/env python

import csv
from scipy.special import erfinv, erf
from random import uniform
from statistics import median 
import glob, os
from scipy.stats import rankdata 
import numpy as np
import urllib.request
import copy
import time
import pdb

def yahoo_order():
    #return [1,5,11,4,0,7,9,13,8,6,3,12,2,10]
    return [1,2,10, 12,5,0,7,8,6,11,4,13,3,9]

class CompetitionResults:
    def __init__(self, d, ncases, forecast_file, source, use_bonus, option, results_out_dir, initial_truth_file=''):
        self.results_out_dir = results_out_dir
        self.initial_truth_file = initial_truth_file
        if type(option) is str:
            self.results_file = option
            if initial_truth_file:
                self.forecast = Forecast(forecast_file, initial_truth_file)
            else:
                self.forecast = Forecast(forecast_file)
            self.write_truth_files()
        elif type(option) is int:
            self.n_rnd = option
            self.forecast_file = forecast_file
            self.forecast = Forecast(forecast_file, initial_truth_file)
            self.write_truth_scenario_files()

        self.competitions = []
        self.truth_files = []

        first = True
        for truth_file in os.listdir(results_out_dir):
            if truth_file.endswith(".truth"):
                tf = os.path.join(results_out_dir, truth_file)
                print(tf)
                self.truth_files.append(tf)
                if first:
                    curr = Compete(d, ncases, forecast_file, tf, source, use_bonus)
                    first = False
                else:
                    curr.reload(ncases, forecast_file, tf)
                self.competitions.append(copy.copy(curr))

    def write_truth_scenario_files(self):
        n_rnd = self.n_rnd
        out_dir = self.results_out_dir
        bracket = resolve_bracket(self.forecast.first_games)
        rnd = bracket[n_rnd-1]
        self.scenarios = []
        scenario_count = 1
        game_count = 1
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        outfile = os.path.join(out_dir, 'scenario00.truth')
        self.scenarios.append(self.initial_truth_file)
        write_truth_file(outfile, self.forecast)
        for game in rnd:
            team1 = self.forecast.teams[game['team1']['team_id']]
            team2 = self.forecast.teams[game['team2']['team_id']]
            if team1['final_round'] == -1 and team2['final_round'] == -1:
                outfile = os.path.join(out_dir, 'scenario{:02d}.truth'.format(scenario_count))
                forecast = Forecast(self.forecast_file, self.initial_truth_file)
                winner = game['team1']['team_name']
                loser  = game['team2']['team_name']
                forecast.teams[game['team2']['team_id']]['final_round'] = n_rnd
                self.scenarios.append('Round {} Game {}A: {} defeats {}'.format(n_rnd, game_count, winner, loser))
                write_truth_file(outfile, forecast)
                scenario_count += 1

                outfile = os.path.join(out_dir, 'scenario{:02d}.truth'.format(scenario_count))
                forecast = Forecast(self.forecast_file, self.initial_truth_file)
                winner = game['team2']['team_name']
                loser  = game['team1']['team_name']
                forecast.teams[game['team1']['team_id']]['final_round'] = n_rnd
                self.scenarios.append('Round {} Game {}B: {} defeats {}'.format(n_rnd, game_count, winner, loser))
                write_truth_file(outfile, forecast) 
                scenario_count += 1
            game_count += 1


    def get_game(self, competition):
        truth_file = competition.forecast.truth_file
        if truth_file.find('round') >= 0 and truth_file.find('game') >= 0:
            i = int(truth_file[-14])
            j = int(truth_file[-8:-6])
            if i == 0 and j == 0:
                return "initial"
            else:
                curr_id = self.result_ids[i-1][j-1]
               # bracket = competition.mcc.brackets[0]
                bracket = resolve_bracket(competition.forecast.first_games)
                rnd = bracket[i-1]
                for game in rnd:
                    if game['team1']['team_id'] == curr_id:
                        loser =  game['team1']['team_name']  
                        winner = game['team2']['team_name']  
                        break
                    if game['team2']['team_id'] == curr_id:
                        loser =  game['team2']['team_name']  
                        winner = game['team1']['team_name']  
                        break
                return 'Round {} Game {}: {} defeats {}'.format(i,j,winner, loser)
        elif truth_file.find('scenario') >=0:
            i = int(truth_file[-8:-6])
            return self.scenarios[i]
        else:
            print(truth_file)
            return ''
 
    def write_to_file(self, out_file, order=''):
        if not order:
            order = range(0, len(self.competitions[0].names))
        out = ''
        with open(out_file, 'wt') as f:
            out += 'Probability of Winning\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:10.4f},'.format(c.mcc.pwin[i]*100)     
                out += '\n'
            out += '\n'
            out += 'Probability of Losing\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:10.4f},'.format(c.mcc.plose[i]*100)
                out += '\n'
            out += '\n'
            out += 'Best Finish\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.mcc.best_finish[i])
                out += '\n'
            out += '\n'
            out += 'Worst Finish\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.mcc.worst_finish[i])
                out += '\n'
            out += '\n'
            out += 'Min Score\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.mcc.min_scores[i])
                out += '\n'
            out += '\n'
            out += 'Max Score\n'
            out += self.names(order)
            for c in self.competitions:
                out += '{:10},'.format(self.get_game(c))
                for i in order:
                    out += '{:6.0f},'.format(c.mcc.max_scores[i])     
                out += '\n'
            f.write(out)

    def names(self,order):
        out = ','
        for i in order:
            out += '{},'.format(self.competitions[0].names[i])
        out += '\n'
        return out
        

    def write_truth_files(self):
        results_file = self.results_file
        forecast = self.forecast
        out_dir = self.results_out_dir
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        forecast = self.forecast 
        i = -1
        count = 1
        results = []
        result_ids = []
        outfile = os.path.join(out_dir, 'round0_game00.truth')
        write_truth_file(outfile, forecast)
        with open(results_file, 'r') as f:
            for line in f:
                if line[0] == '-':
                    results.append([])
                    result_ids.append([])
                    i += 1
                    count = 1
                else:
                    results[i].append(line.strip())
                    curr_id = name_to_id(line, forecast.idmap, forecast.synonyms)
                    result_ids[i].append(curr_id)
                    if curr_id:
                        forecast.teams[curr_id]['final_round'] = i+1
                        outfile = os.path.join(out_dir, 'round{}_game{:02d}.truth'.format(i+1,count))
                        write_truth_file(outfile, forecast)
                        count += 1
        self.results = results
        self.result_ids = result_ids


def write_truth_file(outfile, forecast):
    with open(outfile, 'wt') as fo:
        fo.write('Name, Final Round\n')
        for team_id in forecast.teams:
            team = forecast.teams[team_id]
            if 'final_round' in team:
                frnd = team['final_round']
            else:
                frnd = -1
            fo.write('{},{}\n'.format(team['team_name'], frnd))

def probability_matrix(ranks):
    shp = np.shape(ranks)
    pmat = np.zeros((shp[1], shp[1]))
    for i in range(0, shp[1]): # competitor
        curr = ranks[:,i]
        for j in range(0, shp[1]): # rank
            pmat[i][j] = len(curr[curr==j+1])
    pmat = pmat/shp[0]
    return pmat

def yahoo_html_region(picks):
    return [picks[0:8], picks[8:12], picks[12:14]]

def calc_win_prob(game):
    diff = game['team1']['team_rating'] - game['team2']['team_rating']
    return 0.5*(1+erf(diff/10/2**0.5))

def team_summary(team):
    return '{:5} {:8} {:12}'.format(team['team_seed'], team['team_region'], team['team_name'][0:12])
#    return '{:8} {:12}'.format(team['team_seed'], team['team_name'][0:12])
#    return '{:5} {:8} {:12}'.format(team['final_round'], team['team_seed'], team['team_name'][0:12])

def game_summary(game):
    team1 = game['team1']
    team2 = game['team2']
    out1 = team_summary(team1)
    out2 = team_summary(team2)
    
#    if 'p_win' in game:
#        out1 = '{:6.2f} {}'.format(game['p_win'], out1)
#        out2 = '{:6.2f} {}'.format(1-game['p_win'], out2)
    if 'result' in game:
        if game['result']:
#            out1 = 'L ' + out1
#            out2 = 'W ' + out2
            out = out2
        else:
#            out1 = 'W ' + out1
#            out2 = 'L ' + out2
            out = out1
    else:    
        out = '{} vs {}'.format(out1, out2)
   
#    if 'seed_diff' in game:
#        out = '{} '.format(game['seed_diff']) + out

    if 'win_id' in game:
        out = '{:7} '.format(game['win_id']) + out
    
    return out

def round_summary(rd):
    out = ''
    for game in rd:
        out = out + game_summary(game) + '\n'
    return out

def bracket_summary(bracket):
    out = ''
    i = 1
    for rd in bracket:
        out = out + '------------------------------ Round {} -----------------------------------\n'.format(i)
        out = out + round_summary(rd)
        i += 1
    return out

def champion_summary(brackets):
    idx = len(brackets[0]) - 1
    out = ''
    for bracket in brackets:
        out = out + round_summary(bracket[idx])
    return out


def sort_region(region):
    return [region[0], region[7], region[4], region[3], region[5], region[2], region[6], region[1]]

def resolve_game(game, sample):
# returns index of winning team
# sample must be between 0 and 1
# For monte carlo, sample should be uniformly distributed
# For favorite to win use 1
# For higher rated to win use 0.5
    
    if 'final_round' in game['team1']:
        t1_frnd = game['team1']['final_round']
    else:
        t1_frnd = -1
    
    if 'final_round' in game['team2']:
        t2_frnd = game['team2']['final_round']
    else:
        t2_frnd = -1

    rnd = game['round']    
    if t1_frnd == rnd:
        if t2_frnd > rnd or t2_frnd == -1:
            return 1
        else:
            print(game_summary(game))
    if t2_frnd == rnd:
        if t1_frnd > rnd or t1_frnd == -1:
            return 0
        else:
            print(game_summary(game)) 

    # something doesn't add up
    if t1_frnd > rnd:
        if t2_frnd > rnd:    
            print(game_summary(game))
        else:
            return 0

    if t2_frnd > rnd:
        return 1
 
    if sample <= game['p_win']:
        return 0 # first team wins
    else:
        return 1 # second team wins

def resolve_round(games):
    i = 0
    for game in games:
        games[i]['p_win'] = calc_win_prob(game)
        games[i]['result'] = resolve_game(game, uniform(0,1))
        if games[i]['result']:
            games[i]['win_id'] = games[i]['team2']['team_id']
            games[i]['seed_diff'] = games[i]['team2']['team_seed'] - games[i]['team1']['team_seed']
        else:
            games[i]['win_id'] = games[i]['team1']['team_id']
            games[i]['seed_diff'] = games[i]['team1']['team_seed'] - games[i]['team2']['team_seed']
        i = i+1
    return games

def new_round(last_round):
    games = []
    skip = True
    last_team = {}
    for game in last_round:
        if game['result']:
            team = game['team2']
        else:
            team = game['team1']
        if skip:
            skip = False
        else:
            rnd = game['round']
            games.append({"team1":last_team, "team2":team, "round":rnd+1})
            skip = True

        last_team = team
    return games

   
def resolve_bracket(games):
    bracket = [games]
    i = 0
    while True:
        bracket[i] = resolve_round(bracket[i])
        if len(bracket[i]) <= 1:
            break
        bracket.append(new_round(bracket[i]))
        i = i+1 
               
    return bracket 

def compare_picks_to_bracket(pick_ids, bracket):
    i = 0
    check = []
    for rd in pick_ids:
        j = 0
        check.append([])
#        print('-----')
        for pick_id in rd:
#            print('{} {}'.format(bracket[i][j]['win_id'], pick_id))
            check[i].append(bracket[i][j]['win_id'] == pick_id)
            j += 1
        i += 1
    return check

def score_bracket(check, bracket, use_bonus):
    i = 0
   
    if use_bonus: 
        #bonus_multiplier = [1,1,2,2,3,3]
        bonus_multiplier = [1,1,3,4,5,6]
    else:
        bonus_multiplier = [0,0,0,0,0,0]
    score_by_round = []
    bonus_by_round = []
    score_by_game = []
    bonus_by_game = []
    for rd in check:
        j = 0
        score_by_game.append([])
        bonus_by_game.append([])
        for game in rd:
            score_by_game[i].append(game*2**i)
            temp_bonus = game*bracket[i][j]['seed_diff']*bonus_multiplier[i]
            bonus_by_game[i].append(max(0,temp_bonus))
            j += 1
        score_by_round.append(sum(score_by_game[i]))
        bonus_by_round.append(sum(bonus_by_game[i]))
        i += 1
    score = sum(score_by_round)
    bonus = sum(bonus_by_round)
    total = score + bonus
 #   return (score, score_by_round, score_by_game, bonus, bonus_by_round, bonus_by_game, total)
    return (total, score, bonus)            

def pick_id_to_name_lines(pick_ids, forecast):
    i = 1
    out = ''
    s = []
    for rd in pick_ids:
        out += '----- Round {} -----\n'.format(i)
        i += 1
        for team in rd:
           out = out + (team_summary(forecast.teams[team])) + '\n'
#            s.append(team_summary(forecast.teams[team]))
    return out
#    return s


def compete_print_top_bottom(c, n):
    print_top_bottom(c.mcc.medians, n, c.mcc, len(c.picks), c.mcc.ranks.shape[0], c.mcc.picks, c.mcc.forecast)


class Compete:
    def __init__(self, d, ncases, forecast_file, truth_file, source, use_bonus):
        picks = []
        names = []
        self.use_bonus = use_bonus
        if source == 'dir':
            for file in os.listdir(d):
                if file.endswith(".picks"):
                #if file.startswith("top"):
                    print(file)
                    picks.append(Picks(os.path.join(d, file), True))
                    names.append(file)
        elif source == 'yahoo':
            (names, url_codes) = parse_members_table2(d)
            for i in range(0, len(names)):
                url = 'https://tournament.fantasysports.yahoo.com/t1/' + url_codes[i]
                print(url_codes[i] + ' ' + names[i])
                picks.append(Picks(url))
        self.picks = picks        
        self.names = names
        self.forecast = Forecast(forecast_file, truth_file)
        self.mcc = MCcompete(self.picks, self.forecast, self.use_bonus)
        self.mcc.run_MC(ncases)
#        self.analyze_competition()

    def print_round(self, rnd):
        out = ''
        for i in range(0, len(self.picks)):
            out += '{:30}'.format(self.names[i])
            for team in self.picks[i].picks[rnd-1]:
                out += '{:15}'.format(team[0:14])
            out += '\n' 
        print(out)

    def reload(self, ncases, forecast_file, truth_file):
        self.forecast = Forecast(forecast_file, truth_file)
        self.mcc = MCcompete(self.picks, self.forecast, self.use_bonus)
        self.mcc.run_MC(ncases)
#        self.analyze_competition()
    
    def write_all_picks(self, d):
        os.makedirs(d)
        for i in range(0, len(self.picks)):
            self.picks[i].write_picks(os.path.join(d,self.names[i]+'.picks'))

    def analyze_competition(self):
        print(self.forecast.forecast_file)
        print(self.forecast.truth_file)
        print(self.mcc.ncases)
        print('{:30},{:10},{:10},{:10},{:10},{:10},{:10}'.format('Bracket Name', 'min score', 'max score', 'P lose', 'P win', 'min rank', 'max rank'))
      #  self.mcc.curr_order = [7,13,10,2,9,5,12,4,1,11,8,12,3,0,6]
      #  self.mcc.curr_order = range(0,14)]
      #  for i in self.mcc.curr_order:
        for i in range(0,len(self.names)):
            print('{:30},{:10.0f},{:10.0f},{:10.1f},{:10.1f},{:10.0f},{:10.0f}'.format(self.names[i], self.mcc.min_scores[i], self.mcc.max_scores[i], self.mcc.plose[i]*100, self.mcc.pwin[i]*100, self.mcc.worst_finish[i], self.mcc.best_finish[i]))

     
def write_pmat(pmat, names, fname):
    with open(fname, 'wt') as f:
        out = '{:30} '.format('')
        for i in range(0, len(names)):
            out += '{:8.0f}'.format(i+1)
        f.write(out + '\n')
        for i in range(0, len(names)):
            out = '{:30} '.format(names[i])
            for j in range(0, len(names)):    
                out += '{:8.1f}'.format(pmat[i][j]*100)
            f.write(out + '\n')


def yahoo_sort_teams(teams):
    # South = yahoo_html_region(teams[0:])
    # West = yahoo_html_region(teams[14:])
    # East  = yahoo_html_region(teams[35:])
    # Midwest = yahoo_html_region(teams[49:])
    East = yahoo_html_region(teams[0:])
    Midwest = yahoo_html_region(teams[14:])
    West  = yahoo_html_region(teams[28:])
    South = yahoo_html_region(teams[42:])

    x = []
    for i in range(len(South)):
        x.append(East[i] + Midwest[i] + West[i] + South[i])
    x.append(teams[56:60]) # Final Four
    x.append(teams[60:62]) # Finals
    x.append(teams[62:63]) # Champion
    return x

def yahoo_parse_line(line):
    a = line.split('user-pick">')
    b = a[1].split('</em>')
    c = b[1].split('</b>')
    return c[0]

def parse_yahoo_group(group):
    url = 'https://tournament.fantasysports.yahoo.com/t1/group/' + str(group)
    response = urllib.request.urlopen(url)
    f = open('tmp', 'wt')
    s = []
    for linebyte in response:
        line = str(linebyte)
        f.write(line + '\n') 
        if line.find('members_table') > 0:
            s.append(line)
    f.close()
    return(s)

def parse_members_table(fname):
    with open(fname, 'r') as f:
        s = f.readline()
        a = s.split('href')
        names = []
        urls = []
        for entry in a:
            if entry[0:6] == '="/t1/':
                b = entry.split('>')
                name = b[1][0:-3]
                c = b[0].split('"')
                url = c[1][4:]
                urls.append(url)
                names.append(name)
    return (names, urls)

def parse_members_table2(fname):
    with open(fname, 'r') as f:
        s = f.readline()
        a = s.split('href')
        names = []
        urls = []
        renames = member_renames()
        for entry in a:
            if entry[0:15] == '="http://profil':
                d = entry.split('>')
                name = d[1][0:-3]
                if name in renames:
                    name = renames[name]
                names.append(name)
            if entry[0:6] == '="/t1/':
                b = entry.split('>')
               # name = b[1][0:-3]
                c = b[0].split('"')
                url = c[1][4:]
                urls.append(url)
               # names.append(name)
    return (names, urls)

def member_renames():
    return {"Gregory": "Greg", 
            "Raj arshi": "Raj",
            "Andrew": "Drew",
            "mark Van de": "Mark",
            "duncanm": "Duncan",
            "Nicholas Galano": "Nick"}     


def print_top_bottom(grade, n, mcc, npicks, ncases, pick_brackets, forecast):
    idx_sort = sorted(range(len(grade)), key=lambda k: grade[k])
    idx_sort = idx_sort
    for i in range(0,n):
        j = idx_sort[-i-1]
        write_bracket_to_file(j, 'top{}'.format(i+1), mcc, npicks, ncases, pick_brackets, forecast)
        j = idx_sort[i]
        write_bracket_to_file(j, 'bottom{}'.format(i+1), mcc, npicks, ncases, pick_brackets, forecast)

def write_bracket_to_file(j, fname, mcc, npicks, ncases, pick_brackets, forecast):
    with open(fname, 'wt') as f:
        # f.write('pwin: {}\n'.format(self.mcc.pwin[j]))
        # f.write('max_score: {}\n'.format(self.mcc.max_scores[j]))
        f.write('median: {}\n'.format(mcc.medians[j]))
        # f.write('max_bonus: {}\n'.format(self.mcc.max_bonus[j]))
        # f.write('max_no_bonus: {}\n'.format(self.mcc.max_no_bonus[j]))
        # f.write('min_bonus: {}\n'.format(self.mcc.min_bonus[j]))
        # f.write('min_no_bonus: {}\n'.format(self.mcc.min_no_bonus[j]))
        f.write('mean_finish: {}\n'.format(mcc.mean_finish[j]/npicks))
        f.write('median_finish: {}\n'.format(mcc.median_finish[j]/npicks))

        curr_ranks = mcc.ranks[:,j]
        top20 = np.count_nonzero(curr_ranks <= npicks*20/100)/ncases
        f.write('top20: {}\n'.format(top20))
        top10 = np.count_nonzero(curr_ranks <= npicks*10/100)/ncases
        f.write('top10: {}\n'.format(top10))
        top5 = np.count_nonzero(curr_ranks <= npicks*5/100)/ncases
        f.write('top5: {}\n'.format(top5))
        top2 = np.count_nonzero(curr_ranks <= npicks*2/100)/ncases
        f.write('top2: {}\n'.format(top2))

        f.write(pick_id_to_name_lines(pick_brackets[j].pick_ids, forecast))

class SearchPicks:
    def __init__(self, f1, f2, ncases, npicks, old_method=False):
        self.forecast = Forecast(f1)
        self.pick_forecast = Forecast(f2)
        self.ncases = ncases
        self.npicks = npicks


        if old_method:
            print('old method ZZZ')
            self.old_method()
        else:
            print('new method')
            self.new_method()

#        brackets = []
#        for i in range(0,ncases):
#            brackets.append(resolve_bracket(self.forecast.first_games))
#
#        pick_brackets = []
#        scores = []
#        medians = []
#        for i in range(0,npicks):
#            pick_brackets.append(RandomPicks(self.pick_forecast))
#            scores.append([])
#            for bracket in brackets:
#                check = compare_picks_to_bracket(pick_brackets[i].pick_ids, bracket)
#                scores[i].append(score_bracket(check, bracket))
#            medians.append(median(scores[i])) 
#            print(npicks-i)
#
#        self.brackets = brackets
#        self.pick_brackets = pick_brackets
#        self.scores = scores
#        self.grade = medians
#        self.print_top_bottom(1) 

    def new_method(self):
        self.pick_brackets = []
        medians = []
        print('Getting picks')
        for i in range(0, self.npicks):
            self.pick_brackets.append(RandomPicks(self.pick_forecast))
     
        print("Running MC")
        self.mcc = MCcompete(self.pick_brackets, self.forecast, True)
        self.mcc.run_MC(self.ncases, verbose=True)
        self.grade = self.mcc.medians

    def old_method(self):
        pick_brackets = []
        medians = []
        last_time = time.time()
        for i in range(0, self.npicks):
            pick_bracket = RandomPicks(self.pick_forecast)
            mc = MC(pick_bracket, self.forecast, True)
            mc.run_MC(self.ncases)
            medians.append(median(mc.scores[0]))
            pick_brackets.append(pick_bracket)

            curr_time = time.time()
            dt = curr_time - last_time
            last_time = curr_time
            time_remaining = (self.npicks-i)*dt/60
            print("{:4.0f}, {:4.02f} seconds elapsed, {:4.01f} minutes remaining".format(self.npicks-i, dt, time_remaining))

        self.grade = medians
        self.pick_brackets = pick_brackets
        #self.print_top_bottom(3) 

    def print_top_bottom_old(self, n):
        idx_sort = sorted(range(len(self.grade)), key=lambda k: self.grade[k])
        self.idx_sort = idx_sort
        for i in range(0,n):
            j = idx_sort[-i-1]
            self.write_bracket_to_file_old(j, 'top{}'.format(i+1))
            j = idx_sort[i]
            self.write_bracket_to_file_old(j, 'bottom{}'.format(i+1))

    def write_bracket_to_file_old(self, j, fname):
        with open(fname, 'wt') as f:
            f.write('median: {}\n'.format(self.grade[j]))
            f.write(pick_id_to_name_lines(self.pick_brackets[j].pick_ids, self.forecast))

    # def print_top_bottom_new(self, n):
    #     idx_sort = sorted(range(len(self.mcc.pwin)), key=lambda k: self.mcc.pwin[k])
    #     self.idx_sort = idx_sort
    #     for i in range(0,n):
    #        with open('top{}'.format(i+1), 'wt') as f:
    #             j = idx_sort[-i-1]
    #             f.write('{}\n'.format(self.mcc.pwin[j]))
    #             f.write(pick_id_to_names(self.pick_brackets[j].pick_ids, self.forecast))
    #        with open('bottom{}'.format(i+1), 'wt') as f:
    #             j = idx_sort[i]
    #             f.write('{}\n'.format(self.mcc.pwin[j]))
    #             f.write(pick_id_to_names(self.pick_brackets[j].pick_ids, self.forecast))


    def correlate(self,  i_rd, i_game):
        ids = []
        ratings = []
        seeds = []
        for bracket in self.pick_brackets:
            curr_id = bracket.pick_ids[i_rd][i_game]
            ids.append(curr_id)
            team = self.forecast.teams[curr_id]
            ratings.append(team['team_rating'])
            seeds.append(team['team_seed'])
        return (ids, ratings, seeds)


class RandomPicks:
    def __init__(self, forecast):
#        self.forecast = Forecast(f) 
        self.forecast = forecast
        picks_as_bracket = resolve_bracket(self.forecast.first_games)
        pick_ids = []
        i = 0
        for rd in picks_as_bracket:
            pick_ids.append([])
            j = 0
            for game in rd:
                pick_ids[i].append(picks_as_bracket[i][j]['win_id'])
                j += 1
            i += 1
        self.pick_ids = pick_ids
#        self.mc = MC(self, self.forecast)
#        self.mc.run_MC(100)
       

def check_picks(picks):
    n = len(picks)
    i = 0
    for rd in picks:
        l = len(rd)
        expect = 2**(n-i-1)
        if l != expect and l > 0:
            print('Expected {} Found {}'.format(expect, l))
        i += 1

 
class MCcompete:
    def __init__(self, picks, forecast, bonus):
        self.forecast = forecast
        self.picks = picks
        self.use_bonus = bonus
 
        j = 0
        for j in range(len(self.picks)):
            if not hasattr(self.picks[j], 'pick_ids'):
                self.picks[j].convert_picks_to_id(self.forecast.idmap, self.forecast.synonyms) 

        #for picks in self.picks:
        #    check_picks(picks.picks)

    def run_MC(self, ncases, verbose=True):
        brackets = []
        scores = np.zeros((ncases, len(self.picks)))
        no_bonus = np.zeros((ncases, len(self.picks)))
        bonus = np.zeros((ncases, len(self.picks)))
        ranks = np.zeros((ncases, len(self.picks)))
        ranks2 = np.zeros((ncases, len(self.picks)))
        bracket_arrays = []
        last_time = time.time()
        print('Start simulations')
        for i in range(0, ncases): # case
            curr_time = time.time()
            dt = curr_time - last_time
            last_time = curr_time
            time_remaining = (ncases-i)*dt/60
            if verbose and i%1000 == 0:
                print("{:4.0f}, {:4.02f} seconds elapsed, {:4.01f} minutes remaining".format(ncases-i, dt, time_remaining))
            bracket = resolve_bracket(self.forecast.first_games)
            brackets.append(bracket)
            for j in range(0,len(bracket)): # round
                if i == 0: # first cas
                    bracket_arrays.append(np.zeros((ncases,len(bracket[j]))))
                for k in range(0, len(bracket[j])): # game
                    bracket_arrays[j][i,k] = bracket[j][k]['win_id']

            for j in range(0, len(self.picks)):
                check = compare_picks_to_bracket(self.picks[j].pick_ids, bracket)
                (scores[i,j], no_bonus[i,j], bonus[i,j]) = score_bracket(check, bracket, self.use_bonus)
                       
            ranks[i,:]  = len(self.picks) + 1 - rankdata(scores[i,:], 'max')
            ranks2[i,:] = len(self.picks) + 1 - rankdata(scores[i,:], 'min')

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
        self.brackets = brackets
        self.bracket_arrays = bracket_arrays
        self.scores = scores 
        self.no_bonus = no_bonus
        self.bonus = bonus
        self.ranks = ranks 
        self.ncases = ncases
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
  

    def analyze_brackets(self):
        teams = self.forecast.teams
        self.p_win = np.zeros((len(teams), len(self.bracket_arrays)))
        i = 0
        team_ids = [] 
        for team_id in teams:
            j = 0
            team_ids.append(team_id)
            for ba in self.bracket_arrays:
                p = probability_in_round(ba, team_id)
                self.p_win[i,j] = p 
                j += 1
            i += 1

        p_win_sort = self.p_win
        full_sort_idx = np.arange(0, len(teams)) 
        for i in range(0,5):
            sort_idx = np.argsort(p_win_sort[:,i])
            p_win_sort = p_win_sort[sort_idx,:]
            full_sort_idx = full_sort_idx[sort_idx]
        full_sort_idx = full_sort_idx[::-1]
        for i in full_sort_idx: 
            out = '{:30}'.format(teams[team_ids[i]]['team_name'])
            for j in range(0,len(self.p_win[i,:])):            
                out += '{:4.0f}'.format(self.p_win[i][j]*100)
            print(out)

def probability_in_round(bracket_array, team_id):
    return len(bracket_array[bracket_array==team_id])/bracket_array.shape[0]

class MC:
    def __init__(self, picks, forecast, use_bonus):
        self.forecast = forecast
        self.picks = picks
        self.use_bonus = use_bonus
        if not hasattr(self.picks, 'pick_ids'):
            self.picks.convert_picks_to_id(self.forecast.idmap, self.forecast.synonyms) 


    def run_MC(self, ncases):
        brackets = []
        checks = []
        scores = []
        for i in range(0, ncases):
            bracket = resolve_bracket(self.forecast.first_games)
            #self.picks.pick_ids = perfect_picks(bracket)
            check = compare_picks_to_bracket(self.picks.pick_ids, bracket)
            score = score_bracket(check, bracket, self.use_bonus)
            brackets.append(bracket)
            checks.append(check)
            scores.append(score)
                       
        self.brackets = brackets
        self.checks = checks
        self.scores = scores 
        self.ncases = ncases

def perfect_picks(bracket):
    pick_ids = []
    for rnd in bracket:
        rnd_picks = []
        for game in rnd:
            if game['result']:
                rnd_picks.append(game['team2']['team_id'])
            else:
                rnd_picks.append(game['team1']['team_id'])
        pick_ids.append(rnd_picks)
    return pick_ids


class Picks:
    def __init__(self, fname, alt = False):
        teams = []
        if fname[0:4] == 'http':
            response = urllib.request.urlopen(fname)
            for linebyte in response:
                line = str(linebyte)
                if line.find('user-pick') > 0:
                    if line.find('Real Winner') == -1 and line.find('None') == -1:
                        teams.append(yahoo_parse_line(line)) 
            picks = yahoo_sort_teams(teams)
            self.picks = picks
            self.teams = teams

        else:   
            if alt:
                self.read_picks_alt(fname)
            else:
                self.read_picks(fname)
   
    def write_picks(self, outname):
        with open(outname, 'wt') as f:
            f.write('?\n')
            for rnd in self.picks:
                f.write('-\n')    
                for team in rnd:
                    f.write(team.strip() + '\n')
   
    def read_picks_alt(self,fname):
        picks = []
        i = -1
        initialized = False
        with open(fname, 'r') as f:
            for line in f:
                if not initialized and line[0] == '-':
                    initialized = True
                if initialized:
                    if line[0] == '-':
                        picks.append([])
                        i += 1
                    else:
                        words = line.split()
                        #picks[i].append(' '.join(words[2:]))
                        picks[i].append(line.strip())
                       
        self.picks = picks 
 
    def read_picks(self,fname):
        picks = []
        with open(fname, 'r') as f:
            reader = csv.reader(f)
            header = []
            for row in reader:
                if not header:
                    header = row
                    for col in header:
                        picks.append([])
                else:
                    i = 0
                    for col in row:
                        if col:
                            picks[i].append(col)
                        i += 1
        self.picks = picks
        
    def convert_picks_to_id(self, idmap, synonyms={}):
        pick_ids = [] 
        i = 0
        for rd in self.picks:
            pick_ids.append([])
            for pick in rd:
                pick_id = name_to_id(pick, idmap, synonyms)
                if pick_id:
                    pick_ids[i].append(pick_id)
            i += 1
        self.pick_ids = pick_ids

def name_to_id(name, idmap, synonyms={}):                
    name = name.lower().strip()
    if name in synonyms:
        name = synonyms[name].lower().strip()
    if name in idmap:
        return idmap[name]
    else:
        print('"{}" not found in forecast bracket'.format(name)) 
        return []


class Forecast:
    def __init__(self, fname, truth_file=''):
        self.get_synonyms()
        self.read_forecast(fname)
        self.make_name_to_id_lookup()
        self.truth_file = truth_file
        if truth_file:
            self.add_truth(truth_file)
        self.hardcode_first_round() 
        self.find_first_games()
#        self.check_fit()
        self.sort_first_games()
#        self.rd1 = resolve_round(self.first_games)
#        self.rd2 = new_round(self.rd1)
#        self.bracket = resolve_bracket(self.first_games)

    def add_truth(self, truth_file):
        truth_list = []
        with open(truth_file, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            header = []
            for row in reader:
                if not header:
                    header = row
                else:
                    row[1] = int(row[1])
                    truth_list.append(row)
                    curr_id = name_to_id(row[0], self.idmap, self.synonyms)
                    if curr_id:
                        self.teams[curr_id]['final_round'] = int(row[1])
                    else:
                        print('WTF')
        self.truth_list = truth_list

    def write_first_round_to_file(self, fname='first_round.csv'):
        with open(fname, 'wt') as f:
            for game in self.first_games:
                f.write(game['team1']['team_name'] + '\n')
                f.write(game['team2']['team_name'] + '\n')
    
    def sort_first_games(self):
        m = self.first_games
        mp = sorted(m, key=lambda k:k['team1']['team_seed'])
        mpp = sorted(mp, key=lambda k:k['team1']['team_region'])
        #print(mpp)
        #print(len(mpp))
        East = sort_region(mpp[0:8])
        Midwest = sort_region(mpp[8:16])
        South = sort_region(mpp[16:24])
        West = sort_region(mpp[24:32])
         
        self.first_games = East + Midwest + West + South


    def hardcode_first_round(self):
# 2428,North Carolina Central,71.04,Midwest,16a
# 302,UC-Davis,69.94,Midwest,16b

# 116,Mount St. Mary's,69.78,East,16a
# 2443,New Orleans,69.24,East,16b

# 2507,Providence,81.75,East,11a
# 30,Southern California,81.18,East,11b

# 2306,Kansas State,83.08,South,11a
# 154,Wake Forest,82.96,South,11b

        pdb.set_trace()
        self.teams.pop(2428)  # North Carolina Central
        self.teams.pop(2443)  # New Orleans
        self.teams.pop(2507)  # Providence
        self.teams.pop(154) # Wake Forest
        for team in self.teams:
            if team == 302 or team == 116 or team == 30 or team == 2306:
                self.teams[team]['team_seed'] = float(self.teams[team]['team_seed'][0:2])
                self.teams[team]['playin_flag'] = 0

    def check_fit(self):
        games = self.first_games
        i = 0
        for game in games:
            diff = game['team1']['team_rating'] - game['team2']['team_rating']
            p_win = game['team1']['rd2_win']

            nsigma = 2**0.5*erfinv(2*p_win-1)
            sigma = diff/nsigma
            est = 0.5*(1+erf(diff/10/2**0.5))
            error = est - p_win 

            games[i]['diff'] = diff
            games[i]['nsigma'] = nsigma
            games[i]['sigma'] = sigma
            games[i]['est'] = est
            games[i]['error'] = error

            i = i + 1
        self.first_games = games

    def find_first_games(self):
        teams = self.teams
        games = []
        for teamid in teams:
            team = teams[teamid]
            if team['playin_flag']:
               print(team['team_name'])
            else:
                if team['team_seed'] <= 8:
                    for teamid2 in teams:
                        team2 = teams[teamid2]
                        if team2['team_region'] == team['team_region']:
                            if not team2['playin_flag']:
                                if team['team_seed'] + team2['team_seed'] == 17:
                                    games.append({"team1":team, "team2":team2, "round": 1}) 
        self.first_games = games

    def read_forecast(self, fname):
        teams = {}
        self.forecast_file = fname
        with open(fname, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            header = []
            for row in reader:
                if not header:
                    header = row
                else:
                    if row[0] == 'mens':
                        pdb.set_trace()
                        curr_id = int(row[11])
                        teams[curr_id] = {}
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
                            teams[curr_id][header[i]] = curr
                            i = i + 1
        self.teams = teams

    def make_name_to_id_lookup(self):
        self.idmap = {}
        for teamid in self.teams:
            team = self.teams[teamid]
            self.idmap[team['team_name'].lower()] = team['team_id']
        
    
    def get_synonyms(self):
        s = {
             'cal': 'california', 
             'wichita st.': 'wichita state',
             'miami': 'miami (fl)', 
             "saint joe's": "saint joseph's",
             'unc': 'north carolina',
             'usc': 'southern california',
             'uva': 'virginia',
             'uconn': 'connecticut',
             's. dakota st.': 'south dakota state',
             'unc-wilm.': 'north carolina-wilmington',
             'n. iowa': 'northern iowa',
             'vcu': 'virginia commonwealth',
             'chatt.': 'chattanooga',
             'w. virginia': 'west virginia',
             'ark.-lr': 'arkansas-little rock',
             'virginia com': 'virginia commonwealth',
             'north caroli': 'north carolina',
             'west virgini': 'west virginia',
             'michigan sta': 'michigan state',
             'south dakota': 'south dakota state',
             'wichita stat': 'wichita state',
             'northern iow': 'northern iowa',
             'stephen f. a': 'stephen f. austin',
             'arkansas-lit': 'arkansas-little rock',
             'southern cal': 'southern california',
              'florida gulf': 'florida gulf coast',
             'n. c. wilmington': 'north carolina-wilmington',
             'fresno st.': 'fresno state',
             'n. carolina': 'north carolina',
             'ar little rock': 'arkansas-little rock',
             'iowa st.': 'iowa state',
             'michigan st.': 'michigan state',
             'sf austin': 'stephen f. austin',
             'wichita st': 'wichita state',
             'n carolina': 'north carolina',
             'michigan st': 'michigan state',
             'oregon st.': 'oregon state',
             'n.c. wilmington': 'north carolina-wilmington',
             's.f. austin': 'stephen f. austin',
             "st. joseph\\'s": "saint joseph's",
             "texas am": "texas a&m",
             "saint joes": "saint joseph's",
             "pitt": "pittsburgh",
             "ky": "kentucky",
             "mich st": "michigan state",
             "okla": "oklahoma",
             "west v": "west virginia",
             "nova": "villanova",
             "iowa st": "iowa state",
             "ar-little rock": "arkansas-little rock",
             "zona": "arizona",
             "oregon st": "oregon state",
             "unc wilmington": "north carolina-wilmington",
             "unc-wilm": "north carolina-wilmington",
             "fgcu": "florida gulf coast",
             "unc-ash.": "north carolina-asheville",
             "csu bakers.": "cal state bakersfield",
             "mid. tenn.": "middle tennessee",
             "saint joseph": "saint joseph's", 
             "saint mary\\'s": "saint mary's (ca)",
             "saint mary's": "saint mary's (ca)",
             "southern met": "southern methodist",
             "south caroli": "south carolina",
             "new mexico s": "new mexico state",
             "virginia tec": "virginia tech", 
             "northern ken": "northern kentucky", 
             "florida stat": "florida state",
             "middle tenne": "middle tennessee",
             "oklahoma sta": "oklahoma state",
             "east tenness": "east tennessee state",
             "jacksonville": "jacksonville state",
             "texas southe": "texas southern",
             "mount st. ma": "mount st. mary's",
             "florida st.": "florida state",
             "smu": "southern methodist",
             "middle tenn. st.": "middle tennessee",
             "fla gulf coast": "florida gulf coast",
             "e. tennessee st.": "east tennessee state",
             "kansas st.": "kansas state",
             "n. mex. st.": "new mexico state",
             "st. mary\\'s": "saint mary's (ca)",
             "oklahoma st.": "oklahoma state"
             }

 
        self.synonyms = s 

def champions(brackets):
    champions = []
    runnerups = []
    for bracket in brackets:
        game = bracket[-1][0]
        if game['result'] == 0:
            champ = game['team1']['team_name']
            runnerup = game['team2']['team_name']
        else:
            champ = game['team2']['team_name']
            runnerup = game['team1']['team_name']

        champions.append(champ)
        runnerups.append(runnerup)
    return champions, runnerups

def probabilities(brackets, forecast):
    champs, runnerups = champions(brackets)
    L = len(champs)
    counts = []
    for team in forecast.teams:
        name = forecast.teams[team]['team_name']
        counts.append((name, champs.count(name)/L))

    counts.sort(key=lambda tup: tup[1])
    #print('{}: {:.2f}'.format(name, n/L))
    return counts


def avg(L):
    return(sum(L)/len(L))

def scores_by_round(scores):
    score64 = []
    score32 = []
    score16 = []
    score8 = []
    score4 = []
    score2 = []
    for score in scores:
        score64.append(score[3][0])
        score32.append(score[3][1])
        score16.append(score[3][2])
        score8.append(score[3][3])
        score4.append(score[3][4])
        score2.append(score[3][5])
    return [avg(score64), avg(score32), avg(score16), avg(score8), avg(score4), avg(score2)]


