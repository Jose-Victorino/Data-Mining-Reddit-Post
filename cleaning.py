import json
from datetime import datetime, timezone

with open('raw_posts.json', 'r', encoding='utf-8') as f:
  raw_data = json.load(f)

cleaned_data = []
total_cleaned_posts = 0
total_cleaned_comments = 0
mod_keywords = ['announcement', 'rules', 'mod', 'moderator', 'admin', 'clarification', 'faq', 'meta', 'update', 'policy']

def format_datetime(utc_timestamp):
  return datetime.fromtimestamp(utc_timestamp, tz=timezone.utc).isoformat()

def is_meaningful(text):
  if len(text) < 20:                        # Remove short comments
    return False
  if not any(c.isalpha() for c in text):    # Must contain alphabetic characters
    return False
  if len(text) > 2000:                      # remove very long comments 
    return False
  return True

for post in raw_data:
  cleaned_post = {
    'post_id': post['post_id'],
    'title': post['title'],
    'selftext': post['selftext'],
    'author': post['author'],
    'author_role': post['author_role'],
    'score': post['score'],
    'upvote_ratio': post['upvote_ratio'],
    'created_utc': format_datetime(post['created_utc']),
    'num_comments': 0,
    'subreddit': post['subreddit'],
    'flair': post['flair'],
    'is_self': post['is_self'],
    'nsfw': post['nsfw'],
    'permalink': post['permalink'],
    'comments': []
  }

  for comment in post['comments']:
    if comment['body'] == "":
      continue
    if comment['author'] == "[deleted]":
      continue
    if not is_meaningful(comment['body']):
      continue

    cleaned_comment = {
      'comment_id': comment['comment_id'],
      'body': comment['body'],
      'author': comment['author'],
      'author_role': comment['author_role'],
      'score': comment['score'],
      'created_utc': format_datetime(comment['created_utc']),
      'is_submitter': comment['is_submitter'],
      'parent_id': comment['parent_id'],
      'permalink': comment['permalink']
    }
    cleaned_post['comments'].append(cleaned_comment)

  if cleaned_post['comments']:
    cleaned_post['num_comments'] = len(cleaned_post['comments'])
    total_cleaned_posts += 1
    total_cleaned_comments += len(cleaned_post['comments'])
    cleaned_data.append(cleaned_post)

with open('cleaned_posts.json', 'w', encoding='utf-8') as f:
  json.dump(cleaned_data, f, indent = 2, ensure_ascii = False)

print(f"Data cleaned. {total_cleaned_posts} posts remaining with {total_cleaned_comments} comments.")