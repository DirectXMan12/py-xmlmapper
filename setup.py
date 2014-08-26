from setuptools import setup  # noqa

setup(name='xmlmapper',
      version='0.1.0',
      description='A library for modeling XML',
      author='Solly Ross',
      author_email='sross@redhat.com',
      packages=['xmlmapper', 'xmlmapper.tests'],
      install_requires=['lxml', 'six'])
