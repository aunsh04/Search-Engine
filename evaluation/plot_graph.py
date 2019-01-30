# Script to plot line graph for evaluation results
# by: Will Enright

import matplotlib.pyplot as plt
from os import listdir
import ast
import sys

# Set location of graph data
graph_data_dir = "graph_data/"

# Get all the graph data files
files = sorted([f for f in listdir(graph_data_dir)])

# Initialize plot features
plt.suptitle("Precision-Recall Curve for All Runs")
plt.ylabel("Precision")
plt.xlabel("Recall")
plt.axis([0.0,1.0,0.0,1.0])

# Walk over each file to plot the line it represents
for file in files:
	# Extract a name for the run from the filename
	run_name = file.split('.')[0].split('_',1)[1]

	# Open the file and load the dictionary of points
	with open(graph_data_dir + file, 'r') as data:
		coords = ast.literal_eval(data.read())

		# Extract x and y axis
		x_axis = [float(x) for x in sorted(coords.keys())]
		y_axis = [float(coords[x]) for x in x_axis]

	# Add the plot to the chart
	plt.plot(x_axis,y_axis,label=run_name)

# Generate the graph
plt.legend()
plt.show()