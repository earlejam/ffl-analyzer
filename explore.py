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
import logging

# hide bokeh warnings, but show errors and above
logging.root.setLevel(logging.ERROR)


def retrieve_lg_info(league_id):
    # todo docstring

    league = League(league_id, curr_yr)

    teams = league.teams
    number_teams = league.settings.team_count

    # not available to just pull from league object
    latest_week = teams[0].wins + teams[0].losses

    # list of owner names as given by their espn accounts
    all_owners = [tm.owner for tm in teams]

    # to be used for options in dropdown menus
    owners_list_dd = [(owner, owner) for owner in all_owners]

    # espnff team objects to retrieve data
    all_team_objs = [Team(tm.owner, tm.scores) for tm in teams]

    # valid regular season weeks
    all_weeks = [i for i in range(1, latest_week + 1)]

    # given the name of an owner, returns index where it's found in the team objects list
    owner_to_idx_dict = {tm_obj.owner: index for index, tm_obj in enumerate(all_team_objs)}

    return league, number_teams, latest_week, all_owners, owners_list_dd, all_team_objs, all_weeks, owner_to_idx_dict


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


def get_line_colors(number_teams):
    # todo docstring

    colors = all_palettes['Paired'][number_teams]

    colors[0] = '#7fe8cd'

    if len(colors) >= 7:
        colors[6] = '#000000'

    if len(colors) >= 11:
        colors[10] = '#e6e600'

    return colors


def initialize_sc_figure(league, curr_week):
    # todo docstring

    sc_hover = HoverTool(tooltips=[
        ('Week', '@x'),
        ('Owner', '@owner'),
        ('Score', '@y{*00.00}'),
    ])

    # try plotting just scores first
    plot = figure(plot_height=600, plot_width=1000,
                  title='{} - {} Regular Season'.format(league.settings.name, curr_yr),
                  x_axis_label='Week',
                  y_axis_label='Scores',
                  tools=[sc_hover, ResetTool(), BoxZoomTool(), WheelZoomTool(), SaveTool(), PanTool()])

    plot.xaxis.ticker = FixedTicker(ticks=[i for i in range(1, curr_week + 1)])

    return plot


def initialize_ew_figure(league, curr_week):
    # todo docstring

    ew_hover = HoverTool(tooltips=[
        ('Week', '@x'),
        ('Owner', '@owner'),
        ('Expected Wins', '@y{*0.000}'),
    ])

    # plotting wins and expected wins in the second tab
    plot = figure(plot_height=600, plot_width=1000,
                  title='{} - {} Regular Season'.format(league.settings.name, curr_yr),
                  x_axis_label='Week',
                  y_axis_label='Expected Wins',
                  tools=[ew_hover, ResetTool(), BoxZoomTool(), WheelZoomTool(), SaveTool(), PanTool()])

    plot.xaxis.ticker = FixedTicker(ticks=[i for i in range(1, curr_week + 1)])

    return plot


def get_sc_sources(all_weeks, team_objects, all_owners, curr_week, number_teams):
    # todo docstring

    # scores
    # looks awful, but faster than using list.append() for each
    sources = [ColumnDataSource(dict(
        x=all_weeks,
        y=team_objects[i].scores[:curr_week],
        owner=[all_owners[i]] * len(all_weeks)
    )) for i in range(number_teams)]

    return sources


def get_ew_sources(all_weeks, team_objects, all_owners, curr_week, number_teams):
    # todo docstring

    # expected wins
    # looks awful, but faster than using list.append() for each
    sources = [ColumnDataSource(dict(
        x=all_weeks,
        y=team_objects[i].exp_wins[1:curr_week + 1],
        owner=[all_owners[i]] * len(all_weeks)
    )) for i in range(number_teams)]

    return sources


