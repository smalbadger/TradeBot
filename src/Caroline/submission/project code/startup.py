from os import system as sys

sys("sudo service mongod start")

while True:
    sys("python3 DataRetriever.py")
