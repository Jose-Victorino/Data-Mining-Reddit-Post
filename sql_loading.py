import json
import psycopg2
import nltk
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.cluster import KMeans
from nltk.corpus import stopwords

nltk.download('stopwords')

df = pd.read_csv('DailyDialog.csv')
df = df.dropna(subset = ['text', 'sentiment'])

stop_words = stopwords.words('english')
vectorizer = TfidfVectorizer(
  max_features=5000,
  stop_words=stop_words,
  ngram_range=(1,2)  # Use unigrams and bigrams
)

# TF-IDF Vectorization
X = vectorizer.fit_transform(df['text'])
y = df['sentiment']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)

# Model training
model = DecisionTreeClassifier()
model.fit(X_train, y_train)

# Evaluate performance
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Connection to PostgreSQL
conn = psycopg2.connect(
  host = "127.0.0.1",
  user = "postgres",
  password = "sqljosie10.",
  dbname = "reddit_data",
  port = "5505"
)
cur = conn.cursor()

# Load JSON
with open('cleaned_posts.json', 'r', encoding = 'utf-8') as f:
  data = json.load(f)

# Train Sentiment Classifier
vectorizer = TfidfVectorizer(max_features = 5000)
vectorizer.fit(df['text'])

X_all = vectorizer.fit_transform(df['text'])
model = DecisionTreeClassifier()
model.fit(X_all, df['sentiment'])

def predict_sentiment(text):
  x = vectorizer.transform([text])
  return model.predict(x)[0]

flair_category = {
  "Advice Needed": "Support",
  "Need Support": "Support",
  "Needs A Hug/Support": "Support",
  "Venting": "Support",
  "Medication": "Support",
  "Therapy": "Support",

  "Anxiety Resource": "Mental Health Challenges",
  "Content Warning: Suicidal Thoughts / Self Harm": "Mental Health Challenges",
  "Content Warning: Eating Disorders": "Mental Health Challenges",
  "Content Warning: Sexual Assault": "Mental Health Challenges",
  "Content Warning: Violence": "Mental Health Challenges",
  "Content Warning: Addiction / Substance Abuse": "Mental Health Challenges",
  "Trigger Warning": "Mental Health Challenges",
  "Sadness / Grief": "Mental Health Challenges",

  "Inspiration / Encouragement": "Positive Experiences",
  "Good News / Happy": "Positive Experiences",
  "Share Your Victories": "Positive Experiences",
  "Uplifting": "Positive Experiences",
  "Progress!": "Positive Experiences",

  "DAE Questions": "Community Questions",
  "Question": "Community Questions",
  "Opinion / Thoughts": "Community Questions",

  "Work/School": "Life Experiences",
  "Driving": "Life Experiences",
  "Lifestyle": "Life Experiences",
  "Travel": "Life Experiences",
  "Sleep": "Life Experiences",
  "Health": "Life Experiences",
  "Family/Relationship": "Life Experiences",

  "Helpful Tips!": "Resources",
  "Resources": "Resources",
  "Research Study": "Resources",

  "Diary Entry": "Personal Expression",
  "Introduction": "Personal Expression",
  "Poetry": "Personal Expression",
  "Discussion": "Personal Expression"
}

def get_or_create_topic(flair):
  cur.execute("""
    INSERT INTO dim_topic (topic_category, flair, keywords)
    VALUES (%s, %s, %s)
    ON CONFLICT (flair) DO NOTHING
    RETURNING topic_id;
  """, (flair_category.get(flair, "Other"), flair, ''))
  result = cur.fetchone()
  if not result:
    cur.execute("SELECT topic_id FROM dim_topic WHERE flair = %s;", (flair,))
    result = cur.fetchone()
  return result[0]

