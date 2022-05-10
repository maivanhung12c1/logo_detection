from dataclasses import replace
import tornado.web
import tornado.ioloop
import tornado.template
import pymongo
from bson.objectid import ObjectId
import base64
import uuid
import yolov5.detect as detect
import detection.logo_detection as logo_detection
import os

class MainHandler(tornado.web.RequestHandler):

    def encode_img_data(self, img_path):
        with open(img_path, "rb") as imageFile:
            encoded_img = base64.b64encode(imageFile.read())
        return encoded_img

    def get_template_namespace(self):
        # Set defautl argument for template
        ns = super(MainHandler, self).get_template_namespace()
        default_img = self.encode_img_data("images/original/vnflag.png")
        ns.update({
            "img_path": "images/original/vnflag.png",
            "img_base64": default_img,
            "detected_img64": default_img,
            "alert":""
        })
        return ns

    async def find_image_data(self, image_uuid=None, id_image=None):
        if image_uuid is not None:
            return self.settings["db"]["images"].find_one({"image-uuid": image_uuid})
        elif id_image is not None:
            return self.settings["db"]["images"].find_one({"_id": id_image})
        elif (image_uuid is None) and (id_image is None):
            return self.settings["db"]["images"].find_one()

    async def insert_image_data(self, img):
        return self.settings["db"]["images"].insert_one(img)

    async def get(self, image_uuid=None):
        # If image_uuid isn't presented, default image will be present
        if image_uuid is not None:
            image = await self.find_image_data(image_uuid=image_uuid)
            if image is not None:
                encoded_img = self.encode_img_data(image["image-path"])
                encoded_dt_img = self.encode_img_data(image["detected-img-path"])
                return self.render("templates/home.html", img_base64=encoded_img, uuid=image["image-uuid"], detected_img64=encoded_dt_img)
            else:
                raise tornado.web.HTTPError(404)
        else:
            image = await self.find_image_data()
            img = image["image-path"]
            encoded_img = self.encode_img_data(img)
            return self.render("templates/home.html", img_base64=encoded_img, uuid=image["image-uuid"])

    async def detect_logo(self, encoded_img, source, name):
        detection = logo_detection.LogoDetection(encoded_img, source=source, name=name)
        result = detection.run()
        return result

    async def post(self):
        # Get uploaded file
        img_file = self.request.files['image'][0]
        # Create path to save original image
        fname = img_file['filename']
        store_location = "images/original/"
        fname = fname.split(".")
        if fname[1].lower()=="png" or fname[1].lower()=="jpg":
            image_uuid = str(uuid.uuid4().hex)
            file_name = fname[0] + image_uuid[0:5] + "." + fname[1]
            image_path = store_location + file_name

            # Create path to save original image
            dt_img_path = image_path.replace("original", "detected")

            # Write image to file
            output_file = open(image_path, 'wb')
            output_file.write(img_file['body'])

            # Create data 
            image = {"image-uuid":image_uuid,"image-path":image_path, "detected-img-path":dt_img_path}
            image["_id"] = str(ObjectId())
            new_image = await self.insert_image_data(image)
            uploaded_image = await self.find_image_data(id_image=new_image.inserted_id)
            img_view = self.encode_img_data(uploaded_image["image-path"])

            # Detect logo in image
            #detect.run(weights="best.pt", project="images/detected/", source=image_path, name='')
            res = await self.detect_logo(img_view, source="images/detected/", name=file_name)
            print("detected result: ",res)
            detected_img = self.encode_img_data(uploaded_image["detected-img-path"])
            return self.render("templates/home.html", img_base64=img_view, uuid=image_uuid, detected_img64=detected_img)
        else:
            alert = "You are only allowed to upload jpg or png file"
            return self.render("templates/home.html", alert=alert,img_base64="", uuid="")

def initialize_database(user="mvh", passw="123", host="img_data", default_mongoclient=True):
    if default_mongoclient==False:
        client = pymongo.MongoClient(username=user, password=passw, host=host)
        #client = pymongo.MongoClient(os.environ)
    #client = pymongo.MongoClient()
    db = client["mydata"]
    images = db["images"]
    num_record = list(images.find())
    if len(num_record) == 0:
        vn_uuid = uuid.uuid4().hex
        vn_img = {"image-uuid": vn_uuid, "image-path": "images/original/vnflag.png", "detected-img-path":""}
        vn_img["_id"] = str(ObjectId())
        images.insert_one(vn_img)
    return db


def main():
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/(\w+)", MainHandler),
    ],
    db=db,)
    port = 8080
    app.listen(port)
    print("Running")
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    db = initialize_database(default_mongoclient=False)
    main()