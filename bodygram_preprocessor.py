from .preprocessor import Preprocessor
    
def BodygramPreprocessor(front_img_path, side_img_path):
    front_preprocessed = Preprocessor(front_img_path).correct().correctExif().resize(714).humanCrop(x_margin=300,y_margin=300).resize(416)
    side_preprocessed  = Preprocessor(side_img_path).correct().correctExif().resize(714).humanCrop(x_margin=250, y_margin=200).resize(316).crop(0, 0, 316, 1000)
    return front_preprocessed, side_preprocessed
    
