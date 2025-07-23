/*
SELECT * FROM dim_comment;
SELECT * FROM dim_posts;
SELECT * FROM dim_date;
SELECT * FROM dim_topic ORDER BY topic_category;
SELECT * FROM fact_table;
*/
-- topic category comment count
SELECT fcc.topic_category, SUM(fcc.comment_count) AS comment_count, STRING_AGG(fcc.flair, ', ') AS flairs
FROM (
	-- flair comment count
	SELECT ft.topic_id, t.topic_category, t.flair, COUNT(ft.topic_id) AS comment_count
	FROM fact_table ft
	JOIN dim_topic t ON ft.topic_id = t.topic_id
	GROUP BY ft.topic_id, t.topic_category, t.flair
	ORDER BY comment_count
) AS fcc
GROUP BY fcc.topic_category
ORDER BY comment_count;

-- total comments per day
SELECT d.month, d.weekday, COUNT(*) AS total_comments
FROM fact_table ft
JOIN dim_date d ON ft.date_id = d.date_id
GROUP BY ROLLUP (d.month, d.weekday)
ORDER BY d.month, d.weekday;

-- average comment score per topic
SELECT t.flair AS topic, ROUND(AVG(ft.comment_score), 2) AS avg_score
FROM fact_table ft
JOIN dim_topic t ON ft.topic_id = t.topic_id
GROUP BY t.flair
ORDER BY avg_score DESC;

-- sentiment totals
SELECT COUNT(sentiment_label) AS total, sentiment_label
FROM fact_table
GROUP BY sentiment_label;

-- sentiment comment count per topic
SELECT t.flair AS topic, ft.sentiment_label, COUNT(*) AS num_comments
FROM fact_table ft
JOIN dim_topic t ON ft.topic_id = t.topic_id
GROUP BY t.flair, ft.sentiment_label
ORDER BY t.flair, ft.sentiment_label;

-- weekly activity
SELECT d.weekday, COUNT(ft.comment_id) AS total_comments
FROM fact_table ft
JOIN dim_date d ON ft.date_id = d.date_id
GROUP BY d.weekday
ORDER BY total_comments DESC;

-- top active users
SELECT c.author, COUNT(*) AS comment_count
FROM fact_table ft
JOIN dim_comment c ON ft.comment_id = c.comment_id
GROUP BY c.author
ORDER BY comment_count DESC
LIMIT 10;

-- comment distribution on cluster_id
SELECT cluster_id, COUNT(*) AS total_comments
FROM fact_table
GROUP BY cluster_id
ORDER BY total_comments DESC;

-- Sentiments over the week
SELECT d.month, d.weekday, ft.sentiment_label, COUNT(*) AS count
FROM fact_table ft
JOIN dim_date d ON ft.date_id = d.date_id
GROUP BY d.month, d.weekday, ft.sentiment_label
ORDER BY d.month, d.weekday;