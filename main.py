from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, filename='logs/fastapi.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()
logging.info("FastAPI application has started.")

class BlogRequest(BaseModel):
    topic: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Blog Generator!"}

@app.post("/generate-blog/")
async def generate_blog(request: BlogRequest):
    logging.info(f"Received request to generate blog for topic: {request.topic}")
    
    # Call OpenAI API to generate blog content
    openai_api_key = os.getenv("OPENAI_API_KEY")
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "prompt": f"Write a blog post about {request.topic}",
        "max_tokens": 500
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.openai.com/v1/completions", headers=headers, json=data)
        if response.status_code != 200:
            logging.error(f"Error generating blog post: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error generating blog post")
        
        blog_content = response.json()["choices"][0]["text"]
        
        # Send to Discord
        html_file_path = f"{request.topic}.html"
        with open(html_file_path, "w") as f:
            f.write(blog_content)
        async with httpx.AsyncClient() as discord_client:
            with open(html_file_path, "rb") as f:
                await discord_client.post(discord_webhook_url, files={"file": (html_file_path, f)})
        
        return {"title": request.topic, "content": blog_content}