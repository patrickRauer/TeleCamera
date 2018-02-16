try:
    from comtypes import COMError
except ImportError:
    COMError = AttributeError

from .Driver import Driver


class FilterWheelDriver(Driver):
    """
    The filter wheel driver class is the interface between the python program
    and the ASCOM filter wheel driver. All the methods are wrapped to a python
    interface.
    """

    def __init__(self, driver_name):
        # init the super class Driver
        Driver.__init__(self, 'Filter wheel', driver_name)
        # creates a dict with the filter names and the corresponding position of
        # the filter wheel
        self.filter_names = {'U': 0, 'B': 1, 'V': 2, 'R': 3, 'I': 4, 'Clear': 5, 'None': 6}
        self.filter_ids = ['U', 'B', 'V', 'R', 'I', 'Clear', 'None']

    def get_corresponding_filter_nr(self, name):
        """
        Returns the nr of the filter with this name.

        :param name: Name of the filter
        :type name: str
        :returns: the number of the filter in the filter wheel
        :rtype: int
        """
        return self.filter_names[name]

    def set_filter(self, filter_nr):
        """
        Sets a new filter with the filter id.

        :param filter_nr: the filter number
        :type filter_nr: int

        :returns: True if the new filter is set, else False
        :rtype: bool
        """
        # create the default return value
        rvalue = False
        # try to set the new filter
        try:
            # lock the filter wheel driver
            self.driver_lock.acquire()
            # set the new filter
            self.driver.Position = filter_nr
            # set the return value to True
            rvalue = True
        # except a filter wheel error
        except COMError:
            # create the error message
            self.__create_error_message__('Can\'t set a new filter ' +
                                          '(filter id:' + str(filter_nr) + ')')
            # set the return value back to False
            rvalue = False
        # do anyways
        finally:
            # release the filter wheel driver lock
            self.driver_lock.release()
            # return the return value
            return rvalue

    def set_filter_by_name(self, name):
        """
        Sets a new filter by his name.

        :param name: The name of the filter
        :type name: str
        :returns: True is the new filter is set, else False
        :rtype: bool
        """
        # if the name of the filter is one of the names of filter
        # of the filter wheel
        if name in self.filter_names.keys():
            # Set the filter by his position
            rvalue = self.set_filter(self.filter_names[name])
        # if the filter name is not known
        else:
            # create an error message
            self.__create_error_message__('Unknown filter name')
            # set the return value back to False
            rvalue = False
        # return the return value
        return rvalue

    def get_filter_nr(self):
        """
        Returns the current filter position.

        :returns:
            the filter wheel position if the filter wheel positions is
            readable, else -1
        :rtype: int
        """
        # creates a default return value
        rvalue = -1
        # try to read the filter wheel position
        try:
            # lock the filter wheel driver
            self.driver_lock.acquire()
            # reads the filter wheel position
            rvalue = self.driver.Position
        # except a filter wheel error
        except COMError:
            # create the error message
            self.__create_error_message__('Can\'t read the filter wheel' +
                                          'position')
            # set the return value back to -1
            rvalue = -1
        # do anyways
        finally:
            # release the filter wheel lock
            self.driver_lock.release()
            # return the return value
            return rvalue

    def get_filter_name(self):
        """
        Returns the name of the current filter.

        :returns: name of the filter
        :rtype: str
        """
        # creates the default return value
        rvalue = 'moving'
        # reads the current filter wheel position
        filterwheel_position = self.get_filter_nr()
        # if the filter wheel position is not -1
        if filterwheel_position != -1:
            # set the return value with the key name at the position
            rvalue = self.filter_ids[filterwheel_position]
        # return the return value
        return rvalue

    def is_ready(self):
        """
        Asks if the filter wheel is ready.

        :returns: The number of the filter or -1 if the filter wheel is moving.
        :rtype: int
        """
        if self.get_filter_nr() != -1:
            return True
        else:
            return False
