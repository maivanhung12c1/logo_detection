import yolov5
import base64
import cv2
import numpy as np
import torch
import json
import torch.backends.cudnn as cudnn
from yolov5.utils.augmentations import letterbox

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import (LOGGER, check_img_size, cv2,
                            non_max_suppression, scale_coords,  xyxy2xywh)

from yolov5.utils.plots import Annotator, colors
from yolov5.utils.torch_utils import select_device, time_sync

class LogoDetection:
    def __init__(self,img, name, source):
        self.img = self.decode_base64img(img)
        self.file_name = name
        self.source = source

    def decode_base64img(self, base64img):
        im = base64.b64decode(base64img)
        im = np.fromstring(im, np.uint8)
        decoded_im = cv2.imdecode(im, cv2.IMREAD_ANYCOLOR)
        return decoded_im

    def run(self, weights="weights/best.pt", project="images/detected/", imgsz = (640, 640)):
        detect_list = []
        # Load model
        device = select_device('')
        model = DetectMultiBackend(weights, device=device)
        stride, names, pt = model.stride, model.names, model.pt
        imgsz = check_img_size(imgsz, s=stride)
        model.warmup(imgsz=(1 , 3, *imgsz))
        dt, seen = [0.0, 0.0, 0.0], 0
        print("shape: ",self.img.shape)
        # Padded resize
        im = letterbox(self.img, imgsz, stride=stride, auto=pt)[0]
        im0 = self.img.copy()
        # Convert
        im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        im= np.ascontiguousarray(im)
        t1 = time_sync()
        im = torch.from_numpy(im).to(device)
        #im = im.to(device)
        im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        t2 = time_sync()
        dt[0] += t2 - t1

        # Inference
        pred = model(im, augment=False, visualize=False)
        t3 = time_sync()
        dt[1] += t3 - t2

        # NMS
        agnostic_nms = False
        pred = non_max_suppression(pred)
        dt[2] += time_sync() - t3

        for i, det in enumerate(pred):  # per image
            seen += 1
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
            annotator = Annotator(im0, line_width=3, example=str(names))
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(im.shape[2:], det[:, :4], self.img.shape).round()

                # Print results
                for *xyxy, conf, cls in reversed(det):
                    c = int(cls)
                    label = f'{names[c]} {conf:.2f}'
                    detect_result_per_one = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()
                    detect_result_per_one.insert(0, names[c])
                    detect_result_per_one.insert(1, float(conf))
                    detect_list.append(detect_result_per_one)
                    annotator.box_label(xyxy, label, color=colors(c, True))
                    
        im0 = annotator.result()
        cv2.imwrite(str(self.source + self.file_name), im0)
        t = tuple(x / seen * 1E3 for x in dt)  # speeds per image
        sum_t = sum(t)
        LOGGER.info(sum_t)
        LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
        result = self.convert_to_json_obj(detect_list, sum_t)
        return result

    def convert_to_json_obj(self, detected_result: list, time):
        dic = {}
        logo_list = []
        dic["elapse-time"] = time
        for logo in detected_result:
            info = {}
            info["logo-name"] = logo[0]
            info["bounding-box"] = logo[2:]
            info["confidence"] = logo[1]
            logo_list.append(info)
        dic["list-of-logos"] = logo_list
        result = json.dumps(dic, indent=4)
        return result



