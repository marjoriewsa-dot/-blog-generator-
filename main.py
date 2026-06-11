from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Blog Generator!"}

# Add your blog generation endpoints here