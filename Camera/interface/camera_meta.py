from Camera.drivers.Driver import DriverLog
from Camera.meta.header import Header
from threading import Thread, Lock
import time


class CameraInformation(DriverLog):
    def __init__(self, active_log):
        if active_log:
            DriverLog.__init__(self, './log/camera_log.txt')
        else:
            DriverLog.__init__(self)

        self.bin_x = 1
        self.bin_y = 1
        self.subframe_x0 = 0
        self.subframe_y0 = 0
        self.subframe_w = 4096
        self.subframe_h = 4096
        self.temperature = 99

    def get_bin_x(self):
        """
        Returns the current binning in x-direction.

        :returns: x-binning
        :rtype: int
        """
        return self.bin_x

    def get_bin_y(self):
        """
        Returns the current binning in y-direction.

        :returns: y-binning
        :rtype: int
        """
        return self.bin_y

    def set_binning(self, bin_x, bin_y):
        """
        Sets a new binning in x-, y-direction.

        :param bin_x: x-binning
        :type bin_x: int
        :param bin_y: y-binning
        :type bin_y: int
        """
        self.bin_x = bin_x
        self.bin_y = bin_y
        self.set_new_update('new binning, x:{:1d}  y:{:1d}'.format(bin_x,
                                                                   bin_y))

    def is_current_binning(self, bin_x, bin_y):
        """
        Checks if this binning is the current binning.

        :param bin_x: x-binning
        :type bin_x: int
        :param bin_y: y-binning
        :type bin_y: int
        :returns:
            True if both are the same as the ones which are stored, else
            False
        :rtype: bool
        """
        return self.bin_x == bin_x and self.bin_y == bin_y

    def get_subframe_x0(self):
        """
        Returns the starting point in x-direction of the subframe

        :returns: x0
        :rtype: int
        """
        return self.subframe_x0

    def get_subframe_y0(self):
        """
        Returns the starting point in y-direction of the subframe

        :returns: y0
        :rtype: int
        """
        return self.subframe_y0

    def get_subframe_width(self):
        """
        Returns the width in x-direction of the subframe

        :returns: width
        :rtype: int
        """
        return self.subframe_w

    def get_subframe_height(self):
        """
        Returns the height in x-direction of the subframe

        :returns: height
        :rtype: int
        """
        return self.subframe_h

    def set_subframe(self, x0, y0, w, h):
        """
        Sets a new subframe.

        :param x0: the starting point in x-direction of the subframe
        :type x0: int
        :param y0: the starting point in y-direction of the subframe
        :type y0: int
        :param w: the width of the subframe in x-direction
        :type w: int
        :param h: the height of the subframe in y-direction
        :type h: int
        """
        self.subframe_x0 = x0
        self.subframe_y0 = y0
        self.subframe_w = w
        self.subframe_h = h
        self.set_new_update('new subframe, x0:{:04d} y0:{:04d}' +
                            ' w:{:04d} h:{:04d}'.format(x0, y0, w, h))

    def is_current_subframe(self, x0, y0, w, h):
        """
        Checks if this subframe is the same as the stored one.

        :param x0: the starting point in x-direction of the subframe
        :type x0: int
        :param y0: the starting point in y-direction of the subframe
        :type y0: int
        :param w: the width of the subframe in x-direction
        :type w: int
        :param h: the height of the subframe in y-direction
        :type h: int
        :returns: True if the bounds are the same, else False
        :rtype: bool
        """
        return (self.subframe_x0 == x0 and self.subframe_y0 == y0 and
                self.subframe_w == w and self.subframe_h == h)

    def set_temperature(self, temperature):
        """
        Sets a new temperature.

        :param temperature: the new temperature
        :type temperature: float
        """
        self.temperature = temperature
        self.set_new_update('new temperature: ' + str(temperature))

    def is_current_temperature(self, temperature):
        """
        Checks if this temperature is the same as the stored one.

        :param temperature: the new temperature
        :type temperature: float
        :returns: True if there are the same, else False
        :rtype: bool
        """
        return self.temperature == temperature

    def get_temperature(self):
        """
        Returns the stored temperature.

        :returns: the temperature
        :rtype: float
        """
        return self.temperature


