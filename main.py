import pandas as pd
import numpy as np
from fastapi import FastAPI, APIRouter


class Server:

    def __init__(self):
        self.listings = pd.read_csv("listings.csv")
        self.accounts = pd.read_csv("accounts.csv")
        self.router = APIRouter()
        self.router.add_api_route(
            "/new-account/{name}/{username}/{password}",
            self.new_account,
            methods=["GET"],
        )

    def new_account(self, name: str, username: str, password: str):
        try:
            count = self.accounts["username"].value_counts()[username]
        except KeyError:
            self.accounts.loc[len(self.accounts.index)] = [
                len(self.accounts.index),
                name,
                username,
                password,
            ]
            self.accounts.to_csv("accounts.csv", index=False)
            return {"successful": True}

        else:
            return {"successful": False}

    # def get_account


app = FastAPI()
server = Server()
app.include_router(server.router)
