
try:
    from comtypes import COMError
except ImportError:
    COMError = AttributeError

from threading import Thread, Lock
import numpy as np
import time

from .Driver import Driver
from Camera.interface.camera_meta import CameraInformation


class CameraDriver(Driver):
    """
    The interface driver class is the direct interface to the interface ASCOM driver.
    All methods of the ASCOM driver are wrapped to a proper python interface
    with multi access checks and other security algorithms
    """

    def __init__(self, camera_driver_name, log=True):
        Driver.__init__(self, 'Camera', camera_driver_name)
        self.camera_information = CameraInformation(active_log=log)
        self.image_lock = Lock()
        self.image = None
        self.image_ready = False
        self.current_exposure = False

    def start_exposure(self, exposure_time):
        """
        Calls the interface to start a new exposure.

        :param exposure_time: The exposure time of the image
        :type exposure_time: float

        :returns: True if the exposure starts, else False
        :rtype: bool
        """
        self.current_exposure = True
        # return value
        rvalue = False
        # try to start an exposure
        try:
            # lock the interface interactions
            self.driver_lock.acquire()
            # start the exposure in the interface driver
            self.driver.StartExposure(exposure_time, True)
            # set the return value as True for a seccessfull start of
            # the exposure
            rvalue = True
            self.camera_information.set_new_update('start exposure')
        # Except a COMError of the driver
        except COMError as e:
            # writes the error information to the interface log
            self.camera_information.set_error_update('start_exposure.', e)
            # set the return value to False
            rvalue = False
            # set an error message
            self.__create_error_message__('Can\'t start the exposure')
        # Anyways do
        finally:
            # Release the lock of the interface driver
            self.driver_lock.release()
            # return the return value
            return rvalue

    def __check__image_status__(self):
        """
        Checks the current image status and stores the result in image_ready.
        """
        self.driver_lock.acquire()
        self.image_ready = self.driver.ImageReady
        self.driver_lock.release()
        while not self.image_ready:
            self.driver_lock.acquire()
            self.image_ready = self.driver.ImageReady
            self.driver_lock.release()
            time.sleep(0.1)

    def stop_exposure(self):
        """
        Stops the current exposure. This means the exposure stops and the
        readout starts.

        :returns: True if the stop was successful, else False
        :rtype: bool
        """
        self.current_exposure = False
        # set a default return value
        rvalue = False
        # try to stop the exposure
        try:
            self.camera_information.set_new_update('stop exposure')
            # lock the interface driver
            self.driver_lock.acquire()
            # Stop the exposure in the interface driver
            self.driver.StopExposure()
            # set the return value to True
            rvalue = True
        # except a COMError of the interface driver
        except COMError as e:
            # set the return value to False
            rvalue = False
            # writes the error information to the interface log
            self.camera_information.set_error_update('stop_exposure', e)
            # create a error message
            self.__create_error_message__('Can\'t stop exposure')
        # Do anyways
        finally:
            # release the lock of the interface driver
            self.driver_lock.release()
            return rvalue

    def abort_exposure(self):
        """
        Abort the current exposure. This means there is no readout after
        the exposure.

        :returns: True if the abort was successful, else False
        :rtype: bool
        """
        self.current_exposure = False
        # set the default value for the return value
        rvalue = False
        # try to abort the exposure
        try:
            self.camera_information.set_new_update('abort exposure')
            # lock the interface driver
            self.driver_lock.acquire()
            # Abort the exposure in the interface driver
            self.driver.AbortExposure()
            # set the return value to True
            rvalue = True
        # Expect a interface error
        except COMError as e:
            # Set return value to False
            rvalue = False
            # writes the error information to the interface log
            self.camera_information.set_error_update('abort_exposure', e)
            # create the error message
            self.__create_error_message__('Can\'t abort exposure')
        # do anyways
        finally:
            # release the lock of the interface driver
            self.driver_lock.release()
            # return the return value
            return rvalue

    def is_image_ready(self):
        """
        Checks if the image is ready to download.

        :returns: True if the image is ready, else False
        :rtype: bool
        """
        self.driver_lock.acquire()
        self.image_ready = self.driver.ImageReady
        self.driver_lock.release()
        return self.image_ready

    def download_image(self):
        """
        Downloads the image from the last exposure.

        :returns: The image of the last exposure, or None if there is no image
        :rtype: numpy.ndarray
        """
        th = Thread(target=self.__download_image__)
        th.start()

    def __download_image__(self):
        # create a default return value
        rvalue = None
        # try to readout the image from the interface
        try:
            self.camera_information.set_new_update('download image')
            # lock the interface driver
            self.driver_lock.acquire()
            while not self.driver.ImageReady:
                time.sleep(0.1)
            # readout the image
            print('download image')
            rvalue = self.driver.ImageArray
            print('image downloaded')
            self.image_lock.acquire()
            self.image = rvalue
            self.image_lock.release()
        # except a interface error
        except COMError as e:
            # writes the error information to the interface log
            self.camera_information.set_error_update('download_image', e)
            # create the error message
            self.__create_error_message__('Can\'t read the image')
            # set the return value back to None
            rvalue = None
        # do anyways
        finally:
            # release the interface driver lock
            self.driver_lock.release()
            # return the return value
            self.current_exposure = False
            return rvalue

    def get_image(self):
        """
        Returns the last image onetime. If there was no exposure before or you
        take the image before, the return value will be 'None'
        """
        self.image_lock.acquire()
        img = self.image
        self.image = None
        self.image_lock.release()
        img = np.array(img, dtype=np.uint16)
        img = np.transpose(img)
        self.current_exposure = False
        return img

    def get_temperature(self):
        """
        Reads the current temperature of CCD-chip.

        :returns:
            The current temperature or 99 if the temperature isn\'t
            readable.
        :rtype: float
        """
        # set a default temperature
        temperature = 99
        # try to set a new temperature
        try:
            self.camera_information.set_new_update('get_temperature')
            # lock the interface driver
            self.driver_lock.acquire()
            # reads the current ccd temperature
            temperature = self.driver.CCDTemperature
        # Except a error of the driver
        except COMError as e:
            # writes the error information to the interface log
            self.camera_information.set_error_update('get_temperature', e)
            # create the error message
            self.__create_error_message__('Can\'t readout the exposure')
        # do anyways
        finally:
            try:
                # release the interface driver lock
                self.driver_lock.release()
            except RuntimeError:
                print('ERROR: get temperature self.driver_log.release()')
            # return the temperature
            return temperature

    def get_set_temperature(self):
        """
        Returns the temperature which was set.

        :returns: temperature
        :rtype: float
        """
        return self.camera_information.get_temperature()

    def set_temperature(self, temperature):
        """
        Sets a new temperature for the CCD-chip.

        :param temperature: The new temperature
        :type temperature: float
        :returns: True if the new temperature is set, else False
        :rtype: bool
        """
        # create the default return value
        rvalue = False
        # try to set the new temperature
        try:
            self.camera_information.set_new_update('set_temperature')
            # lock the interface driver
            self.driver_lock.acquire()
            if not self.camera_information.is_current_temperature(temperature):
                # if the cooler is off
                if not self.driver.CoolerOn:
                    # turn the cooler on
                    self.driver.CoolerOn = True
                # set the new ccd temperature
                self.driver.SetCCDTemperature = float(temperature)
                # sets the new temperature to the interface information
                self.camera_information.set_temperature(temperature)
            # set the return value to True
            rvalue = True
        # expect a interface error
        except COMError as e:
            # writes the error information to the interface log
            self.camera_information.set_error_update('set_temperature', e)
            # create the error message
            self.__create_error_message__('Can\'t set a new temperature')
            # set the return value to False
            rvalue = False
        # do anyways
        finally:
            # release the interface driver lock
            self.driver_lock.release()
            # return the return value
            return rvalue

    def get_binning(self):
        """
        Reads the current binning from the interface.

        :returns:
            a list with x- and y-binning. If the binning isn\'t readable,
            the return will be [0, 0]
        :rtype: list
        """
        # sets the default return value
        rvalue = [0, 0]
        # try to readout the binning
        try:
            self.camera_information.set_new_update('get_binning')
            # lock the interface driver
            self.driver_lock.acquire()
            # reads the x-binning
            rvalue[0] = self.driver.BinX
            # reads the y-binning
            rvalue[1] = self.driver.BinY
        # expect a interface error
        except COMError as e:
            # writes the error information to the interface log
            self.camera_information.set_error_update('get_binning', e)
            # create the error message
            self.__create_error_message__('Can\'t readout binning')
            # sets the return value back to default
            rvalue = [0, 0]
        # do anyways
        finally:
            # release the interface driver lock
            self.driver_lock.release()
            # return the return value
            return rvalue

    def set_binning(self, x_bin, y_bin):
        """
        Sets a new binning.

        :param x_bin: The binning in x-direction
        :type x_bin: int
        :param y_bin: the binning in y-direction
        :type y_bin: int
        :returns: True if the new binning is set, else False
        :rtype: bool
        """
        # set the default return value
        rvalue = False
        # try to set the new binning
        try:
            self.camera_information.set_new_update('set_binning')
            # lock the interface driver
            self.driver_lock.acquire()
            if not self.camera_information.is_current_binning(x_bin, y_bin):
                # set the new binning in x direction
                self.driver.BinX = x_bin
                # set the new binning in y-direction
                self.driver.BinY = y_bin
                self.camera_information.set_binning(x_bin, y_bin)
            # set the return value to True
            rvalue = True
        # expect a interface driver error
        except COMError as e:
            # writes the error information to the interface log
            self.camera_information.set_error_update('set_binning', e)
            # create the error message
            self.__create_error_message__('Can\'t set a new binning')
            # set the return value to False
            rvalue = False
        # do anyways
        finally:
            # release the interface driver lock
            self.driver_lock.release()
            # return the return value
            return rvalue

    def get_subframe(self):
        """
        Reads the current subframe of the interface.

        :returns:
            a list with the style [x0, y0, w, h] if the subframe is readable,
            else [0, 0, 0, 0].
        :rtype: list
        """
        # set the default return value
        rvalue = [0, 0, 0, 0]
        # try to readout the subframe
        try:
            # write the current method to the log
            self.camera_information.set_new_update('get_subframe')
            # lock the interface driver
            self.driver_lock.acquire()
            # readout the start of the subframe in x-direction
            rvalue[0] = self.driver.StartX
            # readout the start of the subframe in y-direction
            rvalue[1] = self.driver.StartY
            # readout the size of the subframe in x-direction
            rvalue[2] = self.driver.NumX
            # readout the size of the subframe in y-direction
            rvalue[3] = self.driver.NumY
        # expect a interface error
        except COMError as e:
            # writes the error information to the interface log
            self.camera_information.set_error_update('get_subframe', e)
            # create an error message
            self.__create_error_message__('Can\'t readout the subframe')
            # set the return value back to default
            rvalue = [0, 0, 0, 0]
        # do anyways
        finally:
            # release the interface driver lock
            self.driver_lock.release()
            # return the return value
            return rvalue

    def set_subframe(self, x0, y0, w, h):
        """
        Sets a new subframe.

        :param x0: the starting point of the subframe in x-direction
        :type x0: int
        :param y0: the starting point of the subframe in y-direction
        :type y0: int
        :param w: the width of the subframe (x-direction)
        :type w: int
        :param h: the height of the subframe (y-direction)
        :type h: int
        :returns: True if the new subframe is set, else False
        :rtype: bool
        """
        # create the default return value
        rvalue = False
        # try to set the subframe
        try:
            self.camera_information.set_new_update('set_subframe')
            # lock the interface driver
            self.driver_lock.acquire()
            # if the new subframe is different to the current one
            if not self.camera_information.is_current_subframe(x0, y0, w, h):
                # set x0
                self.driver.StartX = x0
                # set y0
                self.driver.StartY = y0
                # set width
                self.driver.NumX = w
                # set height
                self.driver.NumY = h
                # sets the subframe information to the information object
                self.camera_information.set_subframe(x0, y0, w, h)
            # set the return value to True
            rvalue = True
        # expect a interface error
        except COMError as e:
            # write a new error information to the log
            self.camera_information.set_error_update('set_subframe', e)
            # create an error message
            self.__create_error_message__('Can\'t set a new subframe')
            # set the return value back to False
            rvalue = False
        # do anyways
        finally:
            # release the lock of the interface
            self.driver_lock.release()
            # return the return value
            return rvalue

    def is_cooler(self):
        rvalue = False
        try:
            # lock the interface driver
            self.driver_lock.acquire()
            # ask for cooler status
            rvalue = self.driver.CoolerOn
        # expect a interface error
        except COMError as e:
            # write a new error information to the log
            self.camera_information.set_error_update('is_cooler', e)
            # create an error message
            self.__create_error_message__('Unable to check cooler status')
            # set the return value back to False
            rvalue = False
        # do anyways
        finally:
            # release the lock of the interface
            self.driver_lock.release()
            # return the return value
            return rvalue

    def set_cooler(self, status):
        """
        Sets a new cooler status. This means it turns the cooler on or off.

        :param status: True if you want to start the cooler, else False
        :type status: bool
        """
        try:
            # lock the interface driver
            self.driver_lock.acquire()
            # set new cooler status
            self.driver.CoolerOn = status
        # expect a interface error
        except COMError as e:
            # write a new error information to the log
            self.camera_information.set_error_update('set_cooler', e)
            # create an error message
            self.__create_error_message__('Unable to set cooler status')
        # do anyways
        finally:
            # release the lock of the interface
            self.driver_lock.release()

    def warm_up(self):
        """
        Warms the CCD-chip slowly up.
        """
        temperature = self.get_temperature()
        self.set_temperature(temperature + 3)
        time.sleep(10)
        temperature_act = self.get_temperature()
        while abs(temperature - temperature_act) > 2:
            temperature = temperature_act
            self.set_temperature(temperature + 3)
            time.sleep(10)
            temperature_act = self.get_temperature()

    def is_exposure(self):
        """
        Checks if there is an exposure at the moment.

        :returns: True if there is an exposure, else False.
        :rtype: bool
        """
        return self.current_exposure