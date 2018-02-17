# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 14:34:41 2016

@author: Patrick Rauer
"""
import os


HEADER_PATH = './header_names.dat'


class Header:
    def __init__(self):
        """
        THis cass provides the interface for the names of the header items of the fits images.
        """
        self.exposure_time = read_in('exposure time')
        self.date_obs = read_in('date of the observation(UTC)')
        self.date_cet = read_in('date of the observation(CET)')
        self.jd = read_in('date of the observation(JD)')
        self.observer = read_in('observer')
        self.object = read_in('target name')
        self.RA = read_in('target RA')
        self.DEC = read_in('target DEC')
        self.telescope_ra = read_in('telescope RA')
        self.telescope_dec = read_in('telescope DEC')
        self.image_type = read_in('image type')
        self.filter_name = read_in('name of the filter')
        self.subframe_bounds = read_in('subframe bounds')
        self.binning = read_in('binning')
        self.bin_y = read_in('y-binning')
        self.bin_x = read_in('x-binning')
        self.subframe_size_x = read_in('size of the subframe in x-direction')
        self.subframe_size_y = read_in('size of the subframe in y-direction')
        self.azimuth = read_in('azimuth of the telescope')
        self.altitude = read_in('altitude of the telescope')
        self.hourangle = read_in('hourangle')
        self.ccd_temp = read_in('current ccd-temperature')
        self.ccd_temp_set = read_in('set ccd-temperature')
        self.weather_date = read_in('date of the weather data')
        self.temp_dome = read_in('temperature inside the dome')
        self.dew_dome = read_in('dewpoint inside the dome')
        self.hum_dome = read_in('humidity inside the dome')
        self.temp_schm = read_in('temperature of the schmidt-plate')
        self.heating = read_in('heating')
        self.temp_mount = read_in('temperature of the mount')
        self.heat_dew = read_in('heating dewcap')
        self.hum_dew = read_in('humidity at the dewcap')
        self.temp_out = read_in('temperature at the weather station')
        self.hum_out = read_in('humidity at the weather station')
        
        self.lat = read_in('latitude of the telescope')
        self.lon = read_in('longitude of the telescope')
        self.telescope = read_in('kind of telescope')
        self.focal = read_in('focal length')
        self.aperature = read_in('aperature diameter')
        self.instrument = read_in('instrument name')

    def to_list(self):
        """
        Returns all header information as a list back
        :return: The information of the header items
        :rtype: list
        """
        variables = []
        for attr in dir(Header()):
            if not callable(getattr(Header(), attr)):
                variables.append(getattr(self, attr))
        return variables


def read_in(name):
    """
    Reads a item of the header item file.
    :param name: The name of the header item
    :type name: str
    :return: The value of the header item in the header item file.
    :rtype: str
    """

    if not os.path.exists(HEADER_PATH):
        return ''
    f = open(HEADER_PATH)
    r = ''
    for line in f:
        if name in line and not ('#' in line):
            r = line.split(':')[-1].split(' ')[-1].split('\n')[0]
            break
    return r
