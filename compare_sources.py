import numpy as np
import matplotlib.pyplot as plt
from main import *

if __name__ == '__main__':
  # make a dummy namespace with defaults, then overwrite the csv you want for each new dataframe
  from argparse import Namespace
  dummy_args = Namespace(input_csv    = "dummy.csv", 
                         color_bkgd   = "white", 
                         color_border = "black",   
                         color_dot    = "blue", 
                         dot_size     = 4,       
                         colorscale   = "gnuplot", 
                         ull          = True, 
                         DEBUG        = False)

  # completed data sources, that we will harvest info from
  dummy_args.input_csv = "EmoAnthologyData.csv"
  dataframe_Anthology, missing_places_Anthology = execute_args(dummy_args)

  dummy_args.input_csv = "VultureData.csv"
  dataframe_Vulture, missing_places_Vulture = execute_args(dummy_args)

  dummy_args.input_csv = "ENAOData.csv"
  dataframe_ENAO, missing_places_ENAO = execute_args(dummy_args)

  dummy_args.input_csv = "RollingStoneData.csv"
  dataframe_RStone, missing_places_RStone = execute_args(dummy_args)

  dummy_args.input_csv = "AltPressData.csv"
  dataframe_AltPress, missing_places_AltPress = execute_args(dummy_args)

  dfs = {"Anthology" : dataframe_Anthology,
         "Vulture"   : dataframe_Vulture, 
         "RStone"    : dataframe_RStone, 
         "AltPress"  : dataframe_AltPress,
         "ENAO"      : dataframe_ENAO,
        }

  # in each df, add a column that's just the dfs name
  # drop columns that are df-specific, and keep only columns that appear in all dfs
  # drop duplicate band name entries (i.e. if MCR has two influential albums, etc.)
  keepColumns = ["Band", "City", "State", "State_id", "Year formed", "Year disbanded", "Latitude", "Longitude",
                 "Name", "City:State_id"]
  for key, df in dfs.items():
    df["Name"] = key
    allColumns = df.columns
    dropColumns = [column for column in allColumns if column not in keepColumns]
    df.drop(columns=dropColumns, inplace=True)
    dfs[key] = df.drop_duplicates(subset=['Band'])
    print(key)
    source_stats(df)
    print()
     
  # combine into one df
  combinedData = pd.concat(dfs)
  uniqueCombinedData = combinedData.drop_duplicates(subset=['Band'])

  print("        Dataset : size , unique bands")
  print("-------------------------------------")
  for key, df in dfs.items():
    sourceSize = len(df)
    uniqueSourceSize = len(df.drop_duplicates(subset=['Band'])) # already done!
    print(f"{key:>15} : {sourceSize:^5}, {uniqueSourceSize:^4}")
  print("-------------------------------------")
  print(f"       Combined : {len(combinedData):^5}, {len(uniqueCombinedData):^5}")
  print("-------------------------------------")
  print()

  # combined stats - dealt with in file 'plot_emo_compare_VERA.py'
  #mini_csv_output(combinedData, keepColumns) # read out parts of dataframe before removing anything
  # TODO: couldn't you have just created a csv instead of copying columns by hand?
  # TODO: write small number on city dots with multiple bands?
  
  processed = []
  dfCombs, dfInts, dfIoUs, dfNormIoUs = {}, {}, {}, {}
  for key1, df1 in dfs.items():
    for key2, df2 in dfs.items():
      combKey = f"{key1}:{key2}"
      if (key1 == key2): continue
      if (combKey in processed) or (f"{key2}:{key1}" in processed): continue
      print(combKey)
      dfComb, dfInt, IoU, normIoU = combine_two_dataframes(df1, df2)
      dfCombs[combKey] = dfComb
      dfInts[combKey]  = dfInt
      dfIoUs[combKey]  = IoU
      dfNormIoUs[combKey]  = normIoU
      processed.append(combKey)
      print()

  print("Individual dataset compared against combined dataset")
  for iterkey, df in dfs.items():
    print(iterkey)
    dfs_    = {key : value for key, value in dfs.items() if key != iterkey}
    dfComp_ = pd.concat(dfs_)
    dfComp_ = dfComp_.drop_duplicates(subset=["Band"])
    dfComb_, dfInt_, IoU_, normIoU_ = combine_two_dataframes(df, dfComp_, printIndivs=True)
    print()

  #df.to_csv('output.csv', index=False) # for printing/saving

  rawIoUs = [val for key, val in dfIoUs.items()]
  rawNormIoUs = [val for key, val in dfNormIoUs.items()]
  #print(min(rawIoUs), max(rawIoUs))
  #print(min(rawNormIoUs), max(rawNormIoUs))
  rawVals = rawIoUs + rawNormIoUs
  #print(rawVals)
  #print(min(rawVals), max(rawVals))

  fig, ax2d = plt.subplots()
  # upper right vals
  UR = np.array([[0.0, dfIoUs["Anthology:Vulture"], dfIoUs["Anthology:RStone"], dfIoUs["Anthology:AltPress"], dfIoUs["Anthology:ENAO"]],
                [0.0, 0.0, dfIoUs["Vulture:RStone"], dfIoUs["Vulture:AltPress"], dfIoUs["Vulture:ENAO"]],
                [0.0, 0.0, 0.0, dfIoUs["RStone:AltPress"], dfIoUs["RStone:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, dfIoUs["AltPress:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, 0.0]])
  UR = -1*UR
  # lower left vals (made as upper right then transposed)
  LL = np.array([[0.0, dfNormIoUs["Anthology:Vulture"], dfNormIoUs["Anthology:RStone"], dfNormIoUs["Anthology:AltPress"], dfNormIoUs["Anthology:ENAO"]],
                [0.0, 0.0, dfNormIoUs["Vulture:RStone"], dfNormIoUs["Vulture:AltPress"], dfNormIoUs["Vulture:ENAO"]],
                [0.0, 0.0, 0.0, dfNormIoUs["RStone:AltPress"], dfNormIoUs["RStone:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, dfNormIoUs["AltPress:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, 0.0]])
  LL = LL.T # transpose 
  X = UR + LL
  vmin, vmax = -0.5, 1.1
  midVal = (vmax + vmin) / 2.0
  #Xplot = X / midVal
  for i in range(len(dfs.keys())):
    X[i, i] = np.nan
  cmap = plt.cm.PRGn.copy()
  cmap.set_bad(color='white')
  im = ax2d.imshow(X, cmap=cmap, vmin=vmin, vmax=vmax)
  cbar = fig.colorbar(im, ax=ax2d, label="", shrink=0.9)
  cbar.ax.axhline(y=midVal, color='black', linewidth=2) # Draw a horizontal line at the center value on the colorbar
  cbar.ax.yaxis.set_tick_params(labelright=False, color="white") # remove ticks
  # labeling the two ranges properly
  cbar.ax.invert_yaxis()
  ax2d.annotate('IoU', xy=(1.15, 0.685), xytext=(1.155, 0.685), xycoords='axes fraction', 
            fontsize=12, ha='center', va='bottom', rotation = 90)
  ax2d.annotate('Normed IoU', xy=(1.15, 0.12), xytext=(1.155, 0.125), xycoords='axes fraction', 
            fontsize=12, ha='center', va='bottom', rotation = 90)

  labels = [key for key in dfs.keys()]
  ax2d.set_xticks(range(len(labels)), labels=labels,
                rotation=45, ha="right", rotation_mode="anchor")
  ax2d.set_yticks(range(len(labels)), labels=labels)
  for i in range(len(labels)):
    for j in range(len(labels)):
      # j > i is upper right, j < i is lower left
      if (j < i): temptext = f"{100*X[i, j]:.0f}%"
      else:       temptext = f"{X[i, j]:.2f}"
      temptext = temptext.replace("-", "") # remove negative signs
      realtext = temptext if temptext not in ["0.00", str(midVal), "nan"] else ""
      text = ax2d.text(j, i, realtext,
                     ha="center", va="center", color="black")

  ax2d.set_title("IoU and Normed IoU for All Source Combinations")
  # Turn spines off and create white grid.
  # styling from here: https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
  ax2d.spines[:].set_visible(False)
  ax2d.set_xticks(np.arange(X.shape[1]+1)-.5, minor=True)
  ax2d.set_yticks(np.arange(X.shape[0]+1)-.5, minor=True)
  ax2d.grid(which="minor", color="w", linestyle='-', linewidth=3)
  ax2d.tick_params(which="both", bottom=False, left=False)


  # end IoU plotting, begin combined/intersected size plotting
  dfCombsSize = {key : len(dfCombs[key]) for key in dfCombs}
  dfIntsSize = {key : len(dfInts[key]) for key in dfInts}
  print(dfCombsSize)
  print(dfIntsSize)
  fig, ax2dS = plt.subplots()
  UR = np.array([[0.0, dfCombsSize["Anthology:Vulture"], dfCombsSize["Anthology:RStone"], dfCombsSize["Anthology:AltPress"], dfCombsSize["Anthology:ENAO"]],
                [0.0, 0.0, dfCombsSize["Vulture:RStone"], dfCombsSize["Vulture:AltPress"], dfCombsSize["Vulture:ENAO"]],
                [0.0, 0.0, 0.0, dfCombsSize["RStone:AltPress"], dfCombsSize["RStone:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, dfCombsSize["AltPress:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, 0.0]])
  #UR = -1*UR
  # lower left vals (made as upper right then transposed)
  LL = np.array([[0.0, dfIntsSize["Anthology:Vulture"], dfIntsSize["Anthology:RStone"], dfIntsSize["Anthology:AltPress"], dfIntsSize["Anthology:ENAO"]],
                [0.0, 0.0, dfIntsSize["Vulture:RStone"], dfIntsSize["Vulture:AltPress"], dfIntsSize["Vulture:ENAO"]],
                [0.0, 0.0, 0.0, dfIntsSize["RStone:AltPress"], dfIntsSize["RStone:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, dfIntsSize["AltPress:ENAO"]],
                [0.0, 0.0, 0.0, 0.0, 0.0]])
  LL = LL.T # transpose 
  Y = UR + LL
  for i in range(len(dfs.keys())):
    Y[i, i] = np.nan
  # no cbar
  im2 = ax2dS.imshow(Y, cmap="grey", vmax=0, vmin=-9999999)

  ax2dS.set_xticks(range(len(labels)), labels=labels,
                rotation=45, ha="right", rotation_mode="anchor")
  ax2dS.set_yticks(range(len(labels)), labels=labels)
  for i in range(len(labels)):
    for j in range(len(labels)):
      temptext = f"{Y[i, j]:.0f}"
      realtext = temptext if temptext not in ["0.00", str(midVal), "nan"] else ""
      text = ax2dS.text(j, i, realtext,
                     ha="center", va="center", color="black")

  ax2dS.set_title("Union and Intersection Counts for All Source Combinations")
  # Turn spines off and create white grid.
  # styling from here: https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
  ax2dS.spines[:].set_visible(True)
  ax2dS.set_xticks(np.arange(X.shape[1]+1)-.5, minor=True)
  ax2dS.set_yticks(np.arange(X.shape[0]+1)-.5, minor=True)
  ax2dS.grid(which="minor", color="black", linestyle='-', linewidth=1)
  ax2dS.tick_params(which="both", bottom=False, left=False)
  plt.plot([-0.5, 4.5], [-0.5, 4.5], color="black")
  ax2dS.annotate('Union', xy=(0.54, 0.47), xytext=(0.54, 0.47), xycoords='axes fraction', 
            fontsize=12, ha='center', va='bottom', rotation = -45,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", lw=1))
  ax2dS.annotate('Intersection', xy=(0.48, 0.37), xytext=(0.48, 0.37), xycoords='axes fraction', 
            fontsize=12, ha='center', va='bottom', rotation = -45,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", lw=1))

  plt.show()




