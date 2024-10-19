from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.lib.mint import Mint


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def main():
    return Mint().show()
