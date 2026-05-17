import argparse
import pandas as pd
import numpy as np
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mpl_toolkits.basemap import Basemap
from matplotlib.animation import FuncAnimation

#########################################
# ATTRIBUTION REQUIRED!!!!###############
# https://simplemaps.com/data/us-cities #
#########################################

uscities = pd.read_csv('uscities.csv', usecols=["city", "state_id", "lat", "lng"])
locations = { f"{row[1]['city']}:{row[1]['state_id']}" : (row[1]["lat"], row[1]["lng"]) for row in uscities.iterrows()}
# locations looks like: { "Lawrence:KS" : (38.9597,-95.2642), ... }

def get_data(input_csv, DEBUG):
  # return the csv as a dataframe with 
  # - some formatting and helpful columns
  # - a list of missing cities, so they can be manually corrected by script

  # load input file, and tell user some things
  print(f"Reading in {input_csv}...")
  datacsv = pd.read_csv("data/"+input_csv,header=1) # first line should be "Data source: " so it's skipped here
  # check if City and either State or State_id is present
  present_cols = datacsv.columns.to_list()
  from state_abbrevs import us_state_to_abbrev, abbrev_to_us_state
  print("Available columns of data are: ", [col for col in present_cols])
  if ("City" in present_cols) and (("State" in present_cols) or ("State_id" in present_cols)):
    datacsv["City"] = datacsv["City"].astype('string')
    # if column not present, write it from one that is
    if ("State_id" not in present_cols): 
      datacsv["State_id"] = us_state_to_abbrev[datacsv["State"]]
    if ("State" not in present_cols):    
      datacsv["State"] = [abbrev_to_us_state[datacsv["State_id"][i]] for i in range(len(datacsv["State_id"]))]
      #datacsv["State"] = abbrev_to_us_state[datacsv["State_id"]] # dunno why this stopped working...
    datacsv["State"]    = datacsv["State"].astype('string')
    datacsv["State_id"] = datacsv["State_id"].astype('string')
    print("  Required columns present!")
  else:
    print("One or more required columns not present (or not capitalized). Exiting...")
    sys.exit() # this is an inside joke. since sys isn't imported, this will crash and exit the program
               # which is the same thing that would happen if sys were imported
               # ... one month later, no longer an inside joke because i do import sys now..
  print("The input column datatypes are: ", datacsv.dtypes)
  # provide user with additional information
  print("Your csv shape is: ", datacsv.shape)
  expected_datapoints = datacsv.shape[0] - 1
  print("Expected datapoints: ", expected_datapoints)
  if (expected_datapoints == -1):
    print("  I think this is an empty csv...")
    print("  Are you using 'plot_blank_map.py'?")
    print("  Assuming you are, and letting you continue!")
    return datacsv, [] # 2nd arg is missing_places, which is empty in this case

  # do light formatting and cleanup for the user
  # trim leading and trailing whitespace from string types
  for col_i, col_dtype in enumerate(datacsv.dtypes):
    if (col_dtype == "string"): datacsv.iloc[col_i].str.strip()

  # make column of keys for location data
  datacsv['City:State_id'] = datacsv['City'] + ':' + datacsv['State_id']

  # check for existing longitude and latitude columns
  if ("Longitude" in present_cols) or ("Latitude" in present_cols):
    print("Original latitude and longitude data copied to columns 'Source_latitude'")
    print("and 'Source_longitude'. Lats/lons from uscities.csv used instead.")
    datacsv["Latitude"]  = datacsv["Latitude"].astype(float)
    datacsv["Longitude"] = datacsv["Longitude"].astype(float)
    datacsv.rename(columns={'Latitude': 'Source_latitude', 'Longitude': 'Source_longitude'}, inplace=True)
  datacsv['Latitude']  = None
  datacsv['Longitude'] = None

  missing_places = []
  latitudes, longitudes = [], []
  if ("Source_latitude" in datacsv.columns) and ("Source_longitude" in datacsv.columns):
    latitudes  = datacsv["Source_latitude"].to_list()
    longitudes = datacsv["Source_longitude"].to_list()
  else:
    # if user lat/lons not present, get longitude and latiude data for city and states 
    # and make a list of cities whose data is not found in uscities.csv
    from missing_locations import missing
    for place in datacsv['City:State_id']:
      if DEBUG: print(place)
      try:
        # access and save location data
        if DEBUG: print(place, locations[place])
        lat_, lon_ = locations[place]
        latitudes.append(lat_)
        longitudes.append(lon_)
      
      except KeyError: # missing!
        try:
          if DEBUG: print(place, locations[place])
          lat_, lon_ = missing[place]
          latitudes.append(lat_) 
          longitudes.append(lon_) 
        except KeyError: # missing and not in list of commonly missing places!
          if DEBUG: print("missing!")
          missing_places.append(place)
          latitudes.append(-999)
          longitudes.append(-999)
 
  print("cities not found:")
  print(missing_places)
  print()

  datacsv["Latitude"]  = latitudes
  datacsv["Longitude"] = longitudes

  return datacsv, missing_places


