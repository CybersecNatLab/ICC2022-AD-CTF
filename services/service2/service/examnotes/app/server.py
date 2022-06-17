import auth
from hashlib import sha256
import os
import json

base_path = "data"

def write_note(foldername):
    try:
        if len(os.listdir(os.path.join(base_path, foldername))) >= 10:
            print("You reached the maximum number of notes for this account")
            return
    except FileNotFoundError:
        os.makedirs(os.path.join(base_path, foldername))

    title = input("Title of the note: ")

    if len(title) > 20:
        print("Title is too long")
        return

    content = input("Content of the note: ")

    if len(content) > 100:
        print("Content is too long")
        return

    note = json.dumps({"title":title, "content":content})

    try:
        note_number = str(len(os.listdir(os.path.join(base_path, foldername))))
        with open(os.path.join(base_path, foldername, note_number), "x") as f:
            f.write(note)
        print("Note added!")
    except FileExistsError:
        print("Apparently you already wrote this note...")

def list_notes(foldername):
    try:
        assert len(os.listdir(os.path.join(base_path, foldername))) > 0
        for f in os.listdir(os.path.join(base_path, foldername)):
            title = json.loads(open(os.path.join(base_path, foldername, f), "r").read().strip())["title"]
            print(f"Id: {f}, Title: {title}")
    except FileNotFoundError:
        print("It seems that you don't have any note")

def read_note_by_id(foldername):
    id = input("Enter your note id: ")
    try:
        with open(os.path.join(base_path, foldername, id), "r") as f:
            note = json.loads(f.read().strip())
            print(f"Title: {note['title']}")
            print(f"Content: {note['content']}")
    except FileNotFoundError:
        print("You must write a note before reading it!")
    except Exception as e:
        print(e)

print("Welcome to ExamNotes!")
token = input("Enter your login token: ")

username = auth.handle_token(token)

print()

if username is None:
    print("Authentication failed")
    exit(1)

print(f"Successfully authenticated as {username.decode()}")
print()

print("Welcome to ExamNotes 1.0!")
print("Here you can store the notes for your cyber-university courses to read them later.")

while True:
    print("What do you want to do?")
    print("1. Add a new note")
    print("2. List my notes")
    print("3. Read a note by id")
    print("0. Exit")

    foldername = sha256(username).hexdigest()

    try:
        ch = int(input())
        assert ch in [1,2,3]

        if ch == 1:
            write_note(foldername)
        elif ch == 2:
            list_notes(foldername)
        else:
            read_note_by_id(foldername)
    except:
        exit(1)
