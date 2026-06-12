from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx
from datetime import datetime
import logging
import os
from supabase import create_client

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# =========================
# ENV VARIABLES
# =========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# =========================
# SUPABASE
# =========================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# STATIC FOLDER
# =========================

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# HOME PAGE
# =========================

@app.get("/", response_class=HTMLResponse)
async def home():

    posts_html = ""

    try:
        response = supabase.table("blog_posts").select("*").execute()

        posts = response.data

        for post in posts:
            posts_html += f"""
            <li>
                <strong>{post['title']}</strong><br>
                {post['created_at']}
            </li>
            <hr>
            """

    except Exception as e:
        logging.error(str(e))

    return f"""
    <html>

    <head>
        <title>Blog Generator</title>

        <style>

            body {{
                font-family: Arial;
                max-width: 800px;
                margin: auto;
                padding: 40px;
            }}

            input {{
                width: 70%;
                padding: 10px;
            }}

            button {{
                padding: 10px 20px;
            }}

        </style>

    </head>

    <body>

        <h1>Blog Generator</h1>

        <form action="/generate/" method="post">

            <input
                type="text"
                name="topic"
                placeholder="Enter blog topic"
                required
            >

            <button type="submit">
                Generate
            </button>

        </form>

        <h2>Previous Blog Posts</h2>

        <ul>
            {posts_html}
        </ul>

    </body>

    </html>
    """

# =========================
# GENERATE BLOG
# =========================

@app.post("/generate/", response_class=HTMLResponse)
async def generate_blog(topic: str = Form(...)):

    try:

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"Write a detailed blog post about {topic}"
                }
            ],
            "max_tokens": 1000
        }

        async with httpx.AsyncClient(timeout=60.0) as client:

            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )

            response.raise_for_status()

            result = response.json()

            blog_content = result["choices"][0]["message"]["content"]

        title = topic.title()

        created_at = datetime.now().isoformat()

        # SAVE TO SUPABASE

        supabase.table("blog_posts").insert({
            "topic": topic,
            "title": title,
            "content": blog_content,
            "created_at": created_at
        }).execute()

        # CREATE HTML FILE

        filename = f"{title.replace(' ', '_')}.html"

        html_path = f"static/{filename}"

        html_content = f"""
        <html>
            <head>
                <title>{title}</title>
            </head>

            <body style="font-family: Arial; padding: 40px;">

                <h1>{title}</h1>

                <p>{blog_content}</p>

            </body>
        </html>
        """

        with open(html_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        # SEND TO DISCORD

        async with httpx.AsyncClient(timeout=60.0) as client:

            with open(html_path, "rb") as file:

                files = {
                    "file": (
                        filename,
                        file,
                        "text/html"
                    )
                }

                data = {
                    "content": f"New Blog Post: {title}"
                }

                await client.post(
                    DISCORD_WEBHOOK,
                    data=data,
                    files=files
                )

        return f"""
        <html>

        <body style="font-family: Arial; padding: 40px;">

            <h1>Blog Generated Successfully!</h1>

            <p><strong>Title:</strong> {title}</p>

            <a href="/">Go Back</a>

        </body>

        </html>
        """

    except Exception as e:

        logging.error(str(e))

        return f"""
        <html>

        <body style="font-family: Arial; padding: 40px;">

            <h1>Error</h1>

            <p>{str(e)}</p>

            <a href="/">Go Back</a>

        </body>

        </html>
        """

# =========================
# TEST ROUTE
# =========================

@app.get("/test")
async def test():
    return {"message": "Server is running!"}