def drop_data_matching_condition(dataframe, label, column_name, remove_if_equals):
#def drop_data_matching_condition(dataframe, column_name, remove_if_equals):
  original_size = dataframe.shape[0]-1
  drop_rows = []
  bands_dropped = []
  for i, row in dataframe.iterrows():
    if (row[column_name] == remove_if_equals): 
      bands_dropped.append(row[label])
      #bands_dropped.append(row[column_name])
      drop_rows.append(i)
  dataframe = dataframe.drop(drop_rows)
  final_size = dataframe.shape[0]-1
  print("Dataframe updated!")
  nFound = original_size - final_size
  print(f"  {nFound} entries found in column '{column_name}' with '{remove_if_equals}' criteria, and removed")
  return dataframe, bands_dropped


def calculate_duplicates(dataframe, columnName):
  # this is O(n^2), so if things get really slow later this could be why...
  uniqVals = set(dataframe[columnName].to_list())
  uniqValCounts = {key: 0 for key in uniqVals}
  for val in uniqVals:
    for i, row in dataframe.iterrows():
      compareVal = row[columnName]
      if (val == compareVal):
        uniqValCounts[val] += 1
  keepUniqValCounts = {}
  for key, value in uniqValCounts.items():
    if (value > 1):
      keepUniqValCounts[key] = value
  duplicates = keepUniqValCounts
  if (columnName == "City"):
    if ("Washington" in duplicates.keys()):
      duplicates["Washington D.C."] = duplicates.pop("Washington")
  return duplicates
 

def configure_plot(color_bkgd, color_border, color_dot, DEBUG, animated=False):
  # make basic map with given color settings
  if DEBUG:
    print(f"Map background:   {color_bkgd}")
    print(f"State border:     {color_border}")
    print(f"Data point color: {color_dot}")
  fig, map_ax = plt.subplots(figsize=(10,8))
  add_Canada_and_Mexico = False # normally False, manually set here as an "expert" setting..
  initial_map = Basemap(llcrnrlon=-122, llcrnrlat=20, urcrnrlon=-60, urcrnrlat=50, # default, main 48 only
                        projection='lcc', lat_1=32, lat_2=45, lon_0=-95)
  #initial_map = Basemap(width=12000000,height=9000000,projection='lcc',         # wider view, including Canada and AL
  #                      resolution='c',lat_1=45.,lat_2=55,lat_0=50,lon_0=-107.)
  
  # if plot_inset # still testing...
  #initial_map = Basemap(projection='lcc',width=6000.e3,height=4000.e3,lon_0=-90,lat_0=40,resolution='l', ax=map_ax)

  initial_map.drawmapboundary(fill_color=color_bkgd) # sets background color
  if (add_Canada_and_Mexico == False):
    _, _, _, _, matplot_lines = initial_map.readshapefile('shapefiles/cb_2024_us_state_20m', name='states', drawbounds=True)
    # CA shape files have encoding error that i can't figure out currently
    #_, _, _, _, matplot_lines = initial_map.readshapefile('CA_shapefiles/lpr_000a21a_e', name='Province', drawbounds=True)
    matplot_lines.set_color(color_border) # sets state border color
  else: # add Canada and Mexico
    initial_map.drawcountries(linewidth=1)
    initial_map.drawcoastlines(linewidth=1)
    initial_map.drawstates(linewidth=0.5)

  # see plot-precip example for more inspo
  # https://matplotlib.org/basemap/stable/users/examples.html

  if DEBUG:
    plt.title("map plot before data!")

  if (animated == True):
    return initial_map, map_ax, fig
  # if plot_inset
  #from mpl_toolkits.axes_grid1.inset_locator import inset_axes
  #from matplotlib.patches import Polygon
  ## axes for inset map.
  #axin = inset_axes(initial_map.ax,width="30%",height="30%",loc=4)
  ## inset map is global, with primary map projection region drawn on it.
  #omap = Basemap(projection='ortho',lon_0=-105,lat_0=40,ax=axin,anchor='NE')
  #omap.drawcountries(color='white')
  #omap.fillcontinents(color='gray') #color = 'coral'               
  #bx, by = omap(initial_map.boundarylons, initial_map.boundarylats)
  #xy = list(zip(bx,by))
  #mapboundary = Polygon(xy,edgecolor='red',linewidth=2,fill=False)
  #omap.ax.add_patch(mapboundary)

  return initial_map, map_ax


def parse_dataframe_lat_lon_to_map(dataframe, basemap, ull_source=False):
  all_lats, all_lons = [], []
  latName = "Source_latitude" if ull_source == True else "Latitude"
  lonName = "Source_longitude" if ull_source == True else "Longitude"
  for i, row in dataframe.iterrows():
    lat_, lon_ = row[latName], row[lonName]
    x, y = basemap(lon_, lat_)
    all_lats.append(x)
    all_lons.append(y)
  return all_lats, all_lons