def plot_sc_data(team_objects, score_sources, colors):
    # todo docstring

    sc_rend_list = []
    sc_legend_items = []

    for idx, tm_obj in enumerate(team_objects):
        first_name = tm_obj.owner.split(' ')[0]

        r = plot1.rect('x', 'y', source=score_sources[idx], width=.5, height=1.2, fill_color=colors[idx], fill_alpha=0.95,
                       line_color=colors[idx], muted_color=colors[idx], muted_alpha=0.05)

        l = plot1.line('x', 'y', source=score_sources[idx], line_color=colors[idx], line_alpha=0.35, line_dash='dashed',
                       muted_color=colors[idx], muted_alpha=0.05)

        sc_rend_list.append((r, l))
        sc_legend_items.append(('{}  '.format(first_name), [r, l]))

    plot1.legend.location = 'top_center'
    plot1.legend.orientation = 'horizontal'

    sc_legend = Legend(items=sc_legend_items, location=(0, 13), orientation='horizontal')

    plot1.add_layout(sc_legend, 'above')
    plot1.legend.click_policy = 'mute'
    plot1.legend.border_line_alpha = 0

    return sc_rend_list


def plot_ew_data(team_objects, exp_wins_sources, colors):
    # todo docstring

    ew_rend_list = []
    ew_legend_items = []

    for idx, tm_obj in enumerate(team_objects):

        f_name = tm_obj.owner.split(' ')[0]

        l = plot2.line('x', 'y', source=exp_wins_sources[idx], line_color=colors[idx], line_alpha=0.95,
                       muted_color=colors[idx], muted_alpha=0.05, line_width=1.5)

        x = plot2.square('x', 'y', size=4, source=exp_wins_sources[idx], fill_color=colors[idx], line_alpha=0.95,
                         muted_color=colors[idx], muted_alpha=0.05, line_color=colors[idx], line_width=1.5)

        ew_rend_list.append((l, x))
        ew_legend_items.append(('{}  '.format(f_name), [l, x]))

    plot2.legend.location = 'top_center'
    plot2.legend.orientation = 'horizontal'

    ew_legend = Legend(items=ew_legend_items, location=(0, 13), orientation='horizontal')

    plot2.add_layout(ew_legend, 'above')
    plot2.legend.click_policy = 'mute'
    plot2.legend.border_line_alpha = 0

    return ew_rend_list


def compile_expected_wins(league, team_objects, all_weeks, ownr_to_idx, number_teams):
    # todo docstring

    # compile expected wins
    for week in all_weeks:

        all_scores = get_scores(league, week)

        for i, (owner, score) in enumerate(all_scores):

            tgt_team = team_objects[ownr_to_idx[owner]]

            # e.g., 12-team league, 2nd highest scorer would lose one matchup --> 1 - (1 * 1/11) = .909 expected wins
            ew_this_week = 1 - (i * (1/(number_teams - 1)))

            # determine new expected wins total and store
            cumul_ew = tgt_team.exp_wins[week - 1]
            new_cumul_ew = cumul_ew + ew_this_week
            tgt_team.exp_wins.append(new_cumul_ew)


def league_id_handler(attr, old, new):
    # todo docstring

    global league_obj, num_teams, week_num, owners, owners_list, team_objs, weeks, owner_to_idx
    global plot1, plot2, line_colors, backup_sc_data, backup_ew_data, legend_labels
    global sc_sources, ew_sources, sc_renderers, ew_renderers
    global layout

    league_obj, num_teams, week_num, owners, owners_list, team_objs, weeks, owner_to_idx = retrieve_lg_info(int(new))

    plot1 = initialize_sc_figure(league_obj, week_num)
    plot2 = initialize_ew_figure(league_obj, week_num)

    line_colors = get_line_colors(num_teams)

    sc_sources = get_sc_sources(weeks, team_objs, owners, week_num, num_teams)
    sc_renderers = plot_sc_data(team_objs, sc_sources, line_colors)

    compile_expected_wins(league_obj, team_objs, weeks, owner_to_idx, num_teams)

    ew_sources = get_ew_sources(weeks, team_objs, owners, week_num, num_teams)
    ew_renderers = plot_ew_data(team_objs, ew_sources, line_colors)

    # force bokeh to update figures
    plot1_wrap.children[0] = plot1
    plot2_wrap.children[0] = plot2

    # will use to avoid re-computation of data after comparisons
    backup_sc_data = [[[], []] for _ in range(num_teams)]
    backup_ew_data = [[[], []] for _ in range(num_teams)]
    legend_labels = ['' for _ in range(num_teams)]

    team1_dd.disabled = False
    team2_dd.disabled = False
    team1_dd.label = 'Team 1 - Select'
    team2_dd.label = 'Team 2 - Select'
    team1_dd.menu = owners_list
    team2_dd.menu = owners_list
    comp_button.button_type = 'danger'
    week_slider.end = week_num
    week_slider.value = (1, week_num)


