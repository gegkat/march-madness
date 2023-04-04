import pdb
import forecast
import yahoo_parsing

def read_from_file(fname):
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
                    picks[i].append(line.strip())
                   
    return picks 
 

class Picks:
    def __init__(self, fname, url=''):
        self.name = fname
        if len(url) > 0:
            self.picks = yahoo_parsing.parse_bracket(url)
            self.write_to_file()
        else:   
            self.picks = read_from_file(fname)
   
    def write_to_file(self):
        with open(self.name, 'wt') as f:
            f.write('?\n')
            for rnd in self.picks:
                f.write('-\n')    
                for team in rnd:
                    f.write(team.strip() + '\n')
   
    def convert_to_id(self, forecast):
        pick_ids = [] 
        for rd in self.picks:
            for pick in rd:
                pick_ids.append(forecast.name_to_id(pick))
        return pick_ids

    def __str__(self):
        out = self.name + '\n'
        for rd in self.picks:
            out += '-------------------------\n'
            for team in rd:
                out += team + '\n'
        return out
        
