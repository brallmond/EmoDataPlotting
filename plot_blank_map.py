import numpy as np
import matplotlib.pyplot as plt
from main import *

if __name__ == '__main__':
  # boilerplate code you need for everything, and adjust per script
  input_csv_        = "none.csv" 
  color_bkgd_       = "white"
  color_border_     = "black"
  color_dot_        = "red"
  dot_size_         = 4
  colorscale_       = "Copper"
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

  # usually this part is "fix_places", but this is a csv, so you're adding your own data manually! 
  add_manual_places_lat_lon = {
    "LaFayette:NY" : [42.91, -76.11],
    "ahhhh:we"     : [41.91, -78.11],
    "whatever:we"  : [40.91, -80.11],
    "fake"         : [39.91, -82.11],
    "blublublub"   : [30.91, -84.11],
    "blublublub"   : [30.91, -83.11],
    "blublublub"   : [30.91, -82.11],
    "blublublub"   : [30.91, -81.11],
    "blublublub"   : [30.91, -80.11],
    "blublublub"   : [30.91, -79.11],
    "blublublub"   : [30.91, -78.11],
    "blublublub"   : [30.91, -77.11],
    "blublublub"   : [30.91, -76.11],
    "blublublub"   : [30.91, -75.11],
    "blublublub"   : [30.91, -74.11],
    "blublublub"   : [30.91, -73.11],
    "blublublub"   : [30.91, -72.11],
    "blublublub"   : [30.91, -71.11],
  }
  dataframe = add_data_manual_lat_lon(dataframe, add_manual_places_lat_lon)

  # plot the csv data on the map
  monocolor_ax = plot_locations_monocolor(dataframe, "plot title!", "noline", args)

  # try some stuff, file is intended to be an easy testing ground
  #hmmm = plot_animated_line(dataframe, args)

  plt.show()