def plot_locations_monocolor(dataframe, title, line_on, args):
  basemap, map_ax = configure_plot(args.color_bkgd, args.color_border, args.color_dot, args.DEBUG)
  plt.title(title)
  lats, lons = parse_dataframe_lat_lon_to_map(dataframe, basemap, args.ull)
  plot_connections = False
  if plot_connections: add_lines(map_ax, lons, lats)
  line_on = False if line_on == "noline" else True
  if (line_on == True):
    basemap.plot(lats, lons, '-o', color=args.color_dot, markersize=args.dot_size, linewidth=1)
    basemap.plot(lats[0], lons[0], '*', color=args.color_dot, markersize=12)  # start
    basemap.plot(lats[-1], lons[-1], 's', color=args.color_dot, markersize=7) # end
    # can't remember why but i was doing this before...
    #basemap.plot(lats, lons, '-o', color=args.color_dot, markersize=args.dot_size, alpha=0.5, linewidth=1)
    #basemap.scatter(lats, lons, c=[i for i in range(len(lats))], cmap="coolwarm")
  else:
    basemap.plot(lats, lons, 'o', color=args.color_dot, markersize=args.dot_size)
  return basemap, map_ax


# i sorta can't believe this works, but it does!
# followed steps here: https://matplotlib.org/stable/api/animation_api.html#funcanimation
def plot_animated_line(dataframe, title, label_col1, label_col2, args):
  basemap, map_ax, fig = configure_plot(args.color_bkgd, args.color_border, args.color_dot, args.DEBUG, animated=True)
  dates  = dataframe[label_col1].to_list()
  cities = dataframe[label_col2].to_list()
  lats, lons = parse_dataframe_lat_lon_to_map(dataframe, basemap)

  lat_update, lon_update = [], []
  ln,_ = map_ax.plot([], [], '-o', args.color_dot, linewidth=1)

  scat = map_ax.scatter(lats[0], lons[0], marker="*", color=args.color_dot, s=100)

  # Unfortunately, these are somewhat magic numbers because
  # Basemap isn't in lon/lat, it's in 'map coordinates' which are translated internally from lon/lat...
  text    = map_ax.text(55000, 3250000, "", fontsize=12, color='black')
  loctext = map_ax.text(0, 0, "", fontsize=12, color='black', # initial position not important for city text
                        bbox=dict(boxstyle='round', facecolor='wheat', edgecolor="none", pad=0.05))
  plt.title(title)
  def update(frame):
    loctext.set_position((lats[frame]+55000, lons[frame]+55000))
    loctext.set_text(cities[frame])
    loctext.set_zorder(10) 
    text.set_text(dates[frame])
    text.set_zorder(10)

    lat_update.append(lats[frame]) 
    lon_update.append(lons[frame]) 
    scat.set_offsets((lats[frame], lons[frame]))
    ln.set_zorder(1)
    scat.set_zorder(3)

    if (frame == (len(lats) - 1)):
      start = map_ax.scatter(lats[0], lons[0], marker="v", color="green", s=120)
      end   = map_ax.scatter(lats[-1], lons[-1], marker="s", color="green", s=120)
      start.set_zorder(2)
      end.set_zorder(2)
    if (len(lat_update) <= (len(lats)+1)): 
      ln.set_data(lat_update, lon_update) # stop updating line after the last frame!
    return ln, scat

  anim = FuncAnimation(fig, update, frames=[*range(len(lats))], interval=500)
  plt.show()
  return basemap, map_ax, anim
# one could imagine rewriting this function as a class that generates an animator on a plot
# that way you can plot multiple tours at once 


def plot_locations_categories(dataframe, title, category_col, args, category_order=[], user_color_list=[], user_marker_list=[]):
  basemap, map_ax = configure_plot(args.color_bkgd, args.color_border, args.color_dot, args.DEBUG)
  plt.title(title)
  lats, lons = parse_dataframe_lat_lon_to_map(dataframe, basemap)
  # if custom lists given, use those
  default_color_list  = ["red", "green", "blue", "orange", "pink", "purple"]
  default_marker_list = ["o", "s", "v", "d", "P", "*"] # circle, square, triangle, thin diamond, thick plus, star
  color_list  = default_color_list if user_color_list == [] else user_color_list
  marker_list = default_marker_list if user_marker_list == [] else user_marker_list
  # find number of categories in given column, and make list of categories instead of using dataframe
  categories = set(dataframe[category_col].values) if category_order == [] else category_order
  if (type(list(categories)[0]) == np.int64): categories = [str(val) for val in categories]
  if (len(categories) > 6): print("  More than 6 categories, please specify colors and markers in function call")
  category_list = [str(val) for val in dataframe[category_col].values]
  # create dictionaries for color and markers
  color_dict  = {category : color  for category, color  in zip(categories, color_list)}
  marker_dict = {category : marker for category, marker in zip(categories, marker_list)}
  # counting category info
  category_counts = {category: np.sum(np.array(category_list) == category) for category in categories}
  total = np.sum([category_counts[category] for category in category_counts])
  legend_elements = [plt.Line2D([0], [0], marker=marker_dict[category], linestyle="None",
                           color=color_dict[category], label=f'{category} [{category_counts[category]}]')
                           for category in categories]
  # skip totaling or not
  #legend_elements.append(plt.Line2D([0], [0], marker='None', linestyle="None",
  #                         color="black", label=f'Total [{total}]'))
  #
  map_ax.legend(handles=legend_elements, loc="upper center", ncols=len(category_list), fontsize=9)
  # plot each point with its own color and marker (couldn't pass as list...)
  for lat_, lon_, entry_ in zip(lats, lons, category_list):
    basemap.plot(lat_, lon_, marker=marker_dict[entry_], color=color_dict[entry_], markersize=args.dot_size)
 
  return basemap, map_ax


