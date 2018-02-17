from setuptools import setup

setup(
    name='fpvtracker',
    version='1.0',
    description='Configuration Tool for FPV Tracker',
    author='Diez B. Roggisch',
    author_email='deets@web.de',
    license='MIT',
    packages=['fpvtracker'],
    entry_points = {
        'console_scripts': [
            'fpv-tracker=fpvtracker:main'
        ],
    }
)
