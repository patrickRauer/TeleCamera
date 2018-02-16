
class Frame:
    x_start = 0
    y_start = 0
    x_size = 2048
    y_size = 2048
    bin_x = 1
    bin_y = 1


class Coordinates:
    ra_telescope = ''
    dec_telescope = ''
    ra_target = ''
    dec_target = ''


class Image:
    filter = 'B'
    exposure_time = 0
    type = 'science'


class ImageInformation:
    frame = Frame()
    coordinates = Coordinates()
    image = Image()

    def __init__(self):
        pass