def plot_locations_colorscale(dataframe, title, colorscale_col, colorscale_label, args, user_vmin=None, user_vmax=None):
  basemap, map_ax = configure_plot(args.color_bkgd, args.color_border, args.color_dot, args.DEBUG)
  plt.title(title)
  lats, lons = parse_dataframe_lat_lon_to_map(dataframe, basemap)
  scale_data = [int(val) for val in dataframe[colorscale_col].values]
  vmin = min(scale_data) if user_vmin == None else user_vmin
  vmax = max(scale_data) if user_vmax == None else user_vmax
  sc = basemap.scatter(lats, lons, c=scale_data, vmin=vmin, vmax=vmax, cmap=args.colorscale, zorder=10) # zorder puts it on top
  cbar = basemap.colorbar(sc, shrink=0.9, aspect=18, pad=0.05, location="bottom")
  #cbar = plt.colorbar(shrink=0.9, aspect=18, orientation='horizontal', pad=0.01)
  cbar.set_label(colorscale_label)
  # TODO
  #cbar.set_xticks
  #cbar.set_xticklabels
  return basemap, map_ax


def add_labels_to_plot(dataframe, label_p1, label_p2, label_p3=None):
  legend_elements = []
  for i, row in dataframe.iterrows():
    label = str(row[label_p1]) + " - " + str(row[label_p2])
    if (label_p3 != None): label += " - " + str(row[label_p3])
    legend_elements.append(plt.Line2D([0], [0], marker='o', linestyle="None", color="None", label=label))
  plt.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(1.05, 0.5))
  plt.tight_layout()


def add_misc_textbox(ax, initialText, items, textColor="black", faceColor="none", edgeColor="none"):
  # box in bottom left of map
  itemsText = ""
  for item in items:
    itemsText += f"  {item}\n"
  itemsText = itemsText[:-1] # removes final \n (extra whitespace)
  text    = ax.text(0.02, 0.04, f"{initialText}\n{itemsText}", fontsize=10, color=textColor, #fontname=fontname,
                        bbox=dict(boxstyle='round', facecolor=faceColor, edgecolor=edgeColor, pad=0.4),
                        transform=ax.transAxes)


def add_attribution(ax):
  # box in bottom right of map
  text    = ax.text(0.80, 0.02, f"Plot by Braden Allmond", fontsize=7, color="black",
                        bbox=dict(boxstyle='round', facecolor="none", edgecolor="none", pad=0.1),
                        transform=ax.transAxes)


def add_duplicates_textbox(ax, duplicates, initialText="", bump=False):
  # line at top of map, in small text
  dupeText = f"{initialText} "
  counter, counterBump = 0, False
  for dupeName, dupeVal in duplicates.items():
    dupeText += f"{dupeName}:{dupeVal}, "
    counter += 1
    if (counter % 9 == 0): 
      dupeText += '\n' # doesn't quite work, pushes yaxis start up...
      counterBump = True
  ystart = 0.97
  if bump: ystart -= 0.03
  if (counterBump): ystart -= 0.06
  text    = ax.text(0.01, ystart, f"{dupeText}", fontsize=7, color='black',
                        transform=ax.transAxes)


def add_missing_bands_textbox(ax, droppedBands, textColor="black", faceColor="none", edgeColor="none"):
  # column in bottom left of map
  droppedBandsText = ""
  if (len(droppedBands) == 0): 
    print("No bands dropped, no textbox added")
    return
  for band in droppedBands:
    droppedBandsText += f"  {band}\n"
  droppedBandsText = droppedBandsText[:-1]
  text    = ax.text(0.02, 0.04, f"Non-US Bands in Dataset\n{droppedBandsText}", fontsize=10, color=textColor,
                        bbox=dict(boxstyle='round', facecolor=faceColor, edgecolor=edgeColor, pad=0.4),
                        transform=ax.transAxes)


def mini_csv_output(inputDF, columns=[]):
  # default behavior reads out band name, latitude, longitude
  # alternatively, pass in column names to print
  if (columns == []):
    bands = inputDF["Band"].to_list()
    lats = inputDF["Latitude"].to_list()
    lons = inputDF["Longitude"].to_list()
    print("Band, Latitude, Longitude")
    for b, v1, v2 in zip(bands, lats, lons):
      print(",".join([b, str(v1), str(v2)]))
  else:
    for column in columns:
      print()
      print(f"Added info for {len(inputDF)} bands, copy columns below")
      print(column)
      colVals = inputDF[column].to_list()
      for val in colVals:
        if (column == "Notes") and (type(val) != str): print() # keeps nans from being printed in Notes section
        else: print(val)
      input("Press any key to get the next column") 


