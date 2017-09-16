import os
import ntpath

print('Welcome to the FFL Power Rankings (Expected Wins) Calculator!')

league_files = []
for file in os.listdir('leagues'):
    if file.endswith('.txt'):
        league_files.append(file)

if len(league_files) == 0:
    league_name = input('No previously-created leagues found. Please enter a name for a new league: ')
    league_name = league_name.replace(' ', '-')
    league_file = os.path.join('leagues', '{}.txt'.format(league_name))


else:
    print('Detected leagues: ')
    for league in league_files:
        print(ntpath.basename(league)[0:-4].replace('-', ' '))
    while True:
        league_name = input('Please select a league: ')
        for lf in league_files:
            if league_name.replace(' ', '-') in lf:
                league_file = lf
                print('Selected {}'.format(league_name))
                break
        else:
            print('That league could not be found.')

# have league filename, open/create new file ( am I going with multiple versions of file? if so, figure out how to load the most recent one