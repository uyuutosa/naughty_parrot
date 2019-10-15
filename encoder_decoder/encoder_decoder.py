import json
import io
import PIL.Image as I
import pandas as pd
import pickle
import base64
import zlib

class EncoderDecoder:
    def __init__(self, is_compress=True):
        self.is_compress=is_compress

    def encode(self, x):
        return x

    def decode(self, x):
        return x


class ImageEncoderDecoder(EncoderDecoder):
    def __init__(self, image_format="jpeg", is_compress=True):
        super().__init__(is_compress)
        self.image_format = image_format

    def encode(self, x):
        if isinstance(x, str):
            x = open(x, 'rb').read()
        elif isinstance(x, I.Image):
            img_bytes = io.BytesIO()
            x.save(img_bytes, format=self.image_format)
            img_bytes.seek(0)
            x = img_bytes.read()
        if self.is_compress:
            x = zlib.compress(x)
        x = base64.b64encode(x)
        return x.decode()

    def decode(self, x):
        if isinstance(x, str):
            x = x.encode()
        x = base64.b64decode(x)
        if self.is_compress:
            x = zlib.decompress(x)
        return I.open(io.BytesIO(x))

class CSVEncoderDecoder(EncoderDecoder):
    def __init__(self, is_compress=True):
        super().__init__(is_compress)

    def encode(self, x):
        if isinstance(x, pd.DataFrame):
            x = x.to_csv().encode()
        elif isinstance(x, str):
            x = x.encode()
        if self.is_compress:
            x = zlib.compress(x)
        x = base64.b64encode(x)
        return x.decode()

    def decode(self, x):
        if isinstance(x, str):
            x = x.encode()
        x = base64.b64decode(x)
        if self.is_compress:
            x = zlib.decompress(x)
        x = x.decode()
        x = pd.read_csv(io.StringIO(x),index_col=0)
        return x

class PickleEncoderDecoder(EncoderDecoder):
    def __init__(self, is_compress=True):
        super().__init__(is_compress)

    def encode(self, x):
        f = io.BytesIO()
        file = pickle.dump(x, f)
        f.seek(0)
        x = f.read()
        if self.is_compress:
            x = zlib.compress(x)
        x = base64.b64encode(x)
        return x.decode()

    def decode(self, x):
        if isinstance(x, str):
            x = x.encode()
        x = base64.b64decode(x)
        if self.is_compress:
            x = zlib.decompress(x)
        f = io.BytesIO(x)
        x = pickle.load(f)
        return x


