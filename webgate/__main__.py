import uvicorn

uvicorn.run("webgate:app", host="0.0.0.0", reload=True)
