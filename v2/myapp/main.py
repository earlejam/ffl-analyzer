from bokeh.io import curdoc
from bokeh.plotting import figure, ColumnDataSource
from bokeh.layouts import row, column, widgetbox
from bokeh.models import HoverTool, ResetTool, SaveTool, WheelZoomTool, BoxZoomTool, PanTool, Spacer, Range1d, Legend
from bokeh.models.widgets import Dropdown, Button, RangeSlider, Div, TextInput, Panel, Tabs
from bokeh.models.tickers import FixedTicker
from bokeh.palettes import all_palettes
from espnff import League
from datetime import datetime
from structures import Team


def get_scores(lg_obj, wk_num):
    """Returns a list of each team's owner and score for the selected week
    :param lg_obj: a League(league_id, year) object for espnff
    :param wk_num: int, week of the season
    :return: a list of lists; [[owner, score], ... ] sorted highest to lowest
    """

    week_scores = {}
    for matchup in lg_obj.scoreboard(week=wk_num):
        home = [matchup.home_team, matchup.home_score]
        away = [matchup.away_team, matchup.away_score]
        week_scores[home[0].owner] = home[1]
        week_scores[away[0].owner] = away[1]

    # dict to list of lists
    scores = map(list, week_scores.items())

    # a list of lists [owner, score] for current week, highest to lowest score
    return sorted(scores, reverse=True, key=lambda x: x[1])


lg_id_input = TextInput(value="1667721", title="League ID (from URL):")

curr_yr = datetime.today().year

league_obj = League(int(lg_id_input.value), curr_yr)

teams = league_obj.teams
num_teams = league_obj.settings.team_count

# not available to just pull from league object
week_num = teams[0].wins + teams[0].losses

# list of owner names as given by their espn accounts
owners = [tm.owner for tm in teams]

owners_list = [(owner, owner) for owner in owners]

team_objs = [Team(tm.owner, tm.scores) for tm in teams]

# given the name of an owner, returns index where it's found in the team objects list
owner_to_idx = {tm_obj.owner: index for index, tm_obj in enumerate(team_objs)}

team1_dd = Dropdown(label='Team 1 - Select', menu=owners_list)
team2_dd = Dropdown(label='Team 2 - Select', menu=owners_list)
comp_button = Button(label='Compare', button_type='danger')
clear_button = Button(label='Clear', button_type='warning')

compare_widgets = column(team1_dd, team2_dd, comp_button, clear_button)

week_slider = RangeSlider(title='Weeks', start=1, end=week_num, value=(1, week_num), step=1)

wid_spac1 = Spacer(height=30)
wid_spac2 = Spacer(height=30)
wid_spac3 = Spacer(height=30)

all_widgets = column(lg_id_input, wid_spac1, compare_widgets, wid_spac2, week_slider, wid_spac3)

weeks = [i for i in range(1, week_num + 1)]

sc_hover = HoverTool(tooltips=[
    ('Week', '@x'),
    ('Owner', '@owner'),
    ('Score', '@y{*00.00}'),
])

# try plotting just scores first
plot1 = figure(plot_height=600, plot_width=1000, title='{} - {} Regular Season'.format(league_obj.settings.name, curr_yr),
               x_axis_label='Week',
               y_axis_label='Scores',
               tools=[sc_hover, ResetTool(), BoxZoomTool(), WheelZoomTool(), SaveTool(), PanTool()])

plot1.xaxis.ticker = FixedTicker(ticks=[i for i in range(1, week_num + 1)])

ew_hover = HoverTool(tooltips=[
    ('Week', '@x'),
    ('Owner', '@owner'),
    ('Expected Wins', '@y{*0.000}'),
])

# plotting wins and expected wins in the second tab
plot2 = figure(plot_height=600, plot_width=1000, title='{} - {} Regular Season'.format(league_obj.settings.name, curr_yr),
               x_axis_label='Week',
               y_axis_label='Expected Wins',
               tools=[ew_hover, ResetTool(), BoxZoomTool(), WheelZoomTool(), SaveTool(), PanTool()])

plot2.xaxis.ticker = FixedTicker(ticks=[i for i in range(1, week_num + 1)])

line_colors = all_palettes['Paired'][num_teams]

line_colors[0] = '#7fe8cd'

if len(line_colors) >= 7:
    line_colors[6] = '#000000'

