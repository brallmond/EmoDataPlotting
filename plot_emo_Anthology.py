import numpy as np
import matplotlib.pyplot as plt
from main import *

if __name__ == '__main__':
  # boilerplate code you need for everything, and adjust per script
  input_csv_        = "EmoAnthologyData.csv" 
  color_bkgd_       = "white" #"black"
  color_border_     = "black" #"green"
  color_dot_        = "green" #"orange"
  dot_size_         = 4
  colorscale_       = "viridis"
  ull_              = False
  DEBUG_            = False
  from argparse import Namespace
  script_args = Namespace(input_csv    = input_csv_, 
                          color_bkgd   = color_bkgd_,
                          color_border = color_border_, 
                          color_dot    = color_dot_, 
                          dot_size     = dot_size_, 
                          colorscale   = colorscale_, 
                          ull          = ull_,
                          DEBUG        = DEBUG_)
  command_line_inputs = sys.argv[1:]
  args = script_args if len(command_line_inputs) == 0 else parse_args(command_line_inputs)
  dataframe, missing_places = execute_args(args)
  # end boilerplate

  dataframe, droppedBands1 = drop_data_matching_condition(dataframe, "Band", "Band", "Alt Press")
  dataframe, droppedBands2 = drop_data_matching_condition(dataframe, "Band", "First on cover", "N")
 
  # plot the csv data on the map
  plot_title = "Bands Featured on Tom Mullen's \"Anthology of Emo\" Cover"
  monocolor_ax = plot_locations_monocolor(dataframe, plot_title, "noline", args)
  add_labels_to_plot(dataframe, "Band", "State_id")

  # here we plot with with a color scale 
  colorscale_col = "Year most pop. album"
  colorscale_label = "Year of Most Popular Work"
  basemap_colorscale, colorscale_ax = plot_locations_colorscale(dataframe, plot_title, colorscale_col, colorscale_label, args, 1990, 2005)

  stacked_ax = plot_stacked_timeline(dataframe, plot_title, colorscale_col, "Band")

  plt.show()
