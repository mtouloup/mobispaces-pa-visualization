##Libraries
from setuptools import setup
import os

# Read requirements.txt file
curDir = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(curDir, 'requirements.txt')) as file:
    requirements = file.read().splitlines()
	
	
setup(
   name='MobiSpaces Privacy Aware Visualization',
   version='1.0',
   description='A python application for xxxxxxxxxxxxxxxx',
   author='Marios Touloupos, Evgenia Kapassa',
   author_email='{touloupos,evgeniakapassa}@gmail.com',
   package_dir={'': '/'},  
   zip_safe=False,
   install_requires=requirements,
)