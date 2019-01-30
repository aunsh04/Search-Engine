# Query Evaluation
# by Will Enright

import sys

# Configuration values
relevancy_file_loc = "../test-collection/cacm.rel.txt"

# Check number of arguments
if len(sys.argv) != 3:
    print('To use this program:')
    print('\tpython3 evaluator.py [run_results_file] [output_file]')
    exit(1)

# Parse input and output files from the command line
results_file_loc = sys.argv[1]
output_file_loc = sys.argv[2]


# Compute evaluation values for each query in the supplied run
def main():

	# Parse the run result file
	# (Separate structure for each query)
	result_docs = {}
	with open(results_file_loc, 'r') as results_file:
		# EX: Q1 1 CACM-1519 18.572
		for l in results_file:
			terms = l.strip().split(' ')
			q_id = int(terms[0].lstrip('Q'))
			doc_id = terms[2]

			# Record result docs in order for the relevant query
			if q_id in result_docs:
				result_docs[q_id].append(doc_id)
			# Initialize doc list for each new query
			else:
				result_docs[q_id] = [doc_id]


	# Parse the relevancy file
	# (Separate structure for each query)
	query_list = []
	relevant_docs = {}
	with open(relevancy_file_loc, 'r') as relevancy_file:
		# EX: 19 Q0 CACM-3075 1
		for l in relevancy_file:
			terms = l.strip().split(' ')
			q_id = int(terms[0])
			doc_id = terms[2]

			# Record all relevant docs for the given query
			if q_id in relevant_docs:
				relevant_docs[q_id].append(doc_id)

			# Initialize record for each new query
			else:
				relevant_docs[q_id] = [doc_id]
				# Track the set of relevant queries (in order)
				query_list.append(q_id)


	# Initialize stat tracking variables for each query
	precisions = {}
	first_relevant_ranks = {}

	# Track evaluation variables across queries
	AP_values = []
	RR_values = []

	# Track average recall-precision pairs for graphing
	curve_points = {}

	# Output file for writing results as we go
	output_file = open(output_file_loc, 'w')


	# Walk over each query in relevancy set
	print("Evaluating Queries...")
	for q_id in query_list:

		# Eval variables for this query
		precision_vals = []
		recall_vals = []
		first_relevant_rank = None

		q_results = result_docs[q_id]
		q_relevant = relevant_docs[q_id]
		num_results = len(q_results)
		num_relevant = len(q_relevant)
		relevant_count = 0

		# Walk down the list of recovered files
		for i in range(0, num_results):
			doc_id = q_results[i]

			# Check if the given result is relevant
			relevant = False
			if doc_id in q_relevant:
				relevant = True

				# Update relevant_count
				relevant_count += 1

				# Set first_relevant_rank if necessary
				if not first_relevant_rank:
					first_relevant_rank = (i+1)

			# Precision
			precision = relevant_count / (i+1)
			precision_vals.append(precision)
			# Recall
			recall = relevant_count / num_relevant
			recall_vals.append(recall)

			# Track graph plotting data
			if relevant:
				recall_rounded = round(recall,2)

				if recall_rounded not in curve_points:
					curve_points[recall_rounded] = []

				curve_points[recall_rounded].append(precision)


		# Calculate eval values
		AP = sum(precision_vals) / len(precision_vals)
		AP_values.append(AP)
		RR = 1 / first_relevant_rank
		RR_values.append(RR)

		P5 = precision_vals[4]
		P20 = precision_vals[19]

		# Write results for query to file
		output_file.write("--------------------")
		output_file.write("\nQUERY " + str(q_id))
		
		output_file.write("\n\nPrecision/Recall Table:")
		output_file.write("\nP:\t" + " ".join([ '%.3f' % val for val in precision_vals]))
		output_file.write("\nR:\t" + " ".join([ '%.3f' % val for val in recall_vals]))

		output_file.write("\n\nP@5:\t" + str(P5))
		output_file.write("\nP@20:\t" + str(P20))
		output_file.write("\n\n")

	# Calculate mean values
	MAP = sum(AP_values) / len(AP_values)
	MRR = sum(RR_values) / len(RR_values)

	# Write mean values to output file and close file
	output_file.write("####################")
	output_file.write("\nMAP: " + str(MAP))
	output_file.write("\nMRR: " + str(MRR))
	output_file.close()

	# Calculate average precision for each recall val to be plotted
	for x in curve_points.keys():
		curve_points[x] = round(sum(curve_points[x])/len(curve_points[x]),3)
	with open("graph_data/" + output_file_loc, 'w') as graph_data:
		graph_data.write(str(curve_points))

	print("Run Evaluated!")


if __name__ == "__main__":
	main()