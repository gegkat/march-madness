import urllib.request
import os
import picks 
import pdb
from bs4 import BeautifulSoup

TAG = 'mens-basketball-bracket'
BASE_URL = 'https://tournament.fantasysports.yahoo.com/' + TAG + '/'

def run_yahoo_parsing(picks_dir):
    if not os.path.isdir(picks_dir):
        os.makedirs(picks_dir)

    members_table = picks_dir + '/members_table'
    if not os.path.isfile(members_table):
        group_id = 9471
        parse_group(group_id, members_table)

    names, url_codes = parse_members_table(members_table)
    picks_list = []
    for i, name in enumerate(names):
        url = BASE_URL + url_codes[i]
        print(url_codes[i] + ' ' + name)
        fname = os.path.join(picks_dir, name + '.picks')
        picks_list.append(picks.Picks(fname, url=url))

    return picks_list

def get_team_key(team_str):
    for text in team_str.split('"'):
        if text.find("ncaab.t.") >= 0:
            return text

def get_team_name(team_str):
    for text in team_str.split(','):
        if text.find("displayName") >= 0:
            return text.split('"')[3]

def get_pick(pick_str, id_to_name):
    split_on_quote = pick_str.split('"')
    split_on_underscore = split_on_quote[1].split("_")
    region_id = int(split_on_underscore[0])
    game_id = int(split_on_underscore[1])
    for text in split_on_quote:
        if text.find("ncaab.t.") >= 0:
            return (region_id, game_id, id_to_name[text])

def parse_picks_by_id(line, id_to_name):
    end_picks_str = line.find('}}}')
    picks_str = line[12:end_picks_str]
    pick_map = {}
    pick_map[0] = ['']*3
    for i in range(1, 5):
        pick_map[i] = ['']*15
    for pick_str in picks_str.split("},"):
        pick = get_pick(pick_str, id_to_name)
        pick_map[pick[0]][pick[1]-1] = pick[2]
    order1 = [1, 2, 3, 4]
    order2 = [7, 8, 9, 10, 11, 12, 13, 14, 3, 4, 5, 6, 1, 2, 0]
    teams = []
    for region in order1:
        for index in order2:
            teams.append(pick_map[region][index])
    teams.append(pick_map[0][1])
    teams.append(pick_map[0][2])
    teams.append(pick_map[0][0])

    return teams

def parse_tournament_teams(line):
    end_tournament_teams = line.find(']')
    tournament_teams_str = line[:end_tournament_teams]
    id_to_name = {}
    for team in tournament_teams_str.split("}},{"):
        id_to_name[get_team_key(team)] = get_team_name(team)
    loc = line.find('picksById')
    return parse_picks_by_id(line[loc:], id_to_name)


def parse_bracket(fname):
    teams = []
    response = urllib.request.urlopen(fname)
    f = open('tmp2', 'w')
    for linebyte in response:
        line = str(linebyte)
        f.write(line)
        loc = line.find('tournamentTeams')
        if loc >= 0:
            teams = parse_tournament_teams(line[loc:])
            break
    teams = sort_teams(teams)
    return teams

def html_region(picks):
    return [picks[0:8], picks[8:12], picks[12:14], picks[14:15]]

def sort_teams(teams):
    ## UPDATE ##
    # Double-check this ordering
    South =    html_region(teams[0:15])
    East =    html_region(teams[15:30])
    Midwest  =  html_region(teams[30:45])
    West = html_region(teams[45:60])

    x = []
    for i in range(len(South)):
        ## UPDATE ##
        # Use order from actual bracket here
        x.append(South[i] + East[i] + Midwest[i] + West[i])
    x.append(teams[60:62]) # Finals
    x.append(teams[62:63]) # Champion
    return x

def parse_line(line):
    a = line.split('user-pick">')
    b = a[1].split('</em>')
    c = b[1].split('</b>')
    pdb.set_trace()
    return c[0]

def parse_group(group, fname):
    url = BASE_URL + 'group/' + str(group)
    response = urllib.request.urlopen(url)
    f = open(fname, 'wt')
    for linebyte in response:
        line = str(linebyte)
        if line.find('<span>Group Leaders</span>') > 0:
            f.write(line + '\n')
    f.close()

def fix_name(name):
    name = name[0].upper() + name[1:]
    name = name.split(' ')[0]
    return name

def parse_members_table(fname):
    with open(fname, 'r') as f:
        s = f.readline()
        a = s.split('href')
        names = []
        urls = []
        for entry in a:
            if entry.startswith('="/' + TAG + '/'):                
                b = entry.split('>')
                c = b[0].split('"')
                d = c[1].split('/')
                url = d[-1]
                name = b[5].split("<")[0]
                if not name: 
                    continue
                try:  
                    # only accept integers
                    int(url)
                    urls.append(url)
                except:
                    continue
                name = fix_name(name)
                names.append(name)
    return (names, urls)
 