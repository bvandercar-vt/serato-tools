from setuptools import find_packages, setup

setup(
   name='serato_tags',
   version='1.0',
   description='Serato track metadata tags',
   author='TODO',
   author_email='TODO',
   packages=["scripts"],
   install_requires=['mutagen']
)