class Process(Thread):
    """
    This class represents a process with a defined time, like a exposure or a
    readout. It counts the time between the start and now to calculate the
    information like left time or the percent of the process.
    """

    def __init__(self, ctime, signal=None):
        # ini Thread super-class
        Thread.__init__(self)
        # store the complete time
        self.ctime = ctime
        # store the current time (in seconds)
        self.start_time = time.time()
        # set the left time to the complete time
        self.time_left = ctime
        # set the process time to 0
        self.time_process = 0
        # ini a lock
        self.lock = Lock()

        self.signal = signal
        # start the thread
        self.start()

    def stop(self):
        """
        Stops the current process.
        """
        self.lock.acquire()
        self.ctime = time.time() - self.start_time
        self.lock.release()

    def run(self):
        """
        Thread-run method to update the times
        """
        self.signal.update_label(2)
        # if the left time is greater than 0
        while self.time_left > 0:
            # lock the interactions
            self.lock.acquire()
            # calculate the process time
            self.time_process = time.time() - self.start_time
            # calculate the left time
            self.time_left = self.ctime - self.time_process
            # release the lock
            self.lock.release()
            # wait
            time.sleep(0.1)
        # after the time is over
        # lock the interactions
        self.lock.acquire()
        # set the process time to the complete time
        self.time_process = self.ctime
        # set the left time to 0
        self.time_left = 0
        # release the lock
        self.lock.release()
        self.signal.update_label(0)

    def get_time_left(self):
        """
        Returns the left time.

        :returns: the left time
        :rtype: float
        """
        # set the return value 0 as default
        time_left = 0
        try:
            # lock the interactions
            self.lock.acquire()
            # store the left time in local variable
            time_left = self.time_left
            # release the lock
            self.lock.release()
        except RuntimeError:
            print('lock problems in get_time_left')
        # return the left time
        return time_left

    def get_time_process(self):
        """
        Returns the time since the start in seconds.

        :returns: time since the start
        :rtype: float
        """
        # lock the interactions
        self.lock.acquire()
        # store the time in a local variable
        time_process = self.time_process
        # release the lock
        self.lock.release()
        # return the time
        return time_process

    def get_time_left_percent(self):
        """
        Returns the rest of the time until the process is finished in percent.

        :returns: the time until the process is finished
        :rtype: float
        """
        # lock interactions
        self.lock.acquire()
        # store the left time in a local variable
        time_left = self.time_left
        # calculate the percent of the left time
        if self.ctime == 0:
            time_left = 0
        else:
            time_left = float(time_left) / self.ctime
        time_left = 1 - time_left
        # release the lock
        self.lock.release()
        # if the percent is greater than 1
        if time_left > 1:
            # set the percent to one
            time_left = 1
        # multiply by 100 to get a proper percent value
        time_left *= 100
        # return the percent value
        return time_left