def fix_data_with_new_city(dataframe, missing_places, fix_places_city):
  for i, row in dataframe.iterrows(): # iterating over the whole thing is lazy, but we never have > 100 entries..
    original_place = row["City:State_id"]
    if (original_place in missing_places):
      new_city = fix_places_city[original_place]
      dataframe.loc[i, "City"] = new_city
      new_place = new_city + ":" + row["State_id"]
      dataframe.loc[i, "City:State_id"] = new_place
      lat_, lon_ = locations[new_place]
      dataframe.loc[i, "Latitude"] = lat_
      dataframe.loc[i, "Longitude"] = lon_
      print(f"  changed {original_place} to {new_place}!")
  return dataframe


def fix_data_with_manual_lat_lon(dataframe, missing_places, fix_places_lat_lon):
  for i, row in dataframe.iterrows(): # iterating over the whole thing is lazy, but we never have > 100 entries..
    original_place = row["City:State_id"]
    if (original_place in missing_places):
      lat_, lon_ = fix_places_lat_lon[original_place]
      dataframe.loc[i, "Latitude"] = lat_
      dataframe.loc[i, "Longitude"] = lon_
      print(f"  updated {original_place} lat/lon data!")
  return dataframe


def add_data_manual_lat_lon(dataframe, add_manual_places_lat_lon):
  for name, lat_lon in add_manual_places_lat_lon.items():
    # these row names are specific to "none.csv"
    new_row_df = pd.DataFrame([{"Place": name, "Latitude": lat_lon[0], "Longitude": lat_lon[1]}])
    dataframe = pd.concat([dataframe, new_row_df], ignore_index=True)
  return dataframe


def helper_flatten(list_of_lists):
  flattened_list = []
  for list_ in list_of_lists:
    if (list_ != []):
      for entry in list_:
        flattened_list.append(entry) 
  return flattened_list

def remove_Canada(dataframe, label="Band"):
  dataframe, bON = drop_data_matching_condition(dataframe, label, "State_id", "ON")
  dataframe, bAB = drop_data_matching_condition(dataframe, label, "State_id", "AB")
  dataframe, bBC = drop_data_matching_condition(dataframe, label, "State_id", "BC")
  dataframe, bQC = drop_data_matching_condition(dataframe, label, "State_id", "QC")
  dataframe, bMB = drop_data_matching_condition(dataframe, label, "State_id", "MB")
  bands_dropped = helper_flatten([bON, bAB, bBC, bQC, bMB])
  print("removed Canada")
  return dataframe, bands_dropped


def set_state_color(basemap, user_state, color):
  # https://stackoverflow.com/questions/7586384/color-states-with-pythons-matplotlib-basemap
  # collect the state names from the shapefile attributes so we can
  # look up the shape obect for a state by it's name
  state_names = []
  for shape_dict in basemap.states_info:
      state_names.append(shape_dict['NAME'])
  ax = plt.gca() # get current axes instance
  color_state_names = [user_state] if user_state != "all" else state_names # this doesn't quite work
  for state in color_state_names:
    seg = basemap.states[state_names.index(state)]
    poly = Polygon(seg, facecolor=color, edgecolor=color)
    ax.add_patch(poly)


def calculate_distance(loc1, loc2):
  lat1, lon1 = loc1
  lat2, lon2 = loc2
  earthRad = 6371000 # meters
  PI = 3.14159265359
  phi1 = lat1 * PI/180.0 # latitude in radians
  phi2 = lat2 * PI/180.0 # latitude in radians
  dphi = phi2 - phi1
  dlambda = (lon2 - lon1) * PI / 180 # longitude difference in radians
  radicand = np.sin(dphi/2) * np.sin(dphi/2) + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2) * np.sin(dlambda/2)
  intermed = 2 * np.arctan2(np.sqrt(radicand), np.sqrt(1-radicand))
  distance = earthRad * intermed # in units of meters, transfer to miles before output
  return distance * 0.621371 / 1000.0 # km * miles / km = miles


def add_lines(ax, lons_to_use, lats_to_use):
  count = 0
  for i, lat1, lon1 in zip(range(len(lons_to_use)), lons_to_use, lats_to_use):
    for j, lat2, lon2 in zip(range(len(lons_to_use)), lons_to_use, lats_to_use):
      if (j == i): continue
      ax.plot((lon1, lon2), (lat1, lat2),  marker='None', linestyle='--', color='grey', linewidth=0.5, alpha=0.2)
      count += 1
  print(f"{count} lines")
  print(f"{len(lons_to_use)} bands")


def gaussian(x, mu, sig):
    # TODO check normalization...
    return ( 1.0 / (np.sqrt(2.0 * np.pi) * sig) * np.exp(-np.power((x - mu) / sig, 2.0) / 2) )


