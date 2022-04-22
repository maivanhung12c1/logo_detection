# MongoDB with Tornado
This is a simple project that build an API to upload and download image with MongoDB and Tornado.
## Run app
### Run app normally
Install requirements: pip install -r requirements.txt
Off line "client = pymongo.MongoClient(username=user, password=passw, host=host)" in app.py
On line "client = pymongo.MongoClient()" in app.py
Start service: python app.py
Now you can load http://localhost:9999 in your browser
### Up docker compose and Run app
Up docker compose: docker-compose up -d
Now you can load http://localhost:8080 in your browser
