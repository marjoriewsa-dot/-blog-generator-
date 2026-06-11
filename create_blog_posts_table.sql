CREATE TABLE blog_posts (
    id SERIAL PRIMARY KEY,
    topic TEXT,
    title TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);