def plot_stacked_timeline(dataframe, title, plot_column, label_column=None, useGauss=False):
  fig, axc = plt.subplots()
  axc.set_title(title)
  year_info = [int(year) for year in dataframe[plot_column].to_list()]
  min_bound, max_bound = min(year_info)-2, max(year_info)-2
  nYears = max_bound - min_bound + 1
  year_range = np.linspace(min_bound, max_bound, nYears)
  year_info = [[year] for year in year_info] # this turns list of [1, 2, 3] into [[1], [2], [3]] for proper labeling
  label_info = dataframe[label_column].to_list() if label_column != None else label_column
  color = ["blue"]*len(year_info)
  edgecolor = ["black"]*len(year_info)
  if (useGauss == True):
    sigma = 1
    year_range = np.linspace(min_bound, max_bound, nYears*3)
    gauss = [gaussian(year_range, year, sigma) for year in year_info]
    if (label_info == None):
      axc.stackplot(year_range, gauss, alpha=0.8, color=color) 
    else:
      axc.stackplot(year_range, gauss, labels=label_info, alpha=0.8, color=color) 
  else:
    if (label_info == None):
      n, bins, _ = axc.hist(year_info, bins=year_range, stacked="True", color=color, edgecolor=edgecolor)
    else:
      n, bins, _ = axc.hist(year_info, bins=year_range, stacked="True", label=label_info, color=color, edgecolor=edgecolor)
  axc.set_xlim(min(year_range), max(year_range))
  axc.set_ylabel("Number of Entries")
  axc.set_xlabel(plot_column)
  axc.legend()
  #print(n, bins) # DEBUG
  legend_elements = [plt.Line2D([0], [0], marker='s', linestyle="None",
                           color="blue", label=f'Band [Total={len(year_info)}]')]
  axc.legend(handles=legend_elements)

  xticks_locations = axc.get_xticks()
  xticks_labels = axc.get_xticklabels()
  minx, maxx = int(xticks_locations[0]), int(xticks_locations[-1])+1
  step_size = 2
  xticks_locations = [i for i in range(minx, maxx, step_size)]
  xticks_labels = [plt.Text(i, 0, str(i)) for i in range(minx, maxx, step_size)]
  axc.set_xticks(xticks_locations)
  axc.set_xticklabels(xticks_labels, rotation=35, fontsize=10) 
  #if (label_info != None): axc.legend()
  #axc.legend() # no legend by default


def plot_1d_hist(valArray, title, xLabel, legendOn=True, nBins=0, binEdges=[]):
  # auto count nbins to be integer of range of column_name
  if (nBins != 0) and (binEdges != []): print("Set one or the other, crashing.")
  fig, ax1d = plt.subplots()
  nBins = int(max(valArray) - min(valArray)) + 1 if nBins == 0 else nBins + 1
  if (binEdges == []):
    counts, bins, _ = ax1d.hist(valArray, bins=nBins)
  else:
    counts, bins, _ = ax1d.hist(valArray, bins=binEdges)
  ax1d.set_title(title)
  ax1d.set_ylabel("Number of Bands")
  ax1d.set_xlabel(xLabel)
  # add statistical info to textbox in upper right, using legend for easier placement
  if (legendOn):
    mean, median = np.mean(valArray), np.median(valArray)
    total, stddev = len(valArray), np.sqrt(np.var(valArray))
    empty_handle = plt.Line2D([], [], color='none', label='An Empty Entry')
    handles = [empty_handle, empty_handle, empty_handle, empty_handle]
    labels = [f"Entries : {total:.0f}", f"Mean: {mean:.1f}", f"Median: {median:.1f}", f"Std. Dev.: {stddev:.1f}"]
    ax1d.legend(handles, labels, loc="upper right")
  return ax1d, counts, bins


def source_stats(dataframe, doPrint=True):
  earliest = min(dataframe['Year formed'].to_list())
  latest   = max(dataframe['Year formed'].to_list())
  if (doPrint):
    print(f"nEntries = {len(dataframe)}")
    print(f"Earliest Formation Year = {earliest}")
    print(f"Latest   Formation Year = {latest}")
  return earliest, latest


# source published
pubYears     = {"Anthology" : 2020, "Vulture" : 2020, "ENAO" : 2023, "RStone" : 2019, "AltPress" : 2017}
def add_source_windows(ax, includeSources=["Anthology", "Vulture", "ENAO", "RStone", "AltPress"]):
  # add vertical lines indicating information window for each source
  # hardcoding because these don't change, this function just picks which are included
  
  # earliest band formed in source
  earliestBandYears = {"Anthology" : 1989, "Vulture" : 1983, "ENAO" : 1983, "RStone" : 1983, "AltPress" : 1983}
  # latest band formed in source
  latestBandYears   = {"Anthology" : 2011, "Vulture" : 2016, "ENAO" : 2015, "RStone" : 2007, "AltPress" : 2016}

  ymax = ax.get_ylim()[-1]
  labelHeights = [ymax*.70, ymax*.12, ymax*0.25, ymax*0.40, ymax*.35]
  
  pubYearsInc          = [pubYears[source]          for source in includeSources]
  earliestBandYearsInc = [earliestBandYears[source] for source in includeSources]
  latestBandYearsInc   = [latestBandYears[source]   for source in includeSources]
  for i in range(len(pubYearsInc)):
    ax.axvline(pubYearsInc[i], color="grey", linestyle="dotted")
    #ax.axvline(earliestBandYearsInc[i], color="red", linestyle="dotted")
    #ax.axvline(latestBandYearsInc[i], color="grey", linestyle="dashed")
    #ax.text(pubYearsInc[i], i*10, f'{includeSources[i]} Published', fontsize=12,
    ax.text(pubYearsInc[i], labelHeights[i], f'{includeSources[i]}', fontsize=10,
            rotation=90, rotation_mode='anchor',
            transform_rotates_text=True)


