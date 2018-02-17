
from threading import Thread
from multiprocessing import Process
from Camera.meta.image_log import ImageLog
from Camera.drivers.Driver import Chooser, get_driver_information, set_driver_information
from Camera.drivers.camera_driver import CameraDriver
from Camera.drivers.filter_wheel_driver import FilterWheelDriver
from .camera_meta import CameraStatus

try:
    from ImageProcessing.astrometry.coordinate_align import Astrometry
except ImportError:
    Astrometry = None

from astropy.io import fits
import os
import time


class Camera:
    camera = None
    filterwheel = None
    last_image = None
    active = True
    readout_time = 0
    image_abort = False
    sequence = False
    images_left = 0
    current_imageing = False

    coordinate_signal = None
    signal_image_saved = None
    """
    The interface class is the main interface for interface and filter wheel
    interactions. Every process as to go via this class to reduce the change
    of a crash.
    """

    def __init__(self, camera_driver_name='ASCOM.Simulator.Camera',
                 filterwheel_driver_name='ASCOM.Simulator.FilterWheel',
                 signal=None):
        self.__driver_initialisation__(camera_driver_name, filterwheel_driver_name)
        self.camera_status = CameraStatus()
        self.image_log = ImageLog(signal=signal)
        self.th = Thread(target=self.run)
        self.th.start()

    def __driver_initialisation__(self, camera_driver, filter_wheel_driver, test=False):
        """
        Starts the drivers to the interface and the filter wheel.
        It searchs in the config file for the driver names.

        :param camera_driver: the name of the interface driver or an empty string
        :type camera_driver: str
        :param filter_wheel_driver:
            the name of the filter wheel driver or an empty string
        """
        # If there is no information of the drivers
        if camera_driver == '':
            if os.path.exists('./config.txt'):
                camera_driver = get_driver_information('./config.txt',
                                                       'Camera').split(' ')[0]
            if camera_driver == '':
                cam = Chooser(device_type='Camera')
                camera_driver = cam.choose()
                if not test:
                    set_driver_information('./config.txt', 'Camera',
                                           camera_driver)
        if filter_wheel_driver == '':
            if os.path.exists('./config.txt'):
                filter_wheel_driver = get_driver_information('./config.txt',
                                                             'Filterwheel').split(' ')[0]
            if filter_wheel_driver == '':
                wheel = Chooser(device_type='Filterwheel')
                filter_wheel_driver = wheel.choose()
                if not test:
                    set_driver_information('./config.txt', 'Filterwheel',
                                           filter_wheel_driver)
        # Create an object of a COM-object of the interface
        self.camera = CameraDriver(camera_driver)
        # Create an object of a COM-object of the filterwheel
        self.filterwheel = FilterWheelDriver(filter_wheel_driver)

    def run(self):
        while self.active:
            self.status_update()

    def status_update(self):
        """
        Updates the interface status
        """
        # updates the current temperature of the ccd-chip
        self.camera_status.set_temperature(self.camera.get_temperature())
        if self.is_exposure_in_process():
            if (self.camera_status.exposure_process.get_time_left_percent() == 100 and
                    not self.is_readout_in_process()):
                if not self.image_abort:
                    self.camera.download_image()
                    self.camera_status.start_readout(self.camera_status.get_image_information().get_readout_time())
                    self.readout_time = time.time()
                else:
                    self.camera_status.reset()
            elif self.is_readout_in_process():
                if self.camera_status.readout_process.get_time_left() <= 0:
                    if self.camera.is_image_ready():
                        self.__save_image__()
                        self.camera_status.reset()
        time.sleep(0.1)

    def __save_image__(self):
        """
        Saves the image with all available information.
        """
        img = self.camera.get_image()
        info = self.camera_status.get_image_information()
        self.camera_status.reset()
        self.last_image = img
        hdu = fits.PrimaryHDU(img)
        hdu.header = self.__create_header__(hdu.header, info)
        save_path = info.get_save_path()
        c = 0
        while os.path.exists(save_path):
            if c == 0:
                save_path = save_path.split('.fit')[0]
            else:
                save_path = save_path.split('_{}.fit'.format(c-1))[0]
            save_path += '_{}.fits'.format(c)
            c += 1
        hdu.writeto(save_path)

        add_wcs(save_path, self.coordinate_signal)

        # add a line to image log
        self.image_log.add(info.get_utc(),
                           info.get_observer(), info.get_object_name(),
                           info.get_ra_telescope(), info.get_dec_telescope(),
                           info.get_ra_target(), info.get_dec_target(),
                           info.get_image_type(), str(info.get_exposure_time()),
                           info.get_filter_name(),
                           info.get_subframe_string(),
                           info.get_binning_string(),
                           str(self.camera_status.get_temperature()),
                           str(info.get_temperature_dome()),
                           str(info.get_temperature_outside()),
                           str(info.get_humidity_dome()),
                           str(info.get_humidity_outside()),
                           time.time() - self.readout_time, save_path)
        self.__image_done__(save_path)
        self.image_left -= 1
        self.current_imageing = False

    def __create_header__(self, header, info):
        """
        Create the header for the image.
        Including object, observer, exposure time, image type, Filter name,
        subframe, binning, date, jd, ra-telescope, dec-telescope,
        ra-target, dec-target, temperature of the ccd and weather information
        if an :class:`ImageInformation` object was used.

        :param header:
            Original header of the image
        :type header: :class:`astropy.io.Header`

        :returns: Original header with the additional information.
        """
        # TODO: put the header thing in a separate file
        if info is not None:
            head = self.camera_status.get_header()
            header[head.object] = info.get_object_name()
            # identification
            header[head.observer] = (info.get_observer(), 'Name of the observer')
            header[head.exposure_time] = (info.get_exposure_time(), 'Exposure time')
            header['EXPTIME'] = (info.get_exposure_time(), 'Exposure time')
            header[head.image_type] = (info.get_iraf_type(),
                                       'Image type LIGHT, FLAT or DARK')
            filter_name = info.get_filter_name()
            header[head.filter_name] = (filter_name, 'Name of the filter')

            header[head.bin_x] = (info.get_bin_x(), 'Binning factor in width')
            header[head.bin_y] = (info.get_bin_y(), 'Binning factor in height')
            header[head.subframe_size_x] = (info.get_x0(),
                                            'Subframe X position in binned pixels')
            header[head.subframe_size_y] = (info.get_y0(),
                                            'Subframe Y position in binned pixels')

            # Time information
            header[head.date_cet] = (info.get_cet().strftime("%Y-%m-%dT%H:%M:%S"),
                                     'Start of the observation')
            image_time = info.get_utc()
            header[head.jd] = (image_time.jd, 'Julian Date')
            header['MJD'] = (image_time.mjd, 'modified julian date')
            header[head.date_obs] = (image_time.isot,
                                     'Start of the observation')

            # position information
            header[head.telescope_ra] = (info.get_ra_telescope(), 'RA of the telescope')
            header[head.telescope_dec] = (info.get_dec_telescope(), 'DEC of the telescope')
            header[head.RA] = (info.get_ra_target(), 'RA of the target')
            header[head.DEC] = (info.get_dec_target(), 'DEC of the target')
            azi, alt, ha = info.get_azi_alt_ha(header[head.jd])
            header[head.azimuth] = (azi[0], 'Azimuth of the telescope')
            header[head.altitude] = (alt[0], 'Altitude of the telescope')
            header[head.hourangle] = (ha[0], 'Hourangle of the telescope')

            # interface temperature information
            header[head.ccd_temp] = (self.get_temperature(),
                                     'The temperature of the CCD chip')
            header[head.ccd_temp_set] = (self.camera.camera_information.get_temperature(),
                                         'The temperature which was set')

            # weather information
            if info.weather_data is not None:
                header['WEATHER'] = 'Weather data'
                header['WDINFO'] = (info.get_weather_information(), '')
                header[head.weather_date] = (info.weather_data.get_date(),
                                             'Date and time of the weather entry')
                header[head.temp_dome] = (info.get_temperature_dome(), 'Temperature in the dome')
                header[head.dew_dome] = (info.get_dewpoint(), 'Dewpoint-Dome')
                header[head.hum_dome] = (info.get_humidity_dome(), 'Humidity-Dome')
                header[head.temp_schm] = (info.get_temperature_schmidtplate(), 'Temperature-Schmidtplate')
                header[head.heating] = (info.get_heating(), '#0-off, 1-on')
                header[head.temp_mount] = (info.get_temperature_mount(), 'Temperature mount')
                header[head.temp_out] = (info.get_temperature_outside(),
                                         'Temperature outside of the dome')
                header[head.hum_out] = (info.get_humidity_outside(), 'Humidity outside of the dome')

            # telescope information
            header[head.lat] = (50 + 58. / 60 + 48.8 / 3600, 'Latitude of the observatory')
            header[head.lon] = (11 + 42. / 60 + 40.2 / 3600, 'Longitude of the observatory')
            header[head.telescope] = 'FFC 3.2'
            header[head.focal] = (940, 'Focal length in mm')
            header[head.aperature] = (300, 'Aperature diameter in mm')
            header[head.instrument] = ('TEST_30cm_MI', 'Instrument name')

        return header

    def take_image(self, image_information):
        """
        Starts a new exposure with an :class:`Camera.meta.image_information.ImageInformation`
        object.

        :param image_information: Information of the image
        :type image_information: Camera.meta.image_information.ImageInformation
        """

        self.camera_status.reset_stopped()
        self.image_abort = False
        if image_information.get_image_amount() > 1:
            self.sequence = True
        th = Thread(target=self.__take_image__, args=(image_information,))
        th.start()

    def __take_image__(self, image_information):
        self.image_left = image_information.get_image_amount()
        for i in range(image_information.get_image_amount()):
            image_information.update_date()
            # stops the next exposure if the last exposure was stopped
            # or aborted
            if self.camera_status.is_stopped():
                break
            # if there is no exposure at the moment
            c = 0
            while not self.is_camera_ready() or self.current_imageing:
                time.sleep(0.5)
                c += 1
                if c % 20 == 0:
                    if self.camera_status.is_stopped():
                        break
            self.current_imageing = True
            # sets the properties for the next exposure
            self.set_image_properties(image_information)
            while not self.filterwheel.is_ready():
                time.sleep(0.1)
            # start the actual exposure in the driver
            exposure_time = image_information.get_exposure_time()
            self.camera.start_exposure(exposure_time)
            self.camera_status.start_exposure_time(exposure_time)
            self.camera_status.set_image_information(image_information)
            time.sleep(2)

        self.sequence = False

    def set_image_properties(self, img_info):
        """
        Sets the properties of the next image by the information of the
        image_information object.

        :param img_info: the information for the next image
        :type img_info: :class:`image.Image_Information`
        """
        # set the new binning to interface
        self.set_binning(*img_info.get_binning())
        # set the new subframe to the interface
        self.set_subframe(*img_info.get_subframe())
        # set the new filter to the filter wheel
        self.filterwheel.set_filter_by_name(img_info.get_filter_name())

    def get_properties(self):
        """
        Returns the current interface properties.

        :returns: the interface properties
        :rtype: dict
        """
        exposure_properties = self.camera_status.exposure_status()
        readout_properties = self.camera_status.readout_status()
        stati = {'interface': self.camera.connection,
                 'filterwheel': self.filterwheel.connection,
                 'temperature': self.camera.get_temperature(),
                 'filter': self.filterwheel.get_filter_name(),
                 'status': self.get_status_camera(),
                 'exposure_time': exposure_properties[0],
                 'exposure_time_percent': exposure_properties[1],
                 'readout_time': readout_properties[0],
                 'readout_time_percent': readout_properties[1],
                 'object': self.camera_status.get_target_name(),
                 'stopped': self.camera_status.was_stopped()}
        return stati

    def get_image_infos(self):
        """
        Returns the image information out of the camera_status.

        :returns: the image information
        :rtype: dict
        """
        return self.camera_status.get_image_infos()

    def set_binning(self, bin_x, bin_y):
        """
        Sets a new binning to the interface if the new binning is different to
        the current binning

        :param bin_x: binning in x-direction
        :type bin_x: int
        :param bin_y: binning in y-direction
        :type bin_y: int
        """
        self.camera.set_binning(bin_x, bin_y)

    def set_subframe(self, x0, y0, w, h):
        """
        Sets a new subframe to the interface if the new subframe is different to
        the current subframe

        :param x0: starting point of subframe in x-direction
        :type x0: int
        :param y0: starting point of subframe in y-direction
        :type y0: int
        :param w: width of the subframe (x-direction)
        :type w: int
        :param h: height of the subframe (y-direction)
        :type h: int
        """
        # set the new subframe to the interface
        self.camera.set_subframe(x0, y0, w, h)

    def get_status_camera(self):
        """
        Returns the status labels and information of the interface and the
        filter wheel.

        :returns: the interface information
        :rtype: dict
        """
        return self.camera_status.get_status_label()

    def set_filter(self, name):
        """
        Sets a new filter by his name.

        :param name: the name of the filter (U, B, V, R, I, None)
        :type name: str
        """
        self.filterwheel.set_filter_by_name(name)

    def get_filter_name(self):
        """
        Returns the name of the current filter

        :returns: filter name
        :rtype: str
        """
        return self.filterwheel.get_filter_name()

    def get_filter_id(self, filter_name):
        """
        Returns the filter id for the filter with this name.

        :param filter_name: Name of the filter
        :type filter_name: str
        :returns: the number of the filter in the filter wheel
        :rtype: int
        """
        return self.filterwheel.get_corresponding_filter_nr(filter_name)

    def get_temperature(self):
        """
        Returns the last stored temperature of the ccd-chip

        :returns: the temperature of the ccd-chip
        :rtype: float
        """
        return self.camera_status.get_temperature()

    def is_exposure_in_process(self):
        """
        Asks if an exposure is currently in process

        :returns: True if a exposure is in process, else False
        :rtype: bool
        """
        return self.camera_status.exposure_in_process()

    def is_readout_in_process(self):
        """
        Asks if a readout is currently in process

        :returns: True if a readout is in process, else False
        :rtype: bool
        """
        return self.camera_status.readout_in_process()

    def is_camera_ready(self):
        """
        Asks if the interface is ready. This means that there is currently no
        exposure or readout.

        :returns: True if the interface is ready, else False
        :rtype: bool
        """
        return (not self.camera_status.readout_in_process() and
                not self.camera_status.exposure_in_process())

    def is_camera_ready2(self):
        """
        Same as :meth:`is_camera_ready` but it takes a sequence in to account, too.
        """
        return self.is_camera_ready() and not self.sequence

    def is_camera_connected(self):
        """
        Asks if the interface is connected or not.

        :returns: True if the interface is connected, else False.
        :rtype: bool
        """
        return self.camera.is_connect()

    def disconnect_camera(self):
        """
        Disconnect the connection to the interface.
        """
        self.camera.disconnect()

    def is_filter_wheel_connected(self):
        """
        Asks if the filterwheel is connected or not.

        :returns: True if the filterwheel is connected, else False.
        :rtype: bool
        """
        return self.filterwheel.is_connect()

    def disconnect_filter_wheel(self):
        """
        Disconnect the connection to the filterwheel.
        """
        self.filterwheel.disconnect()

    def is_connected(self):
        """
        Aks if all subdevices (interface and filterwheel) are connected or not.

        :returns: True if both are connected, else False
        :rtype: bool
        """
        return self.is_camera_connected() and self.is_filter_wheel_connected()

    def disconnect(self):
        """
        Disconnect the connections to the filterwheel and the interface. Also
        the thread of this class will end after the next run.
        """
        self.active = False
        self.disconnect_camera()
        self.disconnect_filter_wheel()

    def add_signal(self, signal_img_saved, signal_err, coordinate_signal=None):
        """
        Adds the optional signal to the interface class.

        :param signal_img_saved:
            Signal which is called after the an exposure is done.

        :param signal_err:
            Signal which is called after an error happen.
        :param coordinate_signal: Signal to send the WCS solution back to the top
        """
        self.signal_image_saved = signal_img_saved
        self.coordinate_signal = coordinate_signal

    def set_signal(self, signal_readout):
        pass

    def __image_done__(self, path):
        """
        Calls the signal to say that a image is ready.

        :param path: The path where the image was saved.
        :type path: str
        """
        if self.signal_image_saved is not None:
            self.signal_image_saved.update_label(path)

    def stop_exposure(self):
        """
        Stops the current exposure and starts the readout.
        """
        if self.camera_status.get_status_id() == 2 and not self.camera_status.is_stopped():
            self.camera_status.stop_exposure()
            self.camera.stop_exposure()

    def abort_exposure(self):
        """
        Stops the current exposure without a readout.
        """
        status_id = self.camera_status.get_status_id()
        if 2 <= status_id <= 3:
            self.camera.abort_exposure()
            self.camera_status.abort_exposure()
            self.image_abort = True
            self.current_imageing = False
            self.sequence = False

    def get_set_temperature(self):
        """
        Returns the temperature which was set.

        :returns: the set temperature
        :rtype: float
        """
        return self.camera.get_set_temperature()

    def is_cooler_on(self):
        """
        Returns the status of the cooler

        :returns: True if the cooler is on, else False
        :rtype: bool
        """
        return self.camera.is_cooler()

    def set_cooler(self, status):
        """
        Sets a new status to the cooler.

        :param status: True to active the cooler, else False.
        :type status: bool
        """
        self.camera.set_cooler(status)

    def warm_up(self):
        """
        Increase the temperature of the interface slowly.
        """
        th = Thread(target=self.camera.warm_up)
        th.start()

    def set_temperature(self, temperature):
        """
        Sets a new temperature for cooling.
        """
        self.camera.set_temperature(temperature)


def add_wcs(path, coordinate_signal):
    """
    Starts a secondary process to generate the WCS for the image
    :param path: The path to the image
    :type path: str
    :param coordinate_signal: Signal to send the offset back to the main process
    :return:
    """
    process = Process(target=__add_wcs__, args=(path, coordinate_signal,))
    process.start()


def __add_wcs__(path, coordinate_signal):
    """
    Calculates and adds the WCS to the image
    :param path: The path to the image
    :type path: str
    :param coordinate_signal: Signal to send the offset back to the main process
    :return:
    """
    if Astrometry is None:
        return

    astrometry = Astrometry(path)
    try:
        astrometry.calibrate()
        delta_ra, delta_dec = astrometry.evaluate()
        coordinate_signal.emit([delta_ra, delta_dec])
    except TypeError as e:
        print(e)

