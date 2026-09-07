from fastapi import FastAPI

app = FastAPI(title='Helpdesk Bottleneck Analyzer')

@app.get("/")
def root():
    return{"starus": "ok","message": "Project is running"}