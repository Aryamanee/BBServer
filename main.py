import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from fastapi import FastAPI, APIRouter, responses, UploadFile
import os
import random


class Server:

    def __init__(self):
        self.remove_counter = 0
        self.listings = pd.read_pickle("listings.pkl")
        self.accounts = pd.read_pickle("accounts.pkl")
        self.chats = pd.read_pickle("chats.pkl")
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english")
        self.listings["desc"] = self.listings["desc"].fillna("")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.listings["desc"])
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
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
        self.router.add_api_route("/new_listing", self.new_listing, methods=["GET"])
        self.router.add_api_route("/get_listing", self.get_listing, methods=["GET"])
        self.router.add_api_route("/get_listings", self.get_listings, methods=["GET"])
        self.router.add_api_route(
            "/get_next_listing", self.get_next_listing, methods=["GET"]
        )
        self.router.add_api_route(
            "/set_view_duration", self.set_view_duration, methods=["POST"]
        )
        self.router.add_api_route("/add_to_basket", self.add_to_basket, methods=["GET"])
        self.router.add_api_route(
            "/remove_from_basket", self.remove_from_basket, methods=["GET"]
        )
        self.router.add_api_route("/get_basket", self.get_basket, methods=["GET"])
        self.router.add_api_route("/get_chat", self.get_chat, methods=["GET"])
        self.router.add_api_route("/create_chat", self.create_chat, methods=["GET"])
        self.router.add_api_route("/write_message", self.write_message, methods=["GET"])

    def new_account(self, name: str, username: str, password: str):
        if (
            name == ""
            or name.isspace()
            or username == ""
            or username.isspace()
            or password == ""
            or password.isspace()
        ):
            return {"successful": False}
        try:
            count = self.accounts["username"].value_counts()[username]
        except KeyError:
            self.accounts.loc[len(self.accounts.index)] = [
                len(self.accounts.index),
                name,
                username,
                password,
                {},
                [],
            ]
            self.accounts.to_pickle("accounts.pkl")
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
            return responses.Response(status_code=400)
        else:
            file = open("pfp/" + str(uid) + ".png", "wb")
            file.write(pfp.file.read())
            pfp.close()
            file.close()

    def set_listing_photo(self, id: int, listing_photo: UploadFile):
        try:
            self.accounts.iloc[id]
        except IndexError:
            return responses.Response(status_code=400)
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

    def new_listing(self, name: str, desc: str, uid: int, price: int):
        if name == "" or name.isspace() or desc == "" or desc.isspace():
            return {"ID": None}
        id = len(self.listings.index)
        self.listings.loc[id] = [
            len(self.listings.index),
            name,
            desc,
            uid,
            price,
        ]
        print(os.getcwd())
        self.listings.to_pickle("listings.pkl")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.listings["desc"])
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
        return {"ID": id}

    def get_listing(self, id: int):
        try:
            listing = dict(self.listings.iloc[id])
        except IndexError:
            return responses.Response(status_code=404)
        else:
            return {
                "ID": int(listing["ID"]),
                "name": listing["name"],
                "desc": listing["desc"],
                "UID": int(listing["UID"]),
                "price": int(listing["price"]),
            }

    def get_listings(self, uid: int):
        listings = {}
        matches = self.listings[self.listings["UID"] == uid]
        n = 0
        for index, row in matches.iterrows():
            listings[n] = {
                "ID": int(row["ID"]),
                "name": row["name"],
                "desc": row["desc"],
                "UID": int(row["UID"]),
                "price": int(row["price"]),
            }
            n += 1
        return listings

    def get_next_listing(self, uid: int):
        self.remove_counter += 1
        try:
            history = self.accounts[self.accounts["UID"] == uid].iloc[0]["history"]
        except IndexError:
            return responses.Response(status_code=400)
        if len(history) > 10:
            randomornot = random.randint(1, 5)
            if randomornot == 5:
                ID = random.randint(0, len(self.listings.index) - 1)
                return self.get_listing(ID)
            history = list(map(list, history.items()))
            history.sort(key=lambda x: x[1], reverse=True)
            selection_index = random.randint(0, 9)
            id = history[selection_index][0]
            sim_nums = enumerate(self.cosine_sim[id])
            sim_nums = list(sim_nums)[1::]
            sim_nums.sort(key=lambda x: x[1], reverse=True)
            sim_index = random.randint(0, 9)
            if self.remove_counter >= 3:
                self.remove_counter = 0
                del self.accounts[self.accounts["UID"] == uid].iloc[0]["history"][
                    history[-1][0]
                ]
                self.accounts.to_pickle("accounts.pkl")

            return self.get_listing(sim_nums[sim_index][0])
        else:
            ID = random.randint(0, len(self.listings.index) - 1)
            return self.get_listing(ID)

    def set_view_duration(self, uid: int, id: int, duration: float):
        try:
            account = self.accounts[self.accounts["UID"] == uid].iloc[0]
        except IndexError:
            return responses.Response(status_code=400)
        account["history"][id] = duration
        self.accounts.to_pickle("accounts.pkl")
        return responses.Response(status_code=200)

    def add_to_basket(self, uid: int, id: int):
        try:
            account = self.accounts[self.accounts["UID"] == uid].iloc[0]
        except IndexError:
            return responses.Response(status_code=400)

        if id not in account["basket"]:
            account["basket"].append(id)
            self.accounts.to_pickle("accounts.pkl")
            return responses.Response(status_code=200)
        else:
            return responses.Response(status_code=400)

    def remove_from_basket(self, uid: int, id: int):
        try:
            account = self.accounts[self.accounts["UID"] == uid].iloc[0]
        except IndexError:
            return responses.Response(status_code=400)

        if id in account["basket"]:
            account["basket"].remove(id)
            self.accounts.to_pickle("accounts.pkl")
            return responses.Response(status_code=200)
        else:
            return responses.Response(status_code=400)

    def get_basket(self, uid: int):
        try:
            account = self.accounts[self.accounts["UID"] == uid].iloc[0]
        except IndexError:
            return responses.Response(status_code=400)

        basket = account["basket"]
        dict_basket = {}
        for i in range(len(basket)):
            dict_basket[i] = self.get_listing(basket[i])

        return dict_basket

    def get_chat(self, P1: int, P2: int):
        matches = self.chats[
            self.chats["name"] == str(min(P1, P2)) + "&" + str(max(P1, P2))
        ]
        if len(matches) == 0:
            return {"matches": None}
        else:
            return {"matches": matches[0]["msgs"]}

    def create_chat(self, P1: int, P2: int):
        if self.get_chat(P1, P2)["matches"] == None:
            return responses.Response(status_code=400)
        new_row = [
            str(min(P1, P2)) + "&" + str(max(P1, P2)),
            min(P1, P2),
            max(P1, P2),
            list(),
        ]
        self.chats.iloc[self.chats.index] = new_row
        self.chats.to_pickle("chats.pkl")
        return responses.Response(status_code=200)

    def write_message(self, uid: int, to: int, content: str):
        matches = self.chats[
            self.chats["name"] == str(min(uid, to)) + "&" + str(max(uid, to))
        ]
        if len(matches) == 0:
            return responses.Response(status_code=400)
        else:
            matches[0]["msgs"].append((content, uid > to))
            return responses.Response(status_code=200)


app = FastAPI()
server = Server()
app.include_router(server.router)
