import numpy as np
import matplotlib.pyplot as plt
from main import *

if __name__ == '__main__':
  # boilerplate code you need for everything, and adjust per script
  input_csv_        = "ENAOData.csv" 
  color_bkgd_       = "white"
  color_border_     = "black"
  color_dot_        = "orange"
  dot_size_         = 4
  colorscale_       = "viridis"
  ull_              = True
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

  #mini_csv_output(dataframe) # read out parts of dataframe before removing anything

  dataframe, droppedBands0 = remove_Canada(dataframe)
  dataframe, droppedBands1 = drop_data_matching_condition(dataframe, "Band", "State_id", "SG") # Singapore
  dataframe, droppedBands2 = drop_data_matching_condition(dataframe, "Band", "State_id", "EG") # England
  droppedBands = helper_flatten([droppedBands0, droppedBands1, droppedBands2])

  # plot the csv data on the map
  plot_title = "Bands Included in Glenn McDonald's \"Every Noise at Once\" Emo Genre Listing"
  basemap, monocolor_ax = plot_locations_monocolor(dataframe, plot_title, "noline", args)
  #add_labels_to_plot(dataframe, "Band", "State_id")
  cityDupes = calculate_duplicates(dataframe, "City")
  add_duplicates_textbox(monocolor_ax, cityDupes, initialText="> 1 Band: ")
  add_missing_bands_textbox(monocolor_ax, droppedBands)

  # here we plot with with a color scale 
  colorscale_col = "Year formed"
  colorscale_label = "Year Band Formed"
  basemap_colorscale, colorscale_ax = plot_locations_colorscale(dataframe, plot_title, colorscale_col, colorscale_label, args)
  #add_labels_to_plot(dataframe, "Band", "State_id")
  add_duplicates_textbox(colorscale_ax, cityDupes, initialText="> 1 Band: ")
  add_missing_bands_textbox(colorscale_ax, droppedBands)

  stacked_ax = plot_stacked_timeline(dataframe, plot_title, colorscale_col, "Band")
  plt.show()