def week_slider_handler(attr, old, new):
    # todo docstring

    start_wk, end_wk = week_slider.value

    # don't attempt to filter teams unless two teams are selected
    if comp_button.button_type == 'warning':
        selected_tm_idxs = [owner_to_idx[str(team1_dd.label)], owner_to_idx[str(team2_dd.label)]]
    else:
        selected_tm_idxs = [i for i in range(num_teams)]

    # values passed from widget are sometimes floats (e.g. 10.0000000002)
    start_wk = round(start_wk)
    end_wk = round(end_wk)

    for i in range(len(sc_renderers)):

        if i in selected_tm_idxs:

            selected_wks = weeks[start_wk - 1: end_wk]
            selected_scores = team_objs[i].scores[start_wk - 1:end_wk]
            selected_ew = team_objs[i].exp_wins[start_wk:end_wk + 1]
            owner = [owners[i]] * (end_wk - start_wk + 1)

            rect_r, sc_line_r = sc_renderers[i]
            ew_line_r, x_r = ew_renderers[i]

            rect_r.data_source.data = dict(x=selected_wks, y=selected_scores, owner=owner)
            sc_line_r.data_source.data = dict(x=selected_wks, y=selected_scores, owner=owner)
            ew_line_r.data_source.data = dict(x=selected_wks, y=selected_ew, owner=owner)
            x_r.data_source.data = dict(x=selected_wks, y=selected_ew, owner=owner)


def team1_select_handler(attr, old, new):
    # todo docstring

    team1_dd.label = str(team1_dd.value)

    if 'Select' not in team1_dd.label and 'Select' not in team2_dd.label and comp_button.button_type == 'danger':
        comp_button.button_type = 'success'


def team2_select_handler(attr, old, new):
    # todo docstring

    team2_dd.label = str(team2_dd.value)

    if 'Select' not in team1_dd.label and 'Select' not in team2_dd.label and comp_button.button_type == 'danger':
        comp_button.button_type = 'success'


def compare_button_handler():
    # todo docstring

    global sc_renderers
    global ew_renderers

    team1_dd.disabled = True
    team2_dd.disabled = True

    selected_tm_idxs = [owner_to_idx[str(team1_dd.label)], owner_to_idx[str(team2_dd.label)]]

    num_rend = len(sc_renderers)

    for i in range(num_rend):

        if i not in selected_tm_idxs:

            for j in range(2):

                # save data to restore when comparison done
                backup_sc_data[i][j] = sc_renderers[i][j].data_source.data
                backup_ew_data[i][j] = ew_renderers[i][j].data_source.data

                # empty data fields hide glyphs from the plot
                sc_renderers[i][j].data_source.data = dict(x=[], y=[], owner=[])
                ew_renderers[i][j].data_source.data = dict(x=[], y=[], owner=[])

            # save label for recovery after comparison
            legend_labels[i] = plot1.legend[0].items[i].label

            # empty labels for legend items hide entries
            plot1.legend[0].items[i].label = None
            plot2.legend[0].items[i].label = None

    comp_button.button_type = 'warning'
    comp_button.label = 'Clear'