def plot_activity_periods(dataframe, label_column, year_start_column, year_end_column):
  fig, axb = plt.subplots()
  labels = dataframe[label_column].to_list()
  nEntries = len(labels)
  y_pos = np.arange(nEntries)
  colors = ["royalblue", "green", "red", "orange", "pink", "purple", "cyan", "gold"]*(round(nEntries/7))
  starts = dataframe[year_start_column].to_list()
  ends   = dataframe[year_end_column].to_list()
  durations = [ends[i] - starts[i] for i in range(len(starts))]
  durations = [dur if dur !=0 else 0.5 for dur in durations]
  for i in range(len(starts)):
    # x input is (start, length)
    axb.broken_barh([(starts[i], durations[i])], (y_pos[i], 0.5), color=colors[i])
  axb.set_yticks(y_pos, labels=labels)
  axb.tick_params(axis='y', which='major', labelsize=8)
  return axb


#                                                            loosely ["1st Wave", "Midwest Emo", "Mallcore", "Revival"]
def assign_generation(year, cutoffs=[1994, 2001, 2012], categoryName=["1985-1994", "1995-2001", "2002-2012", "After 2012"]):
  # assign category to an entry
  # based on the year and cut off points
  assert len(categoryName) == len(cutoffs) + 1, "Category assignment incorrect size"
  saveIdx = ""
  if   (year <= cutoffs[0]): saveIdx = 0
  elif (year > cutoffs[-1]): saveIdx = -1
  else: 
    checkVal = [(cutoffs[i-1] < year <= cutoffs[i]) for i in range(1, len(cutoffs)+1)]
    saveIdx = checkVal.index(True) + 1
  assert type(saveIdx) == int, "Failed to assign category"
  return categoryName[saveIdx]


def plot_active_bands_per_year(dataframe):
  # calculate number of bands active per year
  earliestYear = min(dataframe["Year formed"].to_list())
  latestYear   = 2026 # current year
  years = [year for year in range(earliestYear, latestYear+1)]
  yearSums = []
  for year in years:
    bandFormed    = dataframe["Year formed"] <= year
    stillTogether = dataframe["Year disbanded"] >= year
    activeInYear  = (bandFormed) & (stillTogether)
    yearSums.append(int(np.sum(activeInYear)))
  years.append(latestYear+1)
  fig, ax = plt.subplots()
  ax.stairs(yearSums, years)
  ax.set_title("Number of Bands Active in Each Year")
  ax.set_ylabel("Number of Bands")
  ax.set_xlabel("Year")
  # combine bins by 2
  yearSumsHalfBins = [yearSums[i] + yearSums[i-1] for i in range(1, len(yearSums), 2)]
  yearsHalf = [year for year in range(earliestYear, latestYear+1, 2)].append(latestYear+1)
  fig, axh = plt.subplots()
  axh.stairs(yearSumsHalfBins, yearsHalf)
  axh.set_title("Number of Bands Active in Each Year (Combined Across two Years)")
  axh.set_ylabel("Number of Bands")
  axh.set_xlabel("Year")
  return ax, years, yearSums


def plot_vital_statistics(dataframe):
  # "vital" in the sense of band formation (birth) and disbandment (death)
  # this is a tounge-in-cheek joke about open data, as many states publish
  # birth and death rates annually as "vital statistics"
  #axfo_ = dataframe["Year formed"].to_list()
  #axfo_ = [int(year) for year in axfo_]
  axfo = plot_1d_hist(dataframe["Year formed"].astype(int).to_list(), "Amount of Bands formed by Year", "Year Formed")
  #axfo = plot_1d_hist(axfo_, "Amount of Bands formed by Year", "Year Formed")
  #axdi_ = dataframe["Year disbanded"].to_list()
  #dataframe["Year disbanded"] = [int(year) for year in axdi_]
  yearDisbandedDropPresent = dataframe[dataframe["Year disbanded"].astype(int) != 2026].copy()["Year disbanded"].to_list()
  #axdi = plot_1d_hist(yearDisbandedDropPresent, "Amount of Bands disbanded by Year", "Year Disbanded")
  #yearDisbandedDropPresent = dataframe[axdi_ != 2026].copy()["Year disbanded"].to_list()
  axdi = plot_1d_hist(yearDisbandedDropPresent, "Amount of Bands disbanded by Year", "Year Disbanded")
  dataframe["Duration"] = dataframe["Year disbanded"].astype(int) - dataframe["Year formed"].astype(int)
  #dataframe["Duration"] = axdi_ - axfo_
  axdu = plot_1d_hist(dataframe["Duration"].to_list(), "Length of Bands' Initial Run", "Year Disbanded - Year Formed [Years]")
  return axfo, axdi, axdu


