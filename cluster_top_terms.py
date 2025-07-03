import psycopg2
import spacy
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer

conn = psycopg2.connect(
  host="127.0.0.1",
  user="postgres",
  password="sqljosie10.",
  dbname="reddit_data",
  port="5505"
)
cur = conn.cursor()

cur.execute("""
  SELECT p.post_id, p.title, p.selftext, f.cluster_id
  FROM dim_posts p
  JOIN fact_table f ON p.post_id = f.post_id
  WHERE f.cluster_id IS NOT NULL
""")
rows = cur.fetchall()
conn.close()

# --- Group posts by cluster ---
cluster_posts = {}
for post_id, title, selftext, cluster_id in rows:
  text = (title or '') + ' ' + (selftext or '')
  cluster_posts.setdefault(cluster_id, []).append(text)

nlp = spacy.load("en_core_web_md")

def lemmatize_text(text):
  doc = nlp(text)
  return " ".join([
    token.lemma_ for token in doc
    if not token.is_punct and not token.is_digit and token.pos_ in {"NOUN", "ADJ"}
  ])

# --- Lemmatize and vectorize per cluster ---
for cluster_id, texts in cluster_posts.items():
  lemmatized_texts = [lemmatize_text(t) for t in texts]
  vectorizer = TfidfVectorizer(
    max_features=7000,
    stop_words='english',
    ngram_range=(1, 2),
    lowercase=True,
    min_df=3,
    max_df=0.7
  )
  X = vectorizer.fit_transform(lemmatized_texts)
  terms = vectorizer.get_feature_names_out()
  tfidf_means = np.asarray(X.mean(axis=0)).flatten()
  top_indices = np.argsort(tfidf_means)[::-1][:20]
  top_terms = [terms[i] for i in top_indices]
  print(f"\nCluster {cluster_id} top terms:")
  print(", ".join(top_terms))