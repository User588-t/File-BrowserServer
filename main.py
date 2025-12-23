from fastapi import FastAPI

app = FastAPI()

@app.post("/test")
async def TestFunc():
    return ...
