/*
SELECT * FROM dim_comment;
SELECT * FROM dim_posts;
SELECT * FROM dim_date;
SELECT * FROM dim_topic;
SELECT * FROM fact_table;
*/
-- topic label comment count
SELECT fcc.topic_label, SUM(fcc.comment_count) AS comment_count, STRING_AGG(fcc.flair, ', ') AS flairs
FROM (
	-- flair comment count
	SELECT ft.topic_id, t.topic_label, t.flair, COUNT(ft.topic_id) AS comment_count
	FROM fact_table ft
	JOIN dim_topic t ON ft.topic_id = t.topic_id
	GROUP BY ft.topic_id, t.topic_label, t.flair
	ORDER BY comment_count
) AS fcc
GROUP BY fcc.topic_label
ORDER BY comment_count;