if len(line_colors) >= 11:
    line_colors[10] = '#e6e600'

# scores
# looks awful, but faster than using list.append() for each
sc_sources = [ColumnDataSource(dict(
    x=weeks,
    y=team_objs[i].scores[:week_num],
    owner=[owners[i]] * len(weeks)
)) for i in range(num_teams)]

sc_rend_list = []
sc_legend_items = []

# will use to avoid re-computation of data after comparisons
backup_sc_data = [ [[], []] for i in range(num_teams) ]
backup_ew_data = [ [[], []] for i in range(num_teams) ]
legend_labels = ['' for i in range(num_teams)]

for idx, tm_obj in enumerate(team_objs):
    first_name = tm_obj.owner.split(' ')[0]

    r = plot1.rect('x', 'y', source=sc_sources[idx], width=.5, height=1.2, fill_color=line_colors[idx], fill_alpha=0.95,
                   line_color=line_colors[idx], muted_color=line_colors[idx], muted_alpha=0.05)

    l = plot1.line('x', 'y', source=sc_sources[idx], line_color=line_colors[idx], line_alpha=0.35, line_dash='dashed',
                   muted_color=line_colors[idx], muted_alpha=0.05)

    sc_rend_list.append((r, l))
    sc_legend_items.append(('{}  '.format(first_name), [r, l]))


plot1.legend.location = 'top_center'
plot1.legend.orientation = 'horizontal'

sc_legend = Legend(items=sc_legend_items, location=(0, 13), orientation='horizontal')

plot1.add_layout(sc_legend, 'above')

plot1.legend.click_policy = 'mute'

# compile expected wins

for week in weeks:

    all_scores = get_scores(league_obj, week)

    for idx, (owner, score) in enumerate(all_scores):

        tgt_team = team_objs[owner_to_idx[owner]]

        # e.g., 12-team league, 2nd highest scorer would lose one matchup --> 1 - (1 * 1/11) = .909 expected wins
        ew_this_week = 1 - (idx * (1/(num_teams - 1)))

        # determine new expected wins total and store
        cumul_ew = tgt_team.exp_wins[week - 1]
        new_cumul_ew = cumul_ew + ew_this_week
        tgt_team.exp_wins.append(new_cumul_ew)


# expected wins
# looks awful, but faster than using list.append() for each
ew_sources = [ColumnDataSource(dict(
    x=weeks,
    y=team_objs[i].exp_wins[1:week_num + 1],
    owner=[owners[i]] * len(weeks)
)) for i in range(num_teams)]


def plot_ew_data():
    # todo docstring

    ew_rend_list = []
    ew_legend_items = []

    for idx, tm_obj in enumerate(team_objs):

        f_name = tm_obj.owner.split(' ')[0]

        l = plot2.line('x', 'y', source=ew_sources[idx], line_color=line_colors[idx], line_alpha=0.95,
                       muted_color=line_colors[idx], muted_alpha=0.05, line_width=1.5)

        x = plot2.square('x', 'y', size=4, source=ew_sources[idx], fill_color=line_colors[idx], line_alpha=0.95,
                         muted_color=line_colors[idx], muted_alpha=0.05, line_color=line_colors[idx], line_width=1.5)

        ew_rend_list.append((l, x))
        ew_legend_items.append(('{}  '.format(f_name), [l, x]))

    plot2.legend.location = 'top_center'
    plot2.legend.orientation = 'horizontal'

    ew_legend = Legend(items=ew_legend_items, location=(0, 13), orientation='horizontal')

    plot2.add_layout(ew_legend, 'above')

    plot2.legend.click_policy = 'mute'

    return ew_rend_list


ew_renderers = plot_ew_data()


