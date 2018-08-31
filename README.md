# Matching Web Tables through Embeddings
## Installation

Create venv and install jupyter. Then

pip install gensim
pip install wikidata
pip install networkx

## 1 Surface Form Index
Surface form index was created from latest dump from https://dumps.wikimedia.org/wikidatawiki/entities/.
*wikidata-20180820-all.json.bz2* 

Then the index creation was done using the scripts from:
https://github.com/eXascaleInfolab/ml-phd-scripts_wikidata

## 2 Embeddings
The trained model was taken from wembedder (https://github.com/fnielsen/wembedder)
The model used is https://zenodo.org/record/823195

Some useful commands are:
https://tools.wmflabs.org/wembedder/api/vector/Q42
https://github.com/fnielsen/wembedder/blob/master/wembedder/app/views.py
https://radimrehurek.com/gensim/models/word2vec.html

## 3 Other sources
Main paper followed: https://scholar.google.ch/scholar?cluster=5238909793046189304&hl=en&as_sdt=0,5
DoSeR: https://github.com/quhfus/DoSeR

