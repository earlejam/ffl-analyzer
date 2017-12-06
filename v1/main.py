import os
import glob
import csv
from espnff import League


def create_league(message):
    """Get input from user to fill out the name and members of a new league
    :param message: string, to prompt the user to create the new league
    :return: dict, expected wins (set to 0.0) for each team in the league
    """

    lg_name = input(message).strip()

    lg_id = int(input('Please enter the league id (see the url in any league page): ').strip())

    # create a directory to contain power rankings files for this league
    path_to_league = os.path.join('leagues', '{} ({})'.format(lg_name, lg_id))
    os.mkdir(path_to_league)

    espn_league = League(lg_id, 2017)

    # list of owner names as given by their espn accounts
    owners = [tm.owner for tm in espn_league.teams]

    # key value pairs of an owner and his cumulative expected wins for the season; start with zero
    expected_wins_dict = dict([(owner, 0.0) for owner in owners])

    # avoid creating file with one or more spaces, so silently replace with hyphen
    rankings_filepath = os.path.join(path_to_league, '{}-00.csv'.format(lg_name.replace(' ', '-')))

    # write owner, value to this first file
    with open(rankings_filepath, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(expected_wins_dict.items())

    return lg_name, lg_id, expected_wins_dict


def get_league_files(lg_name, lg_id):
    """Return all of the files associated with this league.
    :param lg_name: string
    :param lg_id: int
    :return: list of filepaths to all league files; meant to be assigned to a dictonary key
    matching the name of the league.
    """

    league_files = glob.glob(os.path.join('leagues', '{} ({})'.format(lg_name, lg_id), '*'))
    league_files.sort(reverse=True)

    return league_files


def get_current_scores(league_obj, week_num):
    """Returns a list of each team's owner and score for the selected week
    :param league_obj: a League(league_id, year) object for espnff
    :param week_num: int, week of the season
    :return: a list of lists; [[owner, score], ... ] sorted highest to lowest
    """

    week_scores = {}
    for matchup in league_obj.scoreboard(week=week_num):
        home = [matchup.home_team, matchup.home_score]
        away = [matchup.away_team, matchup.away_score]
        week_scores[home[0].owner] = home[1]
        week_scores[away[0].owner] = away[1]

    # dict to list of lists
    scores = map(list, week_scores.items())

    # a list of lists [owner, score] for current week, highest to lowest score
    return sorted(scores, reverse=True, key=lambda x: x[1])


print('Welcome to the FFL Power Rankings (Expected Wins) Calculator!')

league_names = os.listdir('leagues')

# first time through the program, need a league on which to operate
if len(league_names) == 0:

    league_name, league_id, expected_wins = create_league('No previously-created leagues found. Please enter a name '
                                                          'for a new league: ')

# indicates that reading from file is required later
else:
    expected_wins = None


# gather existing files for each league; a dictionary of lists, most recent file first
leagues = {}
league_dirs = os.listdir('leagues')


# compile and sort all files for the league
for l_name in league_dirs:
    league_name = l_name.split('(')[0].strip()
    league_id = int(l_name.split('(')[-1].split(')')[0])

    # only use league name so users don't need to enter full string when selecting
    curr_lg_files = get_league_files(league_name, league_id)
    leagues[league_name] = curr_lg_files


# display existing leagues
print('Detected leagues: ')
for league in leagues.keys():
    print(league)

# user must select a league on which to operate, or create new
while True:
    input_string = input('Please select a league by name, or enter "create" to make a new one: ').strip()

    if input_string.lower() == 'create':
        league_name, league_id, expected_wins = create_league('Please enter the name for the new league: ')
        leagues[league_name] = get_league_files(league_name, league_id)
        break

    # determine which number to assign the new file
    elif leagues.get(input_string, None) is not None:

        # extract from selected league's directory
        league_name = input_string
        league_id = int(leagues[input_string][0].split('(')[-1].split(')')[0])

        print('Selected {}'.format(input_string))
        break

    else:
        print('That league could not be found.')

# use the most recent file from which to pull values
latest_rankings = leagues[league_name][0]

# no need to read from file if first run with a league (data already loaded)
if expected_wins is None:

    # read in the most recent (cumulative) expected win values
    with open(latest_rankings, 'r') as infile:
        r = csv.reader(infile)
        expected_wins = {row[0]: float(row[1]) for row in r if row}


week_num = int(input('Select a week to operate on: ').strip())

# used to pull data straight from ESPN league
league_obj = League(league_id, 2017)

sorted_scores = get_current_scores(league_obj, week_num)

# for expected wins calculation
num_teams = len(sorted_scores)

# add expected number of wins for this week to the season-long cumulative value
for idx, pair in enumerate(sorted_scores):

    # e.g., 12-team league, 2nd highest scorer would lose one matchup --> 1 - (1 * 1/11) = .909 expected wins
    ew_this_week = 1 - (idx * (1/(num_teams - 1)))

    sorted_scores[idx][1] = expected_wins[pair[0]] + ew_this_week


# display the new rankings

sorted_exp_wins = sorted(sorted_scores, key=lambda x: x[1], reverse=True)

new_wk_num = int(latest_rankings[-6:-4]) + 1

owners_wins = {team.owner: team.wins for team in league_obj.teams}

print('Power Rankings / Expected Wins: Week {}'.format(new_wk_num))
print('{0: >4} | {1: >19} | {2: >13} | {3: >11} | {4: >6}'.format('Rank', 'Owner', 'Expected Wins',
                                                                  'Actual Wins', '+/-'))

# keep tabs on (ranking, previous ew_total) to support ties in the rankings
prev_ew = (0, -1)

for idx, pair in enumerate(sorted_exp_wins):

    # edge case for ties; check that current expected wins not same (when rounded) as previous
    curr_ew = (idx + 1, pair[1])
    curr_aw = owners_wins[pair[0]]

    if round(curr_ew[1], 4) == round(prev_ew[1], 4):
        print('{0: >4} | {1: >19} | {2: >13.3f} | {3: >11} | {4: >+6.3f}'.format(prev_ew[0], pair[0], prev_ew[1], curr_aw, curr_aw - prev_ew[1]))

    else:
        print('{0: >4} | {1: >19} | {2: >13.3f} | {3: >11} | {4: >+6.3f}'.format(idx + 1, pair[0], pair[1], curr_aw, curr_aw - pair[1]))
        prev_ew = curr_ew

print('\nESPN Power Rankings:')
for row in league_obj.power_rankings(week_num):
    print('{0: >19} | {1: >5}'.format(row[1].owner, row[0]))


# update expected wins dictionary
for pair in sorted_scores:
    expected_wins[pair[0]] = '{0:.6f}'.format(pair[1])  # round to 6 decimal places

# values are now updated, need to save to a new file for this week

# determine proper filename
if new_wk_num < 10:
    new_file = latest_rankings[0:-6] + '0' + str(new_wk_num) + '.csv'
else:
    new_file = latest_rankings[0:-6] + str(new_wk_num) + '.csv'

# save weekly files to corresponding league folder
new_filepath = os.path.join(new_file)

# write owner,value to new file
with open(new_filepath, 'w') as file:
    w = csv.writer(file)
    w.writerows(expected_wins.items())

print('\n(Week saved successfully.)')
