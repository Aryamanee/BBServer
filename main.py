import pandas as pd
import numpy as np
from fastapi import FastAPI, APIRouter, responses, UploadFile
import os


class Server:

    def __init__(self):
        self.listings = pd.read_csv("listings.csv")
        self.accounts = pd.read_csv("accounts.csv")
        self.router = APIRouter()
        self.router.add_api_route(
            "/new_account",
            self.new_account,
            methods=["GET"],
        )
        self.router.add_api_route("/get_account", self.get_account, methods=["GET"])
        self.router.add_api_route(
            "/get_account_by_username", self.get_account_by_username, methods=["GET"]
        )
        self.router.add_api_route("/get_pfp", self.get_pfp, methods=["GET"])
        self.router.add_api_route(
            "/get_listing_photo", self.get_listing_photo, methods=["GET"]
        )
        self.router.add_api_route("/set_pfp", self.set_pfp, methods=["PUT"])
        self.router.add_api_route(
            "/set_listing_photo", self.set_listing_photo, methods=["PUT"]
        )
        self.router.add_api_route("/login", self.login, methods=["GET"])

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

    def get_account(self, uid: int):
        try:
            account = dict(self.accounts.iloc[uid])
        except IndexError:
            return responses.Response(status_code=404)
        else:
            return {
                "UID": int(account["UID"]),
                "name": account["name"],
                "username": account["username"],
            }

    def get_account_by_username(self, username: str):
        try:
            return self.get_account(
                int(self.accounts[self.accounts["username"] == username]["UID"])
            )
        except TypeError:
            return responses.Response(status_code=404)

    def get_pfp(self, uid: int):
        if os.path.exists("pfp/" + str(uid) + ".png"):
            return responses.FileResponse("pfp/" + str(uid) + ".png")
        else:
            return responses.Response(status_code=404)

    def get_listing_photo(self, id: int):
        if os.path.exists("listing_photos/" + str(id) + ".png"):
            return responses.FileResponse("listing_photos/" + str(id) + ".png")
        else:
            return responses.Response(status_code=404)

    def set_pfp(self, uid: int, pfp: UploadFile):
        try:
            self.accounts.iloc[uid]
        except IndexError:
            return responses.Response(status_code=422)
        else:
            file = open("pfp/" + str(uid) + ".png", "wb")
            file.write(pfp.file.read())
            pfp.close()
            file.close()

    def set_listing_photo(self, id: int, listing_photo: UploadFile):
        try:
            self.accounts.iloc[id]
        except IndexError:
            return responses.Response(status_code=422)
        else:
            file = open("listing_photos/" + str(id) + ".png", "wb")
            file.write(listing_photo.file.read())
            listing_photo.close()
            file.close()

    def login(self, username: str, password: str):
        if len(self.accounts[self.accounts["username"] == username].index) == 0:
            return {"username": False, "password": False}
        else:
            pw = self.accounts[self.accounts["username"] == username]["password"].iloc[
                0
            ]
            return {"username": True, "password": pw == password}


app = FastAPI()
server = Server()
app.include_router(server.router)
