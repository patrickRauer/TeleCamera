class CreateObject:
    ImageReady = False
    ImageArray = None
    CameraXSize = 2024
    CameraYSize = 2024
    StartX = 0
    StartY = 0
    NumX = 2024
    NumY = 2024
    CanAsymmetricBin = True
    BinX = 1
    BinY = 1
    CCDTemperature = 0
    Position = -1
    CoolerPower = 0
    name = ''

    def __init__(self, name):
        self.name = name

    def AbortExposure(self):
        pass

    def StopExposure(self):
        pass

    def StartExposure(self, time, open_shutter):
        pass

    class Choose:
        name = ''

        def __init__(self, name):
            self.name = name


class COMError:
    def __init__(self):
        pass