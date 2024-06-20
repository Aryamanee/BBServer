# Final Project Server - main.py
# Aryaman Sawhney
# Interacts with the client to create a user experience

# import neccessary libraries
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from fastapi import FastAPI, APIRouter, responses, UploadFile
import os
import random


# Server class
class Server:

    # init method
    def __init__(self):
        # load all data files
        self.listings = pd.read_pickle("listings.pkl")
        self.accounts = pd.read_pickle("accounts.pkl")
        self.chats = pd.read_pickle("chats.pkl")
        # initialize a tfidf vectorizer with the english stop words so that we dont make desicions based on words such as and and at and words that are just grammatical and dont have any other meaning
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english")
        # fill all of the empty descriptions as blank
        self.listings["desc"] = self.listings["desc"].fillna("")
        # make a tfidf matrix using the descriptions
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.listings["desc"])
        # calculate cosine similarities between different descriptions
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
        # create the api router in order to route fastapi reqeusts to our functions
        self.router = APIRouter()
        # add all of the functions as api routes for the client to use
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
        self.router.add_api_route("/get_chats", self.get_chats, methods=["GET"])

    # new account function
    def new_account(self, name: str, username: str, password: str):
        # return false if empty info provided
        if (
            name == ""
            or name.isspace()
            or username == ""
            or username.isspace()
            or password == ""
            or password.isspace()
        ):
            return {"successful": False}
        # try to see if the username already exists, if so return false otherwise add the row and return true
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
                0,
            ]
            self.accounts.to_pickle("accounts.pkl")
            return {"successful": True}

        else:
            return {"successful": False}

    # get account function
    def get_account(self, uid: int):
        # find the row of the uid and return the info which is non confidential, if the user is not found return a 404
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

    # get account by username function
    def get_account_by_username(self, username: str):
        # try to find the row where username is the provided username and return its uid, if not found return 404
        try:
            return self.get_account(
                int(self.accounts[self.accounts["username"] == username]["UID"])
            )
        except TypeError:
            return responses.Response(status_code=404)

    # try to get the pfp and otherwise return a 404
    def get_pfp(self, uid: int):
        if os.path.exists("pfp/" + str(uid) + ".png"):
            return responses.FileResponse("pfp/" + str(uid) + ".png")
        else:
            return responses.Response(status_code=404)

    # try to get the listing photo and return 404 if not found
    def get_listing_photo(self, id: int):
        if os.path.exists("listing_photos/" + str(id) + ".png"):
            return responses.FileResponse("listing_photos/" + str(id) + ".png")
        else:
            return responses.Response(status_code=404)

    # work only if the uid already exists, if so write to the pfp file for that account
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

    # work only if the id already exists, if so write to the listing  photo file for that listing
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

    # validate the username and password, also specifying whats wrong
    def login(self, username: str, password: str):
        if len(self.accounts[self.accounts["username"] == username].index) == 0:
            return {"username": False, "password": False}
        else:
            pw = self.accounts[self.accounts["username"] == username]["password"].iloc[
                0
            ]
            return {"username": True, "password": pw == password}

    # return the id of the new listing after creating it, the id is none if there are errors
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

    # get listing function - try to get the listing of a certain id, if you find it send the info otherwise return a 404
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

    # get all the listings of an id
    def get_listings(self, uid: int):
        listings = {}
        # find all the listigns that belong to the id
        matches = self.listings[self.listings["UID"] == uid]
        n = 0
        # loop over the matches anda add them all to a dict then return it all
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

    # get next listing function
    def get_next_listing(self, uid: int):
        # add one to the users remove counter - this is useful in accomodating changes in interest
        self.accounts.iloc[uid]["remove_counter"] += 1
        # try to find the users history, if not found return a 404
        try:
            history = self.accounts[self.accounts["UID"] == uid].iloc[0]["history"]
        except IndexError:
            return responses.Response(status_code=400)
        # if the history has more than ten items we can start giving targetted prefs
        if len(history) > 10:
            # 1 in 5 chance of giving a random listing so we can see the changes in interest that occur
            randomornot = random.randint(1, 5)
            if randomornot == 5:
                ID = random.randint(0, len(self.listings.index) - 1)
                return self.get_listing(ID)
            # turn the history into a list of lists containing the first value as the listing id and the second value as the time stopped at that listing
            history = list(map(list, history.items()))
            # sort the history to have the longest ones at the top
            history.sort(key=lambda x: x[1], reverse=True)
            # select one of the top 10 listings to base our suggestion off of
            selection_index = random.randint(0, 9)
            # get the id of the random selection
            id = history[selection_index][0]
            # enumrate over all of the similarities to our current selection
            sim_nums = enumerate(self.cosine_sim[id])
            # make a list of all of the similaritied except the first as the first is literally just our listing
            sim_nums = list(sim_nums)[1::]
            # order all of the nums in order of most similar to least
            sim_nums.sort(key=lambda x: x[1], reverse=True)
            # get a random number to chose one of the top 10 matches
            sim_index = random.randint(0, 9)
            # if we exceeded the remvoe counter-remove the top listing this lets things slowly change in terms of prefs
            if self.accounts.iloc[uid]["remove_counter"] >= 3:
                self.accounts.iloc[uid]["remove_counter"] = 0
                del self.accounts[self.accounts["UID"] == uid].iloc[0]["history"][
                    history[-1][0]
                ]
                self.accounts.to_pickle("accounts.pkl")

            # return the info of the selected listing
            return self.get_listing(sim_nums[sim_index][0])
        # if we dont have enough for a recomendation, give something random
        else:
            ID = random.randint(0, len(self.listings.index) - 1)
            return self.get_listing(ID)

    # set view duration function - this helps the server learn about the user
    def set_view_duration(self, uid: int, id: int, duration: float):
        # try to find the account, if found set the duration of viewing that listing to the given time otherwise return a 404
        try:
            account = self.accounts[self.accounts["UID"] == uid].iloc[0]
        except IndexError:
            return responses.Response(status_code=404)
        account["history"][id] = duration
        self.accounts.to_pickle("accounts.pkl")
        return responses.Response(status_code=200)

    # add to basket function
    def add_to_basket(self, uid: int, id: int):
        # try finding the given account,return a 404 if not found
        try:
            account = self.accounts[self.accounts["UID"] == uid].iloc[0]
        except IndexError:
            return responses.Response(status_code=404)

        # if the item is not in the basket already return a 200 otherwise return a 400
        if id not in account["basket"]:
            account["basket"].append(id)
            self.accounts.to_pickle("accounts.pkl")
            return responses.Response(status_code=200)
        else:
            return responses.Response(status_code=400)

    # remove from basket function
    def remove_from_basket(self, uid: int, id: int):
        # try finding the given account,return a 404 if not found
        try:
            account = self.accounts[self.accounts["UID"] == uid].iloc[0]
        except IndexError:
            return responses.Response(status_code=400)

        # try removing it and return a 400 if the item is not in the basket
        if id in account["basket"]:
            account["basket"].remove(id)
            self.accounts.to_pickle("accounts.pkl")
            return responses.Response(status_code=200)
        else:
            return responses.Response(status_code=400)

    # get the basket of a certain user
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

    # get a chat between two parties
    def get_chat(self, P1: int, P2: int):
        matches = self.chats[
            self.chats["name"] == str(min(P1, P2)) + "&" + str(max(P1, P2))
        ]
        if len(matches) == 0:
            return {"chat": None}
        else:
            return {"chat": matches.iloc[0]["msgs"]}

    def get_chats(self, uid: int):
        matches = self.chats[(self.chats["P1"] == uid) | (self.chats["P2"] == uid)]
        chats = []
        for index, match in matches.iterrows():
            if match["P1"] == uid:
                chats.append(self.get_account(match["P2"]))
            else:
                chats.append(self.get_account(match["P1"]))
        return {"chats": chats}

    # create a chat between two parties
    def create_chat(self, P1: int, P2: int):
        if self.get_chat(P1, P2)["chat"] != None:
            return responses.Response(status_code=400)
        new_row = [
            str(min(P1, P2)) + "&" + str(max(P1, P2)),
            min(P1, P2),
            max(P1, P2),
            list(),
        ]
        self.chats.loc[len(self.chats.index)] = new_row
        self.chats.to_pickle("chats.pkl")
        return responses.Response(status_code=200)

    # write a message from one party to the other
    def write_message(self, uid: int, to: int, content: str):
        matches = self.chats[
            self.chats["name"] == str(min(uid, to)) + "&" + str(max(uid, to))
        ]
        if len(matches) == 0:
            return responses.Response(status_code=400)
        else:
            matches.iloc[0]["msgs"].append((content, uid > to))
            self.chats.to_pickle("chats.pkl")
            return responses.Response(status_code=200)


# start the fastapi app, add the server and finally include the router from the server

app = FastAPI()
server = Server()
app.include_router(server.router)
