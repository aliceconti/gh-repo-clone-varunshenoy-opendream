'''
The Layer class. A layer consists of an image and metadata. 
It can also optionally contain other kwargs. 
'''
from PIL import Image
import requests
import typing
import base64
from io import BytesIO
import numpy as np
import os
import re

class Layer:

    def __init__(self, image: Image.Image, metadata: dict = {}, **kwargs):
        self.image = image
        self.id = -1
        self.metadata = metadata
        self.kwargs = kwargs # kwargs like opacity, etc.

    def get_image(self):
        return self.image
    
    def get_id(self):
        return self.id
    
    def set_id(self, id):
        self.id = id
    
    def get_metadata(self):
        return self.metadata
    
    def set_metadata(self, metadata: dict):
        self.metadata = metadata
        
    def save_image(self):
        # if debug doesn't exist, create it
        try:
            os.mkdir("debug")
        except:
            pass
        self.image.save(f"debug/{self.id}.png")
    
    @staticmethod
    def pil_to_b64(pil_img):
        # Determine the format of the input PIL image
        img_format = pil_img.format.upper() if pil_img.format else "PNG"

        # Create the base64 preamble with the correct image format
        BASE64_PREAMBLE = f"data:image/{img_format.lower()};base64,"

        # Save the PIL image to a byte buffer
        buffered = BytesIO()
        pil_img.save(buffered, format=img_format)

        # Encode the byte buffer as base64 and return the complete string
        img_str = base64.b64encode(buffered.getvalue())
        return BASE64_PREAMBLE + str(img_str)[2:-1]


    @staticmethod
    def b64_to_pil(b64_str):
        # Generalized base64 preamble pattern
        PREAMBLE_REGEX = r'data:image/[^;]+;base64,'

        # Remove the base64 preamble
        b64_str_without_preamble = re.sub(PREAMBLE_REGEX, "", b64_str)

        # Decode base64 string and create a PIL Image object
        return Image.open(BytesIO(base64.b64decode(b64_str_without_preamble)))

    @staticmethod
    def b64_to_layer(b64_str):
        return Layer(image=Layer.b64_to_pil(b64_str))
        
    def serialize(self):
        return {
            "id": self.id,
            "metadata": self.metadata,
            "image": Layer.pil_to_b64(self.image)
        }
        
    @staticmethod
    def from_url(url: str, metadata: dict = {}, **kwargs):
        return Layer(
            image=Image.open(requests.get(url, stream=True).raw),
            metadata=metadata,
            **kwargs
        )
        
    @staticmethod
    def from_path(path: str, metadata: dict = {}, **kwargs):
        # check if path is url
        if path.startswith("http"):
            return Layer.from_url(path, metadata, **kwargs)
        
        # TODO: remove this option. this is a hacky way to make this work in our current setup - typically users will
        # upload base64 encoded images, or perhaps links to s3 buckets
        return Layer(
            image=Image.open(path),
            metadata=metadata,
            **kwargs
        )

    def get_np_image(self):
        return np.array(self.image)
    
    def resize(self, width: int, height: int):
        self.image = self.image.resize((width, height))
        
    def resize_to_nearest_eighth(self):
        width, height = self.image.size
        width = round(width / 8) * 8
        height = round(height / 8) * 8
        self.image = self.image.resize((width, height))
    

class ImageLayer(Layer):
    def __init__(self, image: Image.Image, metadata: dict = {}, **kwargs):
        super().__init__(image, metadata, **kwargs)

class MaskLayer(Layer):
    def __init__(self, image: Image.Image, metadata: dict = {}, **kwargs):
        super().__init__(image, metadata, **kwargs)
