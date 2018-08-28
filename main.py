
import pickle
from model import Model


# Main file for PoC pipeline

# ------- Step 0: Load surface form index and embeddings --------------------------------------------------------------

surface_forms = pickle.load(open("data/surface.pickle", "rb"))
model = Model.load(models_directory="data/models",
                   filename="wikidata-20170613-truthy-BETA-cbow-size=100-window=1-min_count=20")
print(model.metadata)

vector = model.wv.word_vec("Q6")
print(vector)

# ------- Step 1: Load table & recognize entities ---------------------------------------------------------------------





