from bokeh.io import curdoc
from bokeh.plotting import figure, ColumnDataSource
from bokeh.layouts import row, column, widgetbox
from bokeh.models import HoverTool, ResetTool, SaveTool, WheelZoomTool, BoxZoomTool, PanTool, Spacer, Range1d, Legend
from bokeh.models.widgets import Dropdown, Button, RangeSlider, Div, TextInput
from bokeh.models.tickers import FixedTicker
from bokeh.palettes import all_palettes
from espnff import League
from datetime import datetime
from structures import Team

lg_id_input = TextInput(value="1667721", title="League ID (from URL):")

league_obj = League(int(lg_id_input.value), datetime.today().year)

teams = league_obj.teams
num_teams = league_obj.settings.team_count

# not available to just pull from league object
week_num = teams[0].wins + teams[0].losses

# list of owner names as given by their espn accounts
owners = [tm.owner for tm in teams]

owners_list = [(owner, owner) for owner in owners]

team_objs = [Team(tm.owner, tm.scores) for tm in teams]

team1_dd = Dropdown(label='Team 1 - Select', menu=owners_list)
team2_dd = Dropdown(label='Team 2 - Select', menu=owners_list)
comp_button = Button(label='Compare', button_type='success')
reset_button = Button(label='Reset', button_type='warning')

compare_widgets = column(team1_dd, team2_dd, comp_button, reset_button)

week_slider = RangeSlider(title='Weeks', start=1, end=week_num, value=(1, week_num), step=1)

wid_spac1 = Spacer(height=30)
wid_spac2 = Spacer(height=30)
wid_spac3 = Spacer(height=30)

all_widgets = column(lg_id_input, wid_spac1, compare_widgets, wid_spac2, week_slider, wid_spac3)

weeks = [i for i in range(1, week_num + 1)]

source = ColumnDataSource(data=dict(
    owners=owners
))

hover = HoverTool(tooltips=[
    ('Week', '@x'),
    ('Owner', '@owners'),
    ('Score', '@y{*00.00}'),
])

# try plotting just scores first
plot = figure(plot_height=600, plot_width=1000, title=str(league_obj.settings.name), x_axis_label='Week',
              y_axis_label='Scores', tools=[hover, ResetTool(), BoxZoomTool(), WheelZoomTool(), SaveTool(), PanTool()])
plot.xaxis.ticker = FixedTicker(ticks=[i for i in range(1, week_num + 1)])

line_colors = all_palettes['Paired'][num_teams]

if len(line_colors) >= 7:
    line_colors[6] = '#000000'

if len(line_colors) >= 11:
    line_colors[10] = '#e6e600'

rend_list = []
legend_items = []

for idx, tm_obj in enumerate(team_objs):
    first_name = tm_obj.owner.split(' ')[0]

    r = plot.rect(weeks, tm_obj.scores[:week_num], width=.5, height=1.5, fill_color=line_colors[idx], fill_alpha=0.95,
              line_color=line_colors[idx])
    l = plot.line(weeks, tm_obj.scores[:week_num], line_color=line_colors[idx], line_alpha=0.35, line_dash='dashed')

    rend_list.append((r, l))
    legend_items.append(('{}  '.format(first_name), [r]))

plot.legend.location = 'top_center'
plot.legend.orientation = 'horizontal'

legend = Legend(items=legend_items, location=(0, 13), orientation='horizontal')

plot.add_layout(legend, 'above')


def week_slider_callback(attr, old, new):
    # todo docstring

    start_wk, end_wk = week_slider.value

    # values passed from widget are sometimes floats (e.g. 10.0000000002)
    start_wk = round(start_wk)
    end_wk = round(end_wk)

    for i, (rect_rend, line_rend) in enumerate(rend_list):

        selected_wks = weeks[start_wk - 1: end_wk]
        selected_scores = team_objs[i].scores[start_wk - 1:end_wk]

        rect_rend.data_source.data = dict(x=selected_wks, y=selected_scores)
        line_rend.data_source.data = dict(x=selected_wks, y=selected_scores)


week_slider.on_change('value', week_slider_callback)


page_title = Div(text="""<strong><h1 style="font-size: 2.5em;">ESPN Fantasy Football League Explorer</h1></strong>""",
                 width=700, height=50)

main_area = row(all_widgets, plot)

layout = column(page_title, main_area)

curdoc().add_root(layout)
curdoc().title = 'ESPN Fantasy Football League Explorer'
