from threading import Thread
import os


class ImageLog:
    """
    Class to create/interact with the log-file for images.
    """

    def __init__(self, signal=None):
        self.path = './image_log.txt'
        self.last_target = ''
        if not os.path.exists(self.path):
            self.f = open(self.path, 'a')
            self.f.write('# Date; Observer; image name; telescope RA; telescope DEC; target RA; ' +
                         'target DEC; image_type; exposure_time; filter; subframe; binning')
            self.f.flush()
        else:
            self.f = open(self.path, 'a')
        self.is_open = True
        self.signal = signal

    def close(self):
        self.f.close()
        self.is_open = False

    def open(self):
        self.f = open(self.path, 'a')
        self.is_open = True

    def add(self, date, observer, target, telescope_ra, telescope_dec,
            target_ra, target_dec, image_type, exposure_time, filt,
            subframe, binning, chip_temp, dome_temp, out_temp, dome_hum, out_hum,
            readout_time, path):
        """

        :param date: Date of the observation
        :type date: :class:`datetime.datetime`
        :param observer: The name of the observer
        :type observer: str
        :param target: Name of the target
        :type target: str
        :param telescope_ra: RA of the telescope
        :type telescope_ra: str
        :param telescope_dec: DEC of the telescope
        :type telescope_dec: str
        :param target_ra: RA of the target
        :type target_ra: str
        :param target_dec: DEC of the target
        :type target_dec: str
        :param image_type: Type of the image (eg. 'science' or 'flat')
        :type image_type: str
        :param exposure_time: The exposure of the image
        :type exposure_time: str
        :param filt: Name of the filter
        :type filt: str
        :param subframe: The bounds of the sub-frame
        :type subframe: str
        :param binning: The binning in X and Y direction
        :type binning: str
        :param chip_temp: The temperature of the interface chip
        :type chip_temp: str
        :param dome_temp: The temperature inside the dome
        :type dome_temp: str
        :param out_temp: The temperature outside of the dome
        :type out_temp: str
        :param dome_hum: The humidity inside the dome
        :type dome_hum: str
        :param out_hum: The humidity outside of the dome
        :type out_hum: str
        :param readout_time: The needed time to read the image
        :type readout_time: float
        :param path: The path to the image
        :type path: str

        Adds a new entry in the log file
        """
        th = Thread(target=self.__add__, args=(date, observer, target, telescope_ra, telescope_dec,
                                               target_ra, target_dec, image_type, exposure_time, filt,
                                               subframe, binning, chip_temp, dome_temp, out_temp, dome_hum, out_hum,
                                               readout_time,
                                               path,))
        th.start()

    def __add__(self, date, observer, target, telescope_ra, telescope_dec,
                target_ra, target_dec, image_type, exposure_time, filt,
                sub_frame, binning, chip_temp, dome_temp, out_temp, dome_hum, out_hum,
                readout_time, path):
        infos = {'date': date, 'observer': observer, 'target': target, 'telescope_ra': telescope_ra,
                 'telescope_dec': telescope_dec, 'target_ra': target_ra,
                 'target_dec': target_dec, 'type': image_type, 'exposure_time': exposure_time,
                 'filter': filt, 'subframe': sub_frame, 'binning': binning,
                 'chip_temp': chip_temp, 'dome_temp': dome_temp, 'out_temp': out_temp,
                 'dome_hum': dome_hum, 'out_hum': out_hum, 'readout_time': readout_time,
                 'path': path}
        if self.signal is not None:
            self.last_target = target
            self.signal.update_information(infos)
        if self.is_open:
            string = date.strftime("%Y-%m-%d %H:%M:%S")
            string += ';' + observer + ';' + target + ';' + telescope_ra + ';' + telescope_dec
            string += ';' + target_ra + ';' + target_dec + ';' + image_type
            string += ';' + exposure_time + ';' + filt + ';' + sub_frame + ';' + binning
            string += ';' + chip_temp + ';' + dome_temp + ';' + out_temp + ';'
            string += ';' + dome_hum + ';' + out_hum
            self.f.write(string + '\n')
            self.f.flush()
