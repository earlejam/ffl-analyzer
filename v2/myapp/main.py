from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import row
import numpy as np

x = np.array([0, 1, 2, 3, 4, 5, 6])
y = np.array([-4, 2, 0, 1, 2, 6, 4])
x1 = x - (x % 3) * .5
y1 = y + (y % 3) * .3

plot = figure(plot_height=500, plot_width=500, title='Important Data', x_range=[-1, 7], y_range=[-5, 7],
              x_axis_label='Table Size', y_axis_label='# Collisions')
plot.square(x, y, size=6, angle=0.0, fill_alpha=.7, color='red', legend='Method A')
plot.line(x1, y1, line_width=2, line_color='green', line_alpha=.5, legend='Method B')

curdoc().add_root(row(plot, width=500))
curdoc().title = 'ESPN Fantasy Football Power Rankings'