def get_or_create_date_id(dt):
  cur.execute("""
    INSERT INTO dim_date (full_date, year, quarter, month, day, weekday)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (full_date) DO NOTHING
    RETURNING date_id;
  """, (dt.date(), dt.year, ((dt.month - 1) // 3 + 1), dt.month, dt.day, dt.strftime('%A')))
  result = cur.fetchone()
  if not result:
    cur.execute("SELECT date_id FROM dim_date WHERE full_date = %s;", (dt.date(),))
    result = cur.fetchone()
  return result[0]

# Gather all post texts for clustering
post_texts = []
post_ids = []
for post in data:
  text = (post.get('title', '') or '') + ' ' + (post.get('selftext', '') or '')
  post_texts.append(text)
  post_ids.append(post['post_id'])

# Vectorize post texts
vectorizer = TfidfVectorizer(max_features = 5000)
X_posts = vectorizer.fit_transform(post_texts)

# k-means clustering
k = 3  # (anxiety, depression, therapy)
kmeans = KMeans(n_clusters = k, random_state = 42)
cluster_ids = kmeans.fit_predict(X_posts)

# Map post_id to cluster_id
post_cluster_map = dict(zip(post_ids, cluster_ids))

# Gather all comment texts for clustering
comment_texts = []
comment_ids = []
for post in data:
  for comment in post['comments']:
    comment_texts.append(comment.get('body', '') or '')
    comment_ids.append(comment['comment_id'])

# Vectorize comment texts
vectorizer = TfidfVectorizer(max_features=5000)
X_comments = vectorizer.fit_transform(comment_texts)

# k-means clustering
k = 3  # (anxiety, depression, therapy) or any number you want
kmeans = KMeans(n_clusters = k, random_state = 42)
comment_cluster_ids = kmeans.fit_predict(X_comments)

# Map comment_id to cluster_id
comment_cluster_map = dict(zip(comment_ids, comment_cluster_ids))

for post in data:
  cur.execute("""
    INSERT INTO dim_posts (post_id, title, selftext, author, author_role, score, upvote_ratio, created_utc, num_comments, subreddit, is_self, nsfw, permalink)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (post['post_id'], post['title'], post['selftext'], post['author'], post['author_role'], post['score'], post['upvote_ratio'], post['created_utc'], post['num_comments'], post['subreddit'], post['is_self'], post['nsfw'], post['permalink'])
  )

  topic_id = get_or_create_topic(post['flair'])

  for comment in post['comments']:
    comment_cluster_id = int(comment_cluster_map.get(comment['comment_id'], -1))
    cur.execute("""
      INSERT INTO dim_comment (comment_id, author, author_role, body, score, created_utc, is_submitter, parent_id, permalink)
      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
      """, (comment['comment_id'], comment['author'], comment['author_role'], comment['body'], comment['score'], comment['created_utc'], comment['is_submitter'], comment['parent_id'], comment['permalink'])
    )

    dt = datetime.fromisoformat(comment['created_utc'])
    date_id = get_or_create_date_id(dt)

    sentiment = predict_sentiment(comment['body'])

    cur.execute("""
      INSERT INTO fact_table (comment_id, post_id, topic_id, date_id, is_submitter, comment_score, comment_length, sentiment, cluster_id)
      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
      """, (comment['comment_id'], post['post_id'], topic_id, date_id, comment['is_submitter'], comment['score'], len(comment['body']), sentiment, comment_cluster_id)
    )

conn.commit()
cur.close()
conn.close()

print("JSON data successfully loaded into PostgreSQL.")



# Title: Analyzing Public Sentiment and Trends in Reddit Comments on Mental Health Topics

# Description:
# - Data Warehouse Implementation
# DONE 1. Star schema with fact table for comment activity and dimensions for subreddit, user metadata, date, topic category
# DONE 2. Reddit API via Python (PRAW), preprocessing with pandas, loading into PostgreSQL.
# 3. OLAP Queries. Analyze user behavior by subreddit/topic; trends over time using `GROUP BY`, `ROLLUP` on date hierarchy.

# Data Mining Tasks:
# DONE - Classification: TF-IDF + Decision Tree to classify comments into positive, negative, and neutral sentiment. Joy, Sadness, Anger, Neutral, Fear
# DONE - Clustering: Apply k-Means to group discussions by theme (e.g., anxiety, depression, therapy).
# - Association Rule Mining: find co-occurrence between keywords/topics.
# DONE - Target Dataset: At least 5,000 Reddit comments using Reddit API from subreddits like r/mentalhealth, r/anxiety, r/depression.



##### dashboard (Dash or Streamlit) for visualization

##### Z-score