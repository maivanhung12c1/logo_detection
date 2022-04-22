import tornado.web
import tornado.ioloop
import tornado.template
import pymongo
from bson.objectid import ObjectId
import base64
import uuid

user = "mvh"
passw = "123"
host = "img_data"
#client = pymongo.MongoClient(username=user, password=passw, host=host)
client = pymongo.MongoClient()
db = client["mydata"]
images = db["images"]

num_record = list(images.find())
if len(num_record) == 0:
    vn_uuid = uuid.uuid4().hex
    vn_img = {"image-uuid": vn_uuid, "image-path": "images/vnflag.png"}
    vn_img["_id"] = str(ObjectId())
    images.insert_one(vn_img)


class MainHandler(tornado.web.RequestHandler):

    def encode_img(self, img_path):
        with open(img_path, "rb") as imageFile:
            str_data = base64.b64encode(imageFile.read())
        return str_data

    def get_template_namespace(self):
        ns = super(MainHandler, self).get_template_namespace()
        default_img = self.encode_img("images/vnflag.png")
        ns.update({
            "img_path": "images/vnflag.png",
            "img_base64": default_img,
        })
        return ns

    async def find_image(self, image_uuid=None, id_image=None):
        if image_uuid is not None:
            return self.settings["db"]["images"].find_one({"image-uuid": image_uuid})
        elif id_image is not None:
            return self.settings["db"]["images"].find_one({"_id": id_image})
        elif (image_uuid is None) and (id_image is None):
            return self.settings["db"]["images"].find_one()

    async def insert_image(self, img):
        return self.settings["db"]["images"].insert_one(img)

    async def get(self, image_uuid=None):
        
        if image_uuid is not None:
            image = await self.find_image(image_uuid=image_uuid)
            if image is not None:
                img = image["image-path"]
                encoded_img = self.encode_img(img)
                return self.render("templates/home.html", img_base64=encoded_img, uuid=image["image-uuid"])
            else:
                raise tornado.web.HTTPError(404)
        else:
            image = await self.find_image()
            img = image["image-path"]
            encoded_img = self.encode_img(img)
            return self.render("templates/home.html", img_base64=encoded_img, uuid=image["image-uuid"])

    async def post(self):
        img_file = self.request.files['image'][0]
        fname = img_file['filename']
        store_location = "images/"
        fname = fname.split(".")
        image_uuid = str(uuid.uuid4().hex)
        path_image = store_location + fname[0] + image_uuid[0:5] + "." + fname[1]

        output_file = open(path_image, 'wb')
        output_file.write(img_file['body'])

        image = {"image-uuid":image_uuid,"image-path":path_image}
        image["_id"] = str(ObjectId())
        new_image = await self.insert_image(image)
        uploaded_image = await self.find_image(id_image=new_image.inserted_id)
        img_view = self.encode_img(uploaded_image["image-path"])
        return self.render("templates/home.html", img_base64=img_view, uuid=image_uuid)


def main():
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/(\w+)", MainHandler),
    ],
    db=db,)
    port = 9999
    app.listen(port)
    print("Running")
    for x in images.find():
        print(x["image-uuid"])
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()