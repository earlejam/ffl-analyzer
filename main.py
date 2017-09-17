import os
import csv


print('Welcome to the FFL Power Rankings (Expected Wins) Calculator!')

league_names = os.listdir('leagues')

# first time through the program, need a league on which to operate
if len(league_names) == 0:
    league_name = input('No previously-created leagues found. Please enter a name for a new league: ').strip()

    # create a directory to contain power rankings files for this league
    path_to_league = os.path.join('leagues', league_name)
    os.mkdir(path_to_league)

    owners_string = input('Please enter all owners (members) of this league, separated by spaces: \n').strip()

    owners = tuple(owners_string.split(' '))

    # key value pairs of an owner and his cumulative expected wins for the season; start with zero
    expected_wins = dict([(owner, 0.0) for owner in owners])

    # avoid creating file with one or more spaces, so silently replace with hyphen
    league_name = league_name.replace(' ', '-')
    rankings_filepath = os.path.join(path_to_league, '{}-00.csv'.format(league_name))

    # write owner, value to this first file
    with open(rankings_filepath, 'w') as file:
        w = csv.writer(file)
        w.writerows(expected_wins.items())

# indicates that reading from file is required later
else:
    expected_wins = None


# gather existing files for each league; a dictionary of lists, most recent file first
leagues = {}
for league_name in os.listdir('leagues'):
    league_files = os.listdir(os.path.join('leagues', league_name))  # todo error here
    league_files.sort(reverse=True)
    leagues[league_name] = league_files


# display existing leagues
print('Detected leagues: ')
for league in leagues.keys():
    print(league)


# user must select a league on which to operate
while True:
    league_name = input('Please select a league: ').strip()

    # determine which number to assign the new file
    if leagues.get(league_name, None) is not None:

        # use the most recent file from which to pull values
        latest_rankings = leagues[league_name][0]

        print('Selected {}'.format(league_name))
        break

    else:
        print('That league could not be found.')


# no need to read from file if first run through the program (data already loaded)
if expected_wins is None:

    # read in the most recent (cumulative) expected win values
    with open(latest_rankings, 'r') as infile:
        r = csv.reader(infile)
        expected_wins = {rows[0]: float(rows[1]) for rows in r}


# get each team's score for the current week
scores = []
for team in expected_wins.keys():
    team_score = float(input('{}\'s score: '.format(team)).strip())
    scores.append([team, team_score])


# arrange with highest scoring team first, lowest scoring last
sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

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

print('Power Rankings / Expected Wins: Week {}'.format(new_wk_num))
print('{0: >4} | {1: >10} | {2: >13}'.format('Rank', 'Owner', 'Expected Wins'))
for idx, pair in enumerate(sorted_exp_wins):
    print('{0: >4} | {1: >10} | {2: >13.3f}'.format(idx + 1, pair[0], pair[1]))


# update expected wins dictionary
for pair in sorted_scores:
    expected_wins[pair[0]] = '{0:.3f}'.format(pair[1])  # round to 3 decimal places

# values are now updated, need to save to a new file for this week

# determine proper filename
if new_wk_num < 10:
    new_file = latest_rankings[0:-6] + '0' + str(new_wk_num) + '.csv'
else:
    new_file = latest_rankings[0:-6] + str(new_wk_num) + '.csv'

# save weekly files to corresponding league folder
new_filepath = os.path.join('leagues', league_name, new_file)

# write owner,value to this first file
with open(new_filepath, 'w') as file:
    w = csv.writer(file)
    w.writerows(expected_wins.items())

print('\n(Week saved successfully.)')
