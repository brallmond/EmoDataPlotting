import numpy as np
import matplotlib.pyplot as plt
from main import *

if __name__ == '__main__':
  # boilerplate code you need for everything, and adjust per script
  input_csv_        = "combined_AN_V_ENAO_RS_AP.csv" 
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
  dataframeBase, missing_places = execute_args(args)
  # end boilerplate

  #mini_csv_output(dataframe) # read out parts of dataframe before removing anything
  print(f"Size before dropping duplicate bands: {len(dataframeBase)}")
  dataframeBase.drop_duplicates(subset=['Band'], inplace=True) # drop duplicate bands
  print(f"Size after  dropping duplicate bands: {len(dataframeBase)}")

  dataframeGT1 = dataframeBase[dataframeBase["In x sources"] > 1].copy() # 2 or more references in sources
  dataframeGT2 = dataframeBase[dataframeBase["In x sources"] > 2].copy() # 3 or more references in sources
  dataframeGT3 = dataframeBase[dataframeBase["In x sources"] > 3].copy() # 4 or more references in sources

  saveYearCommonRange = 0
  saveYearSums = []
  for label, dataframe in zip(["Any", "2 or More", "3 or More", "4 or More"], 
                              [dataframeBase, dataframeGT1, dataframeGT2, dataframeGT3]):
    plot_vital_statistics(dataframe)
    title_InX = "How Often Bands Are Mentioned In Multiple Sources"
    xlabel_InX = "Number of Sources Mentiond In"
    binEdges = [1, 2, 3, 4, 5, 6] 
    axtemp, _, _  = plot_1d_hist(dataframe["In x sources"].to_list(), title_InX, xlabel_InX, binEdges=binEdges, legendOn=False)
    empty_handle = plt.Line2D([], [], color='none', label='An Empty Entry')
    handles = [empty_handle, empty_handle, empty_handle]
    labels = ["Total = 232", "Only 1 = 143", "More Than 1 = 89"]
    axtemp.legend(handles, labels, loc="upper right")

    ax_act, years, yearSums = plot_active_bands_per_year(dataframe)
    add_source_windows(ax_act)
    if (label == "Any"): saveYearCommonRange = years
    if (label == "Any") or (label == "2 or More"): saveYearSums.append(yearSums)
  
    bandNames = set(dataframe["Band"].to_list())
    bandNamesTotal = len(bandNames)
    count = 0
    for band in bandNames:
      splitName = band.split(" ")
      if (splitName[0] == "The"): count += 1
    print(f"Band names starting with \"The\": {count}")
    print(f"Out of {bandNamesTotal} bands, that's a ratio of {count/bandNamesTotal:.2f}")
    print()
    # >0 0.15
    # >1 0.14
    # >2 0.16
    # ridiculous invariant

    if (label == "Any"): # get stat info on first pass through, when all entries are present
      bandsOneSource = dataframe[dataframe["In x sources"] == 1] # this is the whole df of single source entries
      bandsOneSourceBand = dataframe[dataframe["In x sources"] == 1]["Band"].to_list()
      bandsOneSourceBand.sort()
      print(f"Bands appearing in only one source: {len(bandsOneSource)}")
      print(bandsOneSourceBand)
      print()
  
      bandsMoreThanOne = np.sum(dataframe["In x sources"] > 1)
      print(f"Bands appearing in more than one source: {bandsMoreThanOne}")
      print()
  
      for i in [3, 4, 5]:
        bandsEqualXSource = dataframe[dataframe["In x sources"] == i]["Band"].to_list()
        print(f"Bands appearing in {i} sources: {len(bandsEqualXSource)}")
        print(bandsEqualXSource)
        print()

      sources = ["Anthology", "Vulture", "ENAO", "RStone", "AltPress"]
      #bandsOneSourceName = bandsOneSource["Name"].to_list()
      bandsOneSourceName = bandsOneSource["Dataset name"].to_list()
      print("Number of unique entries in source!")
      for source in sources:
        isSource = [sourceName == source for sourceName in bandsOneSourceName]
        print(f"{source} = {np.sum(isSource)}")
        print(f"Bands unique to {source}:")
        #bandsOneSource_ = bandsOneSource[bandsOneSource["Name"] == source]["Band"].to_list()
        bandsOneSource_ = bandsOneSource[bandsOneSource["Dataset name"] == source]["Band"].to_list()
        bandsOneSource_.sort()
        print(bandsOneSource_)
        print()
    
    # US map plotting
  
    # only do this for plotting, need the stats otherwise
    dataframe, droppedBands0 = remove_Canada(dataframe)
    dataframe, droppedBands1 = drop_data_matching_condition(dataframe, "Band", "City", "Singapore")
    dataframe, droppedBands2 = drop_data_matching_condition(dataframe, "Band", "City", "Cardiff")
    dataframe, droppedBands3 = drop_data_matching_condition(dataframe, "Band", "City", "Derby")
    droppedBands = helper_flatten([droppedBands0, droppedBands1, droppedBands2, droppedBands3])
    print(f"Bands dropped are: {droppedBands}")
  
    # plot the csv data on the map
    plural = "s" if label != "Any" else ""
    plot_title = f"Bands Appearing in {label} Source{plural}"
    #_, monocolor_ax = plot_locations_monocolor(dataframe, plot_title, "noline", args)
    #cityDupes = calculate_duplicates(dataframe, "City")
    #add_labels_to_plot(dataframe, "Band", "State_id")
    #add_missing_bands_textbox(monocolor_ax, droppedBands)
    #add_duplicates_textbox(monocolor_ax, cityDupes, initialText="> 1 Band: ")
    # replace this with a number at the location
  
    # here we plot with with a color scale 
    colorscale_col = "Year formed"
    colorscale_label = "Year Formed"
    basemap_colorscale, colorscale_ax = plot_locations_colorscale(dataframe, plot_title, colorscale_col, colorscale_label, args)
    #add_labels_to_plot(dataframe, "Band", "State_id")
    #add_missing_bands_textbox(colorscale_ax, droppedBands)
    #add_duplicates_textbox(colorscale_ax, cityDupes, initialText="> 1 Band: ")
  
    # here we make some standard timeline plots
    # TODO: fix formatting on these, comparing with ax1ds from vital statistics
    #stacked_ax = plot_stacked_timeline(dataframe, "Year formed", plot_column = "Year formed")
    #stacked_ax = plot_stacked_timeline(dataframe, "Year disbanded", plot_column = "Year disbanded")
    #timeline_ax = plot_activity_periods(dataframe, "Band", "Year formed", "Year disbanded")
 
     
    dataframe["Generation"] = [assign_generation(year) for year in dataframe["Year formed"].to_list()]
    #dataframe["Generation2"] = [assign_generation(year, [2000], ["pre-millenium", "post-millenium"]) for year in dataframe["Year formed"].to_list()]
    #dataframe["Generation3"] = [assign_generation(year, [2001], ["pre-9/11", "post-9/11"]) for year in dataframe["Year formed"].to_list()]
    #dataframe["Generation4"] = [assign_generation(year, [1994], ["pre-Nirvana", "post-Nirvana"]) for year in dataframe["Year formed"].to_list()]
    #dataframe["Generation5"] = [assign_generation(year, [1995], ["pre-Cap'n Jazz", "post-Cap'n Jazz"]) for year in dataframe["Year formed"].to_list()]
    categ6_labels = ["1985-1994", "1995-2003", "2004-2012", "After 2012"]
    dataframe["Generation6"] = [assign_generation(year, [1994, 2003, 2012], categ6_labels) for year in dataframe["Year formed"].to_list()]

    basemap_categ, category_ax = plot_locations_categories(dataframe, "Categorization by Number of Sources Mentioned In", "In x sources", args)
    categ_labels = ["1985-1994", "1995-2001", "2002-2012", "After 2012"] #copied from main 
    categ_tag = ", Categorized by Year Formed"
    basemap_categ1, category_ax1 = plot_locations_categories(dataframe, plot_title + categ_tag, "Generation", args, 
                                    category_order=categ_labels)
    #basemap_categ2, category_ax2 = plot_locations_categories(dataframe, plot_title, "Generation2", args)
    #basemap_categ3, category_ax3 = plot_locations_categories(dataframe, plot_title, "Generation3", args)
    #basemap_categ4, category_ax4 = plot_locations_categories(dataframe, plot_title, "Generation4", args)
    #basemap_categ5, category_ax5 = plot_locations_categories(dataframe, plot_title, "Generation5", args)
    basemap_categ6, category_ax6 = plot_locations_categories(dataframe, plot_title + categ_tag, "Generation6", args, 
                                    category_order=categ6_labels)

    plt.show()

  # custom plot
  fig, axCust = plt.subplots()
  axCust.stairs(saveYearSums[0], saveYearCommonRange, label="Mentioned in Any Source", color="Black")
  axCust.stairs(saveYearSums[1], saveYearCommonRange, label="Mentioned in >1 Source", color="Blue", linestyle="dashed")
  axCust.legend(loc="upper left")
  axCust.set_title("Number of Bands Active in Each Year\n(reunions not considered)")
  axCust.set_ylabel("Number of Bands")
  axCust.set_xlabel("Year")
  add_source_windows(axCust)
  plt.show() 









