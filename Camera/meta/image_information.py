from astropy.time import Time
from datetime import datetime


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

    # TODO: implement azimuth, altitude and hour angle calculations
    def get_azi_alt_ha(self, jd):
        return [0, 0, 0]


class Image:
    filter = 'B'
    exposure_time = 0
    type = 'science'
    number = 1
    observer = ''
    object = ''


class Camera:
    temperature = 0


class Weather:
    temperature_outside = 0
    temperature_dome = 0
    temperature_schmidtplate = 0
    temperature_mount = 0
    humidity_outside = 0
    humidity_dome = 0

    dewpoint = 0
    heating = 0
    heating_dewcap = 0

    information = 'Dummy'


class TelescopeTime:
    date = None
    date_cet = None

    def update_time(self):
        self.date = Time.now()
        self.date_cet = datetime.now()


class ImageInformation:
    frame = Frame()
    coordinates = Coordinates()
    image = Image()
    camera = Camera()
    weather = Weather()
    time = TelescopeTime()

    def __init__(self):
        pass

    def get_object_name(self):
        return self.image.object

    def get_observer(self):
        return self.image.observer

    def get_image_amount(self):
        return self.image.number

    def update_date(self):
        self.time.update_time()

    def get_exposure_time(self):
        return self.image.exposure_time

    def get_binning(self):
        return [self.frame.bin_x, self.frame.bin_y]

    def get_binning_string(self):
        return '{:1d}:{:1d}'.format(*self.get_binning())

    def get_bin_x(self):
        return self.frame.bin_x

    def get_bin_y(self):
        return self.frame.bin_y

    def get_x0(self):
        return self.frame.x_start

    def get_y0(self):
        return self.frame.y_start

    def get_x_size(self):
        return self.frame.x_size

    def get_y_size(self):
        return self.frame.y_size

    def get_subframe(self):
        return [self.frame.x_start, self.frame.y_start,
                self.frame.x_size, self.frame.y_size]

    def get_subframe_string(self):
        return '{:04d}:{:04d};{:04d}:{:04d}'.format(*self.get_subframe())

    def get_filter(self):
        return self.image.filter

    def get_utc(self):
        return self.time.date

    def get_cet(self):
        return self.time.date_cet

    def get_temperature(self):
        return self.camera.temperature

    def get_ra_telescope(self):
        return self.coordinates.ra_telescope

    def get_dec_telescope(self):
        return self.coordinates.dec_telescope

    def get_ra_target(self):
        return self.coordinates.ra_target

    def get_dec_target(self):
        return self.coordinates.dec_target

    def get_azi_alt_ha(self, jd):
        return self.coordinates.get_azi_alt_ha(jd)

    def get_temperature_outside(self):
        return self.weather.temperature_outside

    def get_temperature_dome(self):
        return self.weather.temperature_dome

    def get_temperature_schmidtplate(self):
        return self.weather.temperature_schmidtplate

    def get_temperature_mount(self):
        return self.weather.temperature_mount

    def get_humidity_outside(self):
        return self.weather.humidity_outside

    def get_humidity_dome(self):
        return self.weather.humidity_dome

    def get_humidity_dewcap(self):
        return self.weather.humidity_dewcap

    def get_dewpoint(self):
        return self.weather.dewpoint

    def get_heating(self):
        return self.weather.heating

    def get_heating_dewcap(self):
        return self.weather.heating_dewcap

    def get_weather_information(self):
        return self.weather.information

    def update_weather(self, weather):
        weather = weather.get_data_as_dict()
        self.weather.temperature_outside = weather['temperature_outside']
        self.weather.temperature_dome = weather['temperature_dome']
        self.weather.temperature_schmidtplate = weather['temperature_schmidtplate']
        self.weather.temperature_mount = weather['temperature_mount']
        self.weather.humidity_outside = weather['humidity_outside']
        self.weather.humidity_dome = weather['humidity_dome']
        self.weather.dewpoint = weather['dewpoint']
        self.weather.date = weather['date']
        self.weather.heating = weather['heating']

    @staticmethod
    def from_dict(data):
        information = ImageInformation()
        information.frame.x_start = data['x0']
        information.frame.y_start = data['y0']
        information.frame.x_size = data['width']
        information.frame.y_size = data['height']
        information.frame.bin_x = data['bin_x']
        information.frame.bin_y = data['bin_y']

        information.image.number = data['repeats']
        information.image.object = data['object']
        information.image.filter = data['filter']
        information.image.exposure_time = data['exposure']
        information.image.type = data['image_type']
        return information
