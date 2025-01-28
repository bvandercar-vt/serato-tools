from setuptools import find_packages, setup

setup(
   name='serato-tags',
   version='1.0',
   description='Serato track metadata tags',
   author='TODO',
   author_email='TODO',
   packages=find_packages(where="scripts"),
   package_dir={'serato-tags':'scripts'},
   install_requires=['mutagen']
)