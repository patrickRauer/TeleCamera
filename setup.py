from setuptools import setup

setup(
    name='Camera',
    version='0.8',
    packages=['', 'Camera', 'Camera.meta', 'Camera.drivers', 'Camera.dummies', 'Camera.interface'],
    url='',
    license='GPL',
    author='Patrick Rauer',
    author_email='j.p.rauer@sron.nl',
    description='Camera interface with the usage of ASCOM drivers',
    install_requires=['astropy', 'pytz', 'comtypes', 'numpy']
)