def week_slider_handler(attr, old, new):
    # todo docstring

    start_wk, end_wk = week_slider.value

    # don't attempt to filter teams unless two teams are selected
    if comp_button.button_type == 'success':
        selected_tm_idxs = [owner_to_idx[str(team1_dd.label)], owner_to_idx[str(team2_dd.label)]]
    else:
        selected_tm_idxs = [i for i in range(num_teams)]

    # values passed from widget are sometimes floats (e.g. 10.0000000002)
    start_wk = round(start_wk)
    end_wk = round(end_wk)

    for i in range(len(sc_rend_list)):

        if i in selected_tm_idxs:

            selected_wks = weeks[start_wk - 1: end_wk]
            selected_scores = team_objs[i].scores[start_wk - 1:end_wk]
            selected_ew = team_objs[i].exp_wins[start_wk:end_wk + 1]
            owner = [owners[i]] * (end_wk - start_wk + 1)

            rect_r, sc_line_r = sc_rend_list[i]
            ew_line_r, x_r = ew_renderers[i]

            rect_r.data_source.data = dict(x=selected_wks, y=selected_scores, owner=owner)
            sc_line_r.data_source.data = dict(x=selected_wks, y=selected_scores, owner=owner)
            ew_line_r.data_source.data = dict(x=selected_wks, y=selected_ew, owner=owner)
            x_r.data_source.data = dict(x=selected_wks, y=selected_ew, owner=owner)


def team1_select_handler(attr, old, new):
    # todo docstring

    team1_dd.label = str(team1_dd.value)

    if 'Select' not in team1_dd.label and 'Select' not in team2_dd.label:
        comp_button.button_type = 'success'


def team2_select_handler(attr, old, new):
    # todo docstring

    team2_dd.label = str(team2_dd.value)

    if 'Select' not in team1_dd.label and 'Select' not in team2_dd.label:
        comp_button.button_type = 'success'


def compare_button_handler():
    # todo docstring

    global sc_rend_list
    global ew_renderers

    # don't perform comparison unless two teams are selected
    if comp_button.button_type == 'success':

        selected_tm_idxs = [owner_to_idx[str(team1_dd.label)], owner_to_idx[str(team2_dd.label)]]

        num_rend = len(sc_rend_list)

        for i in range(num_rend):

            if i not in selected_tm_idxs:

                for j in range(2):

                    # save data to restore when comparison done
                    backup_sc_data[i][j] = sc_rend_list[i][j].data_source.data
                    backup_ew_data[i][j] = ew_renderers[i][j].data_source.data

                    # empty data fields hide glyphs from the plot
                    sc_rend_list[i][j].data_source.data = dict(x=[], y=[], owner=[])
                    ew_renderers[i][j].data_source.data = dict(x=[], y=[], owner=[])

                # save label for recovery after comparison
                legend_labels[i] = plot1.legend[0].items[i].label

                # empty labels for legend items hide entries
                plot1.legend[0].items[i].label = None
                plot2.legend[0].items[i].label = None


def clear_button_handler():
    # todo docstring

    global sc_rend_list
    global ew_renderers

    # don't perform reset unless in a comparison state
    if comp_button.button_type == 'success':

        selected_tm_idxs = [owner_to_idx[str(team1_dd.label)], owner_to_idx[str(team2_dd.label)]]

        num_rend = len(sc_rend_list)

        for i in range(num_rend):

            if i not in selected_tm_idxs:

                for j in range(2):

                    # recover scores, expected wins data
                    sc_rend_list[i][j].data_source.data = backup_sc_data[i][j]
                    ew_renderers[i][j].data_source.data = backup_ew_data[i][j]

                # recover label from before comparison
                plot1.legend[0].items[i].label = legend_labels[i]
                plot2.legend[0].items[i].label = legend_labels[i]

    # layout displays non-comparison state again
    team1_dd.label = 'Team 1 - Select'
    team2_dd.label = 'Team 2 - Select'
    comp_button.button_type = 'danger'

    # force redraw using weeks slider
    user_selection = week_slider.value
    week_slider.value = (user_selection[0] + 1, user_selection[1])
    week_slider.value = user_selection

# register callbacks to respond to changes in widget values
week_slider.on_change('value', week_slider_handler)
team1_dd.on_change('value', team1_select_handler)
team2_dd.on_change('value', team2_select_handler)
comp_button.on_click(compare_button_handler)
clear_button.on_click(clear_button_handler)

# arrange layout
tab1 = Panel(child=plot1, title='Scores')
tab2 = Panel(child=plot2, title='Expected Wins')

figures = Tabs(tabs=[tab1, tab2])

page_title = Div(text="""<strong><h1 style="font-size: 2.5em;">ESPN Fantasy Football League Explorer</h1></strong>""",
                 width=700, height=50)

main_area = row(all_widgets, figures)

layout = column(page_title, main_area)

curdoc().add_root(layout)
curdoc().title = 'ESPN Fantasy Football League Explorer'
