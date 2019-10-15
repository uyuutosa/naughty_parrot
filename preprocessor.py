import boto3
import s3fs
import io
import pandas as pd
import itertools
import copy as cp
import PIL.Image as I
from numpy import *
from naughty_parrot.calculation_recorder import CalculationRecorder
from naughty_parrot.encoder_decoder import *

class Preprocessor:
    def __init__(self, path, x_calc_rec=None, y_calc_rec=None):
        self.support_format_lst = ['jpg', 'png', 'bmp']
        self.img_ed = ImageEncoderDecoder()
        self.csv_ed = CSVEncoderDecoder()
        if isinstance(path, str) and not path.split('.')[-1] in self.support_format_lst:
            self.img = self.img_ed.decode(path)
        elif isinstance(path, str):
            if  's3://' in path:
                s3 = s3fs.S3FileSystem()
                with s3.open(path.replace('s3://', '')) as f:
                    self.img = I.open(io.BytesIO(f.read())).convert('RGB')
            else:
                self.img = I.open(path).convert('RGB')
        elif isinstance(path, io.BytesIO):
            self.img = I.open(path)
        else:
            self.img = path
        self.path = path
        self.x_calc_rec = CalculationRecorder() if x_calc_rec is None else x_calc_rec
        self.y_calc_rec = CalculationRecorder() if y_calc_rec is None else y_calc_rec

    def correctExif(self):
        
        convert_image = {
            1: lambda img: img,
            2: lambda img: img.transpose(I.FLIP_LEFT_RIGHT),
            3: lambda img: img.transpose(I.ROTATE_180),
            4: lambda img: img.transpose(I.FLIP_TOP_BOTTOM),
            5: lambda img: img.transpose(I.FLIP_LEFT_RIGHT).transpose(Pillow.ROTATE_90),
            6: lambda img: img.transpose(I.ROTATE_270),
            7: lambda img: img.transpose(I.FLIP_LEFT_RIGHT).transpose(Pillow.ROTATE_270),
            8: lambda img: img.transpose(I.ROTATE_90),
        }
        
        img = self.img
        if '_getexif' in dir(img):
            exif = img._getexif()
            if 'exif' in dir(exif):
                orientation = exif.get(0x112, 1)
                img = convert_image[orientation](img)
        return Preprocessor(img.copy(),
                            x_calc_rec=cp.deepcopy(self.x_calc_rec), 
                            y_calc_rec=cp.deepcopy(self.y_calc_rec))

    def _getHumanArea(self, img):
        img_bin = io.BytesIO()
        img.save(img_bin, format='JPEG')
        endpointName = 'bodygram-pose-estimator-endpoint'

        # Talk to SageMaker
        client = boto3.client('sagemaker-runtime', region_name='ap-northeast-1')
        response = client.invoke_endpoint(
            EndpointName=endpointName,
            Body=img_bin.getvalue(),
            ContentType='image/jpeg',
            Accept='Accept'
        )

        return self.csv_ed.decode(response['Body'].read())
        #return pd.read_csv(io.BytesIO(response['Body'].read()), header=0, index_col=0)

    def centerCrop(self, x=None, y=None):
        w, h = self.img.size
        img = self.img.crop((w // 2 - x // 2,
                             h // 2 - y // 2,
                             w // 2 + x // 2,
                             h // 2 + y // 2))

        x_calc_rec =  self.x_calc_rec - (w // 2 - x // 2)
        y_calc_rec =  self.y_calc_rec - (h // 2 - y // 2)
        return Preprocessor(img.copy(),
                            x_calc_rec=cp.deepcopy(x_calc_rec),
                            y_calc_rec=cp.deepcopy(y_calc_rec))

    def crop(self, xmin, ymin, xmax, ymax):
        x_calc_rec = self.x_calc_rec - xmin
        y_calc_rec = self.y_calc_rec - ymin
        img = self.img.crop((xmin, 
                             ymin, 
                             xmax, 
                             ymax))

        return Preprocessor(img.copy(), 
                            x_calc_rec=cp.deepcopy(x_calc_rec), 
                            y_calc_rec=cp.deepcopy(y_calc_rec))

    def humanCrop(self, x_margin=100, y_margin=100):
        self.df = self._getHumanArea(self.img)
        xmin, xmax, ymin, ymax = array(self.df)[0]
        x_calc_rec = self.x_calc_rec - (xmin - x_margin // 2)
        y_calc_rec = self.y_calc_rec - (ymin - y_margin // 2)
        img = self.img.crop((xmin - x_margin // 2, 
                             ymin - y_margin // 2, 
                             xmax + x_margin // 2, 
                             ymax + y_margin // 2))

        return Preprocessor(img.copy(), 
                            x_calc_rec=cp.deepcopy(x_calc_rec), 
                            y_calc_rec=cp.deepcopy(y_calc_rec))

    def correct(self):
        w,h = self.img.size
        img = self.img 
        if w > h:
            img = img.rotate(-90, expand=True)

        return Preprocessor(img.copy(),
                            x_calc_rec=cp.deepcopy(self.x_calc_rec), 
                            y_calc_rec=cp.deepcopy(self.y_calc_rec))
        
        
    def randomCrop(self, size, seed=None):
        if seed is not None:
            random.seed(seed)
        x = random.randint(0, self.img.size[0] - size[0])
        y = random.randint(0, self.img.size[1] - size[1])
        


        return Preprocessor(self.img.crop((x, y, x+size[0], y+size[1])).copy(),
                            x_calc_rec=cp.deepcopy(self.x_calc_rec) - x, 
                            y_calc_rec=cp.deepcopy(self.y_calc_rec) - y)

    def resize(self, x=None, y=None):
        w,h = self.img.size
        if x is None and y is None:
            raise ValueError("Both of x and y values are None.")

        elif x is None and y is not None:
            x = w / h * y
            v_x, v_y = x / w, y / h

        elif x is not None and y is None:
            y = h / w * x
            v_x, v_y = x / w,  y / h

        else:
            v_x = v_y = 1

        return Preprocessor(self.img.resize((int(x), int(y))).copy(),
                            x_calc_rec=cp.deepcopy(self.x_calc_rec) * v_x, 
                            y_calc_rec=cp.deepcopy(self.y_calc_rec) * v_y)

    def scale(self, x, y):
        w,h = self.img.size
        return Preprocessor(self.img.resize((int(w*x),int(h*y))).copy(),
                            x_calc_rec=cp.deepcopy(self.x_calc_rec) * x, 
                            y_calc_rec=cp.deepcopy(self.y_calc_rec) * y)

    def getIndexAsFirstImageSize(self, x_idx, y_idx):
        if isinstance(x_idx, pd.DataFrame) or isinstance(x_idx, pd.Series):
            return self.x_calc_rec.backward(x_idx.astype(int)), self.y_calc_rec.backward(y_idx.astype(int))
        else:
            return self.x_calc_rec.backward(int(x_idx)), self.y_calc_rec.backward(int(y_idx))


    def dump(self, output_path):
        self.img.save(output_path)

    def convertByte(self):
        img_bin = io.BytesIO()
        self.img.save(img_bin, format='JPEG')
        return img_bin
