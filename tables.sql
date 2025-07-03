DROP TABLE IF EXISTS fact_table CASCADE;
DROP TABLE IF EXISTS dim_comment CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_posts CASCADE;
DROP TABLE IF EXISTS dim_topic CASCADE;

-- TOPIC CATEGORY
CREATE table if not EXISTS dim_topic(
  topic_id SERIAL PRIMARY KEY,
  topic_category TEXT,
  flair TEXT UNIQUE,
  keywords TEXT
);

-- POST
CREATE TABLE IF NOT EXISTS dim_posts (
  post_id TEXT PRIMARY KEY,
  title TEXT,
  selftext TEXT,
  author TEXT,
  author_role TEXT,
  score INT,
  upvote_ratio FLOAT,
  created_utc TIMESTAMP,
  num_comments INT,
  subreddit TEXT,
  is_self BOOLEAN,
  nsfw BOOLEAN,
  permalink TEXT
);

-- DATE
CREATE TABLE IF NOT EXISTS dim_date (
  date_id SERIAL PRIMARY KEY,
  full_date DATE UNIQUE,
  year INT,
  quarter INT,
  month INT,
  day INT,
  weekday TEXT
);

-- COMMENTS
CREATE TABLE IF NOT EXISTS dim_comment (
  comment_id TEXT PRIMARY KEY,
  created_utc TIMESTAMP,
  author TEXT,
  author_role TEXT,
  body TEXT,
  score INT,
  is_submitter BOOLEAN,
  parent_id TEXT,
  permalink TEXT
);

-- FACT TABLE
CREATE TABLE IF NOT EXISTS fact_table (
  comment_id TEXT REFERENCES dim_comment(comment_id),
  post_id TEXT REFERENCES dim_posts(post_id),
  topic_id INT REFERENCES dim_topic(topic_id),
  date_id INT REFERENCES dim_date(date_id),

  is_submitter BOOLEAN,         -- dim_comment.is_submitter
  comment_score INT,            -- dim_comment.score
  comment_length INT,           -- length of the comment
  sentiment TEXT,               -- positive, negative, neutral
  cluster_id INT                -- from k-means
);