def combine_two_dataframes(df1, df2, printInfo=True, printIndivs=False):
  # calculate and return union and intersection of two dataframes
  # also give ratio, and additional size information
  df1Size = len(df1)
  df2Size = len(df2)
  dfComb   = pd.concat([df1, df2])
  dfCombSize = len(dfComb)
  dfUniqComb  = dfComb.drop_duplicates(subset=["Band"])
  dfUniqCombSize = len(dfUniqComb)
  dfInt   = pd.merge(df1, df2, on="Band")
  dfIntSize = len(dfInt)

  df1EarliestYear, df1LatestYear = source_stats(df1, doPrint=False)
  df2EarliestYear, df2LatestYear = source_stats(df2, doPrint=False)
  #print(df1["Name"].to_list()[0], df2["Name"].to_list()[0])
  print("Earliest year band formed in each df: ", df1EarliestYear, df2EarliestYear)
  print("Latest year band formed in each df: ", df1LatestYear, df2LatestYear)

  if printInfo:
    print(f"df1, df2, Naive sum, dfComb, dfInt")
    print(f"{df1Size}, {df2Size}, {df1Size+df2Size}, {dfUniqCombSize}, {dfIntSize}")
    IoU = dfIntSize / dfCombSize
    normIoU = IoU / (min([df1Size,df2Size]) / dfCombSize)
    print(f"IoU = {IoU:.3f}")
    print(f"normIoU = {normIoU:.3f}")
    print(f"df1 Uniq = {df1Size - dfIntSize}")
    print(f"df2 Uniq = {df2Size - dfIntSize}")
    print(f"Checksum, df1 Uniq + df2 Uniq + dfInt = dfUniqComb, {df1Size + df2Size -dfIntSize} = {dfUniqCombSize}")

  if printIndivs:
    df1Bands = df1["Band"].to_list()
    dfIntBands = dfInt["Band"].to_list()
    uniqBands = [band for band in df1Bands if band not in dfIntBands]
    uniqBands.sort()
    print(f"Bands in df1 not in df2 = {len(uniqBands)}")
    print(uniqBands)

  return dfUniqComb, dfInt, IoU, normIoU
 

def savefig(filename):
  outdir = "images"
  plt.savefig(f"{outdir}/{filename}.png", dpi=300)
  plt.savefig(f"{outdir}/{filename}.pdf", dpi=300)
  print(f"Images saved as {outdir}/{filename}.png and .pdf")


def parse_args(args):
  # if already set, return immediately without overriding
  if (type(args) != list): return args
  # argparse organizes command line info for really simple changes
  parser = argparse.ArgumentParser(prog='main.py',
    description='Makes a plot of the US state borders, with dots at input data locations')
  parser.add_argument('--input_csv',    '-i',   help="your csv name in the /data/ dir", default='state_centers.csv')
  parser.add_argument('--color_bkgd',   '-cba', help="map background color", default='white')
  parser.add_argument('--color_border', '-cbo', help="state border color",   default='black')
  parser.add_argument('--color_dot',    '-cd',  help="data location color",  default='green')
  parser.add_argument('--dot_size',     '-ds',  help="data location dot size",  default='4')
  parser.add_argument('--colorscale',   '-cs',  help="for color scale plots",  default='gnuplot')
  parser.add_argument('--ull',                  help="override lat/lon finding",  action='store_true') # "use lat lon source"
  parser.add_argument('--DEBUG',                help="run in debug mode",  action='store_true')
  # "store_true" means "variable is True if specified in command with --DEBGU tag"
  args = parser.parse_args()
  return args


def execute_args(args): # rename to execute args
  args = parse_args(args)
  # create initial basemap object and figure axis object
  # basemap is similar to matplotlib fig object, with a few extensions from the Basemap library
  # we also have map_ax, which lets us customize cosmetics
  # with this function we just get the initial US map and set some colors
  # normally this is called as part of another plotting function
  if args.DEBUG: basemap, map_ax = configure_plot(args.color_bkgd, args.color_border, args.color_dot, args.DEBUG)
  return get_data(args.input_csv, args.DEBUG) # dataframe, missing_places


if __name__ == '__main__':
  # usage
  # python3 main.py -i "inputfile.csv"
  
  # this builds the dataframe object, with light formatting, and any missing entries
  args = sys.argv[1:]
  dataframe, missing_places = execute_args(args)
  # this makes a simple plot using your input arguments
  # for anything more than testing, make a new script for your input file :)
  basemap_mono, monocolor_ax = plot_locations_monocolor(dataframe, "Test plot", "noline", parse_args(args))
  #set_state_color(basemap_mono, "Kansas", "Blue") # does not work for all states, unclosed shapemaps
  savefig("test")
  plt.show()


