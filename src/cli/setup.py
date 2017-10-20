from setuptools import setup

setup(
    name="hydroengine",
    packages=['hydroengine'],
    version="0.0.2",
    install_requires=['requests>=2.12'],
    entry_points={
        'console_scripts': [
            'hydroengine = hydroengine.hydroengine:main'
        ]
    },
    author="Gennadii Donchyts",
    author_email="gennadiy.donchyts@gmail.com",
    description="A small script to help downloading input data for hydrological models",
    license="MIT",
    keywords="hydrology data gis ",
    url="https://github.com/Deltares/hydro-engine"   
)