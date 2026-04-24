from fastapi import FastAPI

app = FastAPI(title="QA TC Agent")

@app.get("/")
def read_root():
    return {"message": "QA TC Agent is running"}

@app.get("/health")
def health():
    return {"status": "ok"}