def clear_button_handler():
    # todo docstring

    global sc_renderers
    global ew_renderers

    selected_tm_idxs = [owner_to_idx[str(team1_dd.label)], owner_to_idx[str(team2_dd.label)]]

    num_rend = len(sc_renderers)

    for i in range(num_rend):

        if i not in selected_tm_idxs:

            for j in range(2):

                # recover scores, expected wins data
                sc_renderers[i][j].data_source.data = backup_sc_data[i][j]
                ew_renderers[i][j].data_source.data = backup_ew_data[i][j]

            # recover label from before comparison
            plot1.legend[0].items[i].label = legend_labels[i]
            plot2.legend[0].items[i].label = legend_labels[i]

    # layout displays non-comparison state again
    team1_dd.label = 'Team 1 - Select'
    team2_dd.label = 'Team 2 - Select'
    comp_button.button_type = 'danger'
    comp_button.label = 'Compare'

    # force redraw using weeks slider
    user_selection = week_slider.value
    week_slider.value = (user_selection[0] + 1, user_selection[1])
    week_slider.value = user_selection

    team1_dd.disabled = False
    team2_dd.disabled = False


def helper_handler():
    # todo docstring

    # for dual functionality of compare / clear button
    button_to_handler = {
        'success': compare_button_handler,
        'warning': clear_button_handler
    }

    if comp_button.button_type in ['success', 'warning']:
        button_to_handler[comp_button.button_type]()


lg_id_input = TextInput(value='1667721', title='League ID (from URL):')

curr_yr = datetime.today().year

league_obj, num_teams, week_num, owners, owners_list, team_objs, weeks, owner_to_idx = retrieve_lg_info(int(lg_id_input.value))

team1_dd = Dropdown(label='Team 1 - Select', menu=owners_list)
team2_dd = Dropdown(label='Team 2 - Select', menu=owners_list)
comp_button = Button(label='Compare', button_type='danger')

week_slider = RangeSlider(title='Weeks', start=1, end=week_num, value=(1, week_num), step=1)

plot1 = initialize_sc_figure(league_obj, week_num)
plot2 = initialize_ew_figure(league_obj, week_num)

plot1_wrap = column(children=[plot1])
plot2_wrap = column(children=[plot2])

line_colors = get_line_colors(num_teams)

sc_sources = get_sc_sources(weeks, team_objs, owners, week_num, num_teams)

# will use to avoid re-computation of data after comparisons
backup_sc_data = [[[], []] for _ in range(num_teams)]
backup_ew_data = [[[], []] for _ in range(num_teams)]
legend_labels = ['' for _ in range(num_teams)]

sc_renderers = plot_sc_data(team_objs, sc_sources, line_colors)

compile_expected_wins(league_obj, team_objs, weeks, owner_to_idx, num_teams)

ew_sources = get_ew_sources(weeks, team_objs, owners, week_num, num_teams)

ew_renderers = plot_ew_data(team_objs, ew_sources, line_colors)

# register callback handlers to respond to changes in widget values
lg_id_input.on_change('value', league_id_handler)
week_slider.on_change('value', week_slider_handler)
team1_dd.on_change('value', team1_select_handler)
team2_dd.on_change('value', team2_select_handler)
comp_button.on_click(helper_handler)

# arrange layout
tab1 = Panel(child=plot1_wrap, title='Scores')
tab2 = Panel(child=plot2_wrap, title='Expected Wins')

figures = Tabs(tabs=[tab1, tab2])

compare_widgets = column(team1_dd, team2_dd, comp_button)

wid_spac1 = Spacer(height=30)
wid_spac2 = Spacer(height=30)
wid_spac3 = Spacer(height=30)

all_widgets = column(lg_id_input, wid_spac1, compare_widgets, wid_spac2, week_slider, wid_spac3)

page_title = Div(text="""<strong><h1 style="font-size: 2.5em;">ESPN Fantasy Football League Explorer</h1></strong>""",
                 width=700, height=50)

main_area = row(all_widgets, figures)

layout = column(page_title, main_area)

curdoc().add_root(layout)
curdoc().title = 'ESPN Fantasy Football League Explorer'