class CameraStatus:
    temperature = 99
    exposure = False
    readout = False
    exposure_process = None
    readout_process = None
    status_id = 0
    stopped = False
    image_information = None
    signal = None
    """
    Camera status stores all helpful information about the interface and the 
    settings for the interface. The advantage of this is that you don't need to 
    communicate with the interface every time.
    """

    def __init__(self):
        self.status_labels = ['ready', 'preparing', 'exposure', 'readout',
                              'disconnect']
        self.header = Header()
        self.lock = Lock()
        # self.signal = LabelSignalInt()
        # self.signal.labelUpdated.connect(self.__exposure_done__)

    def get_target_name(self):
        """
        Returns the current target name.

        :returns: the target name or an empty string if there is no target set.
        :rtype: str
        """
        if self.image_information is not None:
            return self.image_information.name
        else:
            return ''

    def set_temperature(self, temperature):
        """
        Sets a new temperature for the status information

        :param temperature: the ccd temperature of the interface
        :type temperature: float
        """
        # lock the interactions
        self.lock.acquire()
        # store the temperature in the class variable
        self.temperature = temperature
        # release the lock
        self.lock.release()

    def get_temperature(self):
        """
        Returns the last stored temperature of the ccd-chip

        :returns: the last ccd-temperature
        :rtype: float
        """
        # lock the interactions
        self.lock.acquire()
        # store the temperature in a local variable
        temperature = self.temperature
        # release the lock
        self.lock.release()
        # return the temperature
        return temperature

    def get_image_information(self):
        """
        Returns the image information object
        """
        return self.image_information

    def get_image_infos(self):
        if self.image_information is not None:
            infos = {'filter_name': self.image_information.filter_name,
                     'exposure_time': self.image_information.expo_time,
                     'image_type': self.image_information.image_type,
                     'number': self.image_information.number,
                     'subframe_start': self.image_information.get_subframe__start_string(),
                     'subframe_size': self.image_information.get_subframe__size_string(),
                     'binning_x': self.image_information.bin_x,
                     'binning_y': self.image_information.bin_y}
        else:
            infos = {'filter_name': 'B',
                     'exposure_time': 0,
                     'image_type': 'science',
                     'number': 0,
                     'subframe_start': '0000:0000',
                     'subframe_size': '4096:4096',
                     'binning_x': 1,
                     'binning_y': 1}
        return infos

    def set_image_information(self, info):
        self.image_information = info

    def start_exposure_time(self, exposure_time):
        """
        Starts the time measurements of the exposure.

        :param exposure_time: The exposure time
        :type exposure_time: float
        """
        # lock the interactions
        self.lock.acquire()
        # set the status to exposure (status id=2)
        self.status_id = 2
        # self.signal.update_label(0)
        # start the time process for the exposure
        self.exposure_process = Process(exposure_time)
        # set the exposure key to true (can replace by the status id)
        self.exposure = True
        # release the lock
        self.lock.release()

    def start_readout(self, readout_time):
        self.lock.acquire()
        self.status_id = 3
        self.readout_process = Process(readout_time, self.signal)
        self.readout = True
        self.lock.release()

    def __exposure_done__(self, value):
        pass

    def exposure_in_process(self):
        """
        Asks if an exposure is currently in process

        :returns: True if a exposure is in process, else False
        :rtype: bool
        """
        return self.exposure

    def exposure_status(self):
        """
        Returns the exposure status.

        :returns:
            the current exposure status with the time since the start and the
            percent value or 0, 0 if there is no exposure process at the moment.
        :rtype: list
        """
        try:
            if self.exposure:
                return self.exposure_process.get_time_left(), self.exposure_process.get_time_left_percent()
            else:
                if self.readout:
                    return 0, 100
                return 0, 0
        except AttributeError:
            return 0, 0

    def readout_status(self):
        """
        Returns the readout status.

        :returns:
            the current readout status with the time since the start and the
            percent value or 0, 0 if there is no readout process at the moment.
        :rtype: list
        """
        if self.readout:
            return self.readout_process.get_time_process(), self.readout_process.get_time_left_percent()
        else:
            return 0, 0

    def readout_in_process(self):
        """
        Asks if a readout is currently in process

        :returns: True if a readout is in process, else False
        :rtype: bool
        """
        return self.readout

    def get_status_id(self):
        """
        Returns the current status id of the interface.

        :returns: the status id
        :rtype: int
        """
        return self.status_id

    def get_status_label(self):
        """
        Returns the label of the current status

        :returns:
            'ready' if the interface is ready, 'preparing' if the interface prepares
            a new exposure, 'exposure' if an exposure is in process,
            'readout' if an image is readout of the interface or 'disconnect' if
            the interface is disconnected.
        :rtype: str
        """
        return self.status_labels[self.status_id]

    def get_header(self):
        """
        Returns the header of the current image.
        """
        return self.header

    def reset(self):
        """
        Resets the counters of exposure and readout and set the status id back
        to 0 (ready).
        """
        self.exposure = False
        self.readout = False
        self.status_id = 0

    def stop_exposure(self):
        """
        Stops the current exposure counter. Also the exposure time is changed
        to the time since the start.
        """
        self.stopped = True
        if self.exposure:
            self.exposure_process.stop()

    def is_stopped(self):
        """
        Ask if the the current exposure is stopped.
        :return: True if the exposure is stopped, else False
        :rtype: bool
        """
        return self.stopped

    def abort_exposure(self):
        """
        Stops the current exposure counter. Also the exposure time is changed
        to the time since the start.
        """
        self.stopped = True
        if self.exposure:
            self.exposure_process.stop()
        if self.readout:
            self.readout_process.stop()

    def was_stopped(self):
        """
                Checks if the last exposure was stopped or aborted.

                :returns: True if the last exposure was stopped, else False
                :rtype: bool
                """
        st = self.stopped
        return st

    def reset_stopped(self):
        """
                Checks if the last exposure was stopped or aborted.

                :returns: True if the last exposure was stopped, else False
                :rtype: bool
                """
        self.stopped = False
