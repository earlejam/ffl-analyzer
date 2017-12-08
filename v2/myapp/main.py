from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import row, column, widgetbox
from bokeh.models import HoverTool, Spacer
from bokeh.models.widgets import Dropdown, Button, RangeSlider, Div, TextInput
from bokeh.palettes import all_palettes
import numpy as np
from espnff import League
from datetime import datetime
from structures import Team

x = np.array([0, 1, 2, 3, 4, 5, 6])
y = np.array([-4, 2, 0, 1, 2, 6, 4])
x1 = x - (x % 3) * .5
y1 = y + (y % 3) * .3

lg_id_input = TextInput(value="1667721", title="League ID (from URL):")

today = datetime.today()

league_obj = League(int(lg_id_input.value), today.year)

teams = league_obj.teams

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

rundown_button = Button(label='Show Rundown')

wid_spac1 = Spacer(height=30)
wid_spac2 = Spacer(height=30)
wid_spac3 = Spacer(height=30)

all_widgets = column(lg_id_input, wid_spac1, compare_widgets, wid_spac2, week_slider, wid_spac3, rundown_button)

# try plotting just scores first

plot = figure(plot_height=600, plot_width=1000, title=str(league_obj.settings.name), x_axis_label='Week Number',
              y_axis_label='Scores')

line_colors = all_palettes['Paired'][league_obj.settings.team_count]


if len(line_colors) >=7:
    line_colors[6] = '#000000'

if len(line_colors) >= 11:
    line_colors[10] = '#e6e600'

weeks = [i for i in range(1, week_num + 1)]

for idx, tm_obj in enumerate(team_objs):
    first_name = tm_obj.owner.split(' ')[0]
    plot.rect(weeks, tm_obj.scores[:week_num + 1], width=.5, height=1.5, fill_color=line_colors[idx],
              line_color=line_colors[idx], legend='{}  '.format(first_name))
    plot.line(weeks, tm_obj.scores[:week_num + 1], line_color=line_colors[idx], line_alpha=0.35, line_dash="dashed")

plot.legend.location = 'top_center'
plot.legend.orientation = 'horizontal'

page_title = Div(text="""<strong><h1 style="font-size: 2.5em;">ESPN Fantasy Football League Explorer</h1></strong>""",
                 width=700, height=50)

main_area = row(all_widgets, plot)

layout = column(page_title, main_area)

curdoc().add_root(layout)
curdoc().title = 'ESPN Fantasy Football Power Rankings'
