-- SQL queries to check developer data
-- Run these queries in your PostgreSQL client or pgAdmin

-- 1. Check all developers
SELECT 
    id,
    developer_id,
    name,
    email,
    api_token,
    active,
    created_at,
    last_sync
FROM developers
ORDER BY created_at DESC;

-- 2. Check activity summary by developer
SELECT 
    developer_id,
    COUNT(*) as record_count,
    MIN(timestamp) as first_activity,
    MAX(timestamp) as last_activity,
    SUM(duration) / 3600.0 as total_hours
FROM activity_records
WHERE developer_id IS NOT NULL
GROUP BY developer_id
ORDER BY last_activity DESC;

-- 3. Check today's activity
SELECT 
    developer_id,
    COUNT(*) as activities_today,
    SUM(duration) / 3600.0 as hours_today
FROM activity_records
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY developer_id
ORDER BY hours_today DESC;

-- 4. Check recent activity (last 5 records)
SELECT 
    developer_id,
    timestamp,
    duration,
    LEFT(activity_data::text, 100) as data_preview
FROM activity_records
ORDER BY timestamp DESC
LIMIT 5;

-- 5. Check for developers without any activity
SELECT 
    d.developer_id,
    d.name,
    d.created_at,
    d.api_token
FROM developers d
LEFT JOIN activity_records ar ON d.developer_id = ar.developer_id
WHERE ar.id IS NULL
AND d.active = true;

-- 6. Quick statistics
SELECT 
    (SELECT COUNT(*) FROM developers) as total_developers,
    (SELECT COUNT(*) FROM developers WHERE active = true) as active_developers,
    (SELECT COUNT(*) FROM activity_records) as total_activities,
    (SELECT COUNT(DISTINCT developer_id) FROM activity_records) as developers_with_activities;