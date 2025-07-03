import praw
import json
import re
import html
from langdetect import detect, LangDetectException

reddit = praw.Reddit(
  client_id='6NE27-qV7tGX07FuBfik3w',
  client_secret='fauqCWKne1OXmmtzPIABkNW57DFyZA',
  user_agent='Comment scraper'
)

subreddit_names = ['Anxiety', 'mentalhealth']
posts_data = []
total_comments = 0
target_comments = 5000
mod_keywords = ['announcement', 'rules', 'mod', 'moderator', 'admin', 'clarification', 'faq', 'meta', 'update', 'policy']

def is_mod_post(post):
  if post.distinguished in ['moderator', 'admin']:
    return True
  text = (post.title + " " + post.selftext).lower()
  return any(keyword in text for keyword in mod_keywords)

def is_mod_comment(comment):
  if comment.distinguished in ['moderator', 'admin']:
    return True
  text = comment.body.lower()
  return any(keyword in text for keyword in mod_keywords)

def clean_text(text):
  if not text:
    return ""
  text = html.unescape(text)                                                  # Decode HTML entities
  text = re.sub(r'\[deleted\]|\[removed\]', '', text, flags = re.IGNORECASE)  # remove deleted/removed
  text = re.sub(r'http\S+|www\S+', '', text)                                  # Remove URLs
  text = re.sub(r'&\w+;', '', text)                                           # Remove encoded HTML symbols
  text = re.sub(r'u/\w+|r/\w+', '', text)                                     # Remove mentions
  text = re.sub(r'>.*\n?', '', text)                                          # Remove blockquotes
  text = re.sub(r'\*+', '', text)                                             # Remove markdown asterisks
  text = re.sub(r'[^a-zA-Z\s]', '', text)                                     # Remove punctuation/numbers
  text = re.sub(r'[\r\n\t]', ' ', text)                                       # Normalize whitespace
  text = re.sub(r'[^\x00-\x7F]+', '', text)                                   # Remove non-ASCII characters
  text = re.sub(r'\s{2,}', ' ', text)                                         # Collapse multiple spaces
  return text.strip().lower()

def is_english(text):
  try:
    if len(text) < 20:
      return False
    return detect(text) == 'en'
  except LangDetectException:
    return False

for sub_name in subreddit_names:
  sub_comments = 0
  
  for submission in reddit.subreddit(sub_name).hot(limit = None):
    if sub_comments >= target_comments / len(subreddit_names):
      break

    if is_mod_post(submission):
      continue

    submission.comments.replace_more(limit = 0)
    comments = []

    for comment in submission.comments.list():
      if is_mod_comment(comment):
        continue

      clean_body = clean_text(comment.body)

      if not is_english(clean_body):
        continue

      comments.append({
        'comment_id': comment.id,
        'body': clean_body,
        'author': comment.author.name if comment.author else "[deleted]",
        'author_role': comment.distinguished,
        'score': comment.score,
        'created_utc': comment.created_utc,
        'is_submitter': comment.is_submitter,
        'parent_id': comment.parent_id,
        'permalink': comment.permalink
      })

    if comments:
      sub_comments += len(comments)
      total_comments += len(comments)

      post = {
        'post_id': submission.id,
        'title': clean_text(submission.title),
        'selftext': clean_text(submission.selftext),
        'author': submission.author.name if submission.author else "[deleted]",
        'author_role': submission.distinguished,
        'score': submission.score,
        'upvote_ratio': submission.upvote_ratio,
        # 'url': submission.url,
        'created_utc': submission.created_utc,
        'num_comments': len(comments),
        'subreddit': submission.subreddit.display_name,
        'flair': submission.link_flair_text,
        'is_self': submission.is_self,
        'nsfw': submission.over_18,
        'permalink': submission.permalink,
        'comments': comments
      }
      posts_data.append(post)

      print(f"{sub_comments} comments collected from r/{sub_name}")

with open('raw_posts.json', 'w', encoding='utf-8') as f:
  json.dump(posts_data, f, indent = 2, ensure_ascii=False)

print(f"\nScraped {len(posts_data)} posts with {total_comments} comments.")