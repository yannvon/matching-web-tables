
import pickle
from model import Model
import csv
import re
from string import digits
import networkx
import itertools

# Main file for PoC pipeline


# ------- HELPER FUNCTIONS  --------------------------------------------------------------------------------------------

# Given a text string, remove all non-alphanumeric
# characters (using Unicode definition of alphanumeric).
def strip_non_alphanum_and_digits(text):
    li = re.compile(r'\W+', re.UNICODE).split(text)
    string = " ".join(li)
    remove_digits = str.maketrans('', '', digits)
    return string.translate(remove_digits)


# Taken and slightly adapted from :
# https://networkx.github.io/documentation/stable/_modules/networkx/generators/classic.html#complete_multipartite_graph
def complete_multipartite_graph_with_weights(list_of_subsets):
    """Returns the complete multipartite graph with the specified subset sizes and use of embeddings as weight.

    Parameters
    ----------
    subset_sizes : tuple of integers or tuple of node iterables
       The arguments can either all be integer number of nodes or they
       can all be iterables of nodes. If integers, they represent the
       number of vertices in each subset of the multipartite graph.
       If iterables, each is used to create the nodes for that subset.
       The length of subset_sizes is the number of subsets.

    Returns
    -------
    G : NetworkX Graph
       Returns the complete multipartite graph with the specified subsets.

       For each node, the node attribute 'subset' is an integer
       indicating which subset contains the node.

    """
    # The complete multipartite graph is an undirected simple graph.
    G = networkx.Graph()

    if len(list_of_subsets) == 0:
        return G

    # add nodes with subset attribute
    for i in range(0, len(list_of_subsets)):
        for node in list_of_subsets[i]:
            G.add_node(node, subset=i)

    # Across subsets, all vertices should be adjacent.
    # We can use itertools.combinations() because undirected. FIXME directed and use permutations

    for subset1, subset2 in itertools.combinations(list_of_subsets, 2):
        G.add_edges_from(((u, v, {'weight': model.similarity("Q" + str(u), "Q" + str(v))})
                                   for u, v in itertools.product(subset1, subset2)))
        # FIXME normalize to get a meaningful transition probability
    return G


# ------- MAIN CODE  ---------------------------------------------------------------------------------------------------

# ------- Step 0: Load surface form index and embeddings ---------------------------------------------------------------

surface_forms = pickle.load(open("data/surface/surface.pickle", "rb"))
model = Model.load(models_directory="data/models",
                   filename="wikidata-20170613-truthy-BETA-cbow-size=100-window=1-min_count=20")

# -------- Small test --------------------------------------------------------------------------------------------------
# print(model.metadata)

# vector = model.wv.word_vec("Q4")
# print(vector)

# print(surface_forms['queen'])
# print(surface_forms['king']

# print(model.similarity("Q19643", "Q12097"))     # queen, king
# print(model.similarity("Q15862", "Q12097"))     # queen(band), king
# print(model.similarity("Q4", "Q12097"))         # earth, king


# ------- Step 1: Load table -------------------------------------------------------------------------------------------
rows = []
with open('data/webtables/countries.csv', "rt", encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        cells = []
        for cell in row:
            cells.append(cell)
        rows.append(cells)

print("Original csv table")
print(rows)

# ------- Step 2: Normalize cells --------------------------------------------------------------------------------------
# Step 1: Jump over first row if it is header (TODO header not always present, or more than a single row)
# Step 2: Convert to lowercase & remove non alpha numeric characters
# Example: "8 o'clock" to "o clock", "cat & Dog" to "cat dog"


normalized = []
for row in rows[1:]:
    new_row = []
    for cell in row:
        new_row.append(strip_non_alphanum_and_digits(cell.lower()))
    normalized.append(new_row)

print(normalized)

# FIXME John's to Johns instead of John s or keep '

# ------- Step 3: Look up in surface form index ------------------------------------------------------------------------
#         - try lowercase and capitalized
#         - try names together and by themselves

# FIXME better way to add to set
candidates = []
no_surface_found_count = 0
for row in normalized:
    candidate_row = []
    for cell in row:
        if cell is not "":

            cell_candidates = set()

            # Try word as is
            try:
                for can in surface_forms[cell]:
                    cell_candidates.add(can)
            except KeyError:
                pass

            # Try capitalized
            try:
                cap = cell.capitalize()
                for can in surface_forms[cap]:
                    cell_candidates.add(can)
            except KeyError:
                pass

            # Try each word if many
            try:
                for c in cell.split(" "):
                    for can in surface_forms[c]:
                        cell_candidates.add(can)
            except KeyError:
                pass

            if cell_candidates:
                candidate_row.append((cell, cell_candidates))
            else:
                no_surface_found_count += 1

    candidates.append(candidate_row)
print("Entities found in surface form:")
print(candidates)
print("Number of entities where no matching entitiy found:")
print(no_surface_found_count)

# ------- Step 4: Only keep candidates fow which we have embeddings ----------------------------------------------------
final_candidates = []
no_embedding_found_count = 0
embedding_found_count = 0
for row in candidates:
    candidate_row = []
    for (sf, entities) in row:
        cell_candidates = set()

        for i in entities:
            try:
                model.wv.word_vec("Q" + str(i))
                cell_candidates.add(i)
                embedding_found_count += 1
            except Exception:
                no_embedding_found_count += 1

        if cell_candidates:
            candidate_row.append((sf, cell_candidates))
    final_candidates.append(candidate_row)

print("Final candidates:")
print(final_candidates)
print("Number of entities where embedding found:")
print(embedding_found_count)
print("Number of entities where no embedding found:")
print(no_embedding_found_count)
# Note: at the moment not many embeddings are found, but I suspect it is because surface form index returns pretty
#       random entities and not in a good order, final surface form index will be better !

# ------- Step 5: Construct Disambiguation Graph -----------------------------------------------------------------------
subsets = []
for row in final_candidates:
    for (entity, candidates) in row:
        subsets.append(candidates)

G = complete_multipartite_graph_with_weights(subsets)
print("Nodes in the graph:")
print(G.nodes)
# Normalize weights to represent transition probabilities


# ------- Step 6: Perform PageRank and keep highest ranked entity ------------------------------------------------------
# FIXME add random jump when performing pagerank

rank_dict = networkx.pagerank(G, alpha=0.85)
print("Those are the assigned ranks by PageRank algorithm:")
print(rank_dict)

disambiguated_count = 0
disambiguated = []
for row in final_candidates:
    disambiguated_row = []
    for (entity, candidates) in row:
        max_rank = -1
        disambiguated_entity = None
        for c in candidates:
            if rank_dict[c] > max_rank:
                max_rank = rank_dict[c]
                disambiguated_entity = c
        disambiguated_count += 1
        disambiguated_row.append((entity, disambiguated_entity))

    disambiguated.append(disambiguated_row)

print("Disambiguated entities by row:")
print(disambiguated)
print("Nodes disambiguated:")
print(disambiguated_count)

