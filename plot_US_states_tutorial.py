import numpy as np
import matplotlib.pyplot as plt
from main import *

if __name__ == '__main__':
  # boilerplate code you need for everything, and adjust per script
  input_csv_        = "state_centers.csv" 
  color_bkgd_       = "white"
  color_border_     = "black"
  color_dot_        = "green"
  dot_size_         = 4
  colorscale_       = "gnuplot"
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
  # equivalent to old style of
  # python3 plot_US_states_general.py -i "state_centers.csv" -cba "black" -cbo "red" -cd "blue"

  # we fix these on the fly because the Zen of Python says
  # "Errors should never pass silently"
  # and our csv data is not wrong, but some locations are not in the uscities/locations data due to census limitations

  # define dictionary of fixes - this is file specific, and both are defined here for completeness
  # for each file, you only need to define one correction, which can be either
  # - city type, where existing city is replaced with a new one in the census data
  # - lat/lon type, where lat/lon data are manually added and used
  # these fixes are necessary when the city is too small to be in the census data, or 
  # the "City" is actually a natural geographic landmark
  fix_places_city = { 
    "Pikes Peak:CO"    : "Cascade-Chipita Park",
    "East Berlin:CT"   : "Middletown",
    "Northwest:DC"     : "Washington",
    "Wailea-Makena:HI" : "Kihei",
    "Dover-Foxcroft:ME": "Bangor", 
    "Lewiston:MT"      : "Moore", 
    "Ashland:NH"       : "Lebanon", 
    "West Warwick:RI"  : "Providence", 
    "Roxbury:VT"       : "Rutland", 
    "Buckingham:VA"    : "Farmville",
  }
  fix_places_lat_lon = {
    "Pikes Peak:CO"     : [38.9972, -105.5478],
    "East Berlin:CT"    : [41.6219, -72.7273],
    "Northwest:DC"      : [38.9101, -77.0147],
    "Wailea-Makena:HI"  : [20.2927, -156.3737],
    "Dover-Foxcroft:ME" : [45.3695, -69.2428],
    "Lewiston:MT"       : [47.0527, -109.6333],
    "Ashland:NH"        : [43.6805, -71.5811],
    "West Warwick:RI"   : [41.6762, -71.5562],
    "Roxbury:VT"        : [44.0687, -72.6658],
    "Buckingham:VA"     : [37.5215, -78.8537],
  }
  print("fixing missing city and state data")
  # now apply those fixes - use manual lat/lon style for state centers
  #dataframe = fix_data_with_new_city(dataframe, missing_places, fix_places_city)
  dataframe = fix_data_with_manual_lat_lon(dataframe, missing_places, fix_places_lat_lon)

  # now finally plot the csv data on the map
  plot_title = "State Centers (plus DC)"
  basemap_mono, monocolor_ax = plot_locations_monocolor(dataframe, plot_title, "noline", args)

  # we can also plot with multiple colors representing categories
  # (in another script this probably would be non-random info like genre tags or something)
  # create 4 categories, randomly sample them, and add them as a column to the dataframe
  category_colors = {0:'cat 1', 1:'cat 2', 2:'cat 3', 3:'cat 4'}
  rng = np.random.default_rng()
  random_ints = rng.integers(low=0, high=len(category_colors), size=dataframe.shape[0]) 
  color_list = [category_colors[int(rng_int)] for rng_int in random_ints]
  dataframe["Category"] = color_list
  basemap_categ, category_ax = plot_locations_categories(dataframe, plot_title, "Category", args)

  # here we plot with with a color scale 
  colorscale_col = "Year"
  basemap_colorscale, colorscale_ax = plot_locations_colorscale(dataframe, plot_title, colorscale_col, "Year Became State", args)

  plot_stacked_timeline(dataframe, "Year", "Year")

  plt.show()


