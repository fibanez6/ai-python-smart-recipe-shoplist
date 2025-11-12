from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Smart Recipe Shoplist",
    description="AI Agent for recipe and shopping list management",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Smart Recipe Shoplist API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)