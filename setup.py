from setuptools import setup  # noqa

setup(name='xmlmapper',
      version='0.1.0',
      description='A library for modeling XML',
      long_description=open('README.md').read(),
      author='Solly Ross',
      author_email='sross@redhat.com',
      license='ISC',
      url='https://github.com/directman12/py-xmlmapper',
      packages=['xmlmapper', 'xmlmapper.tests'],
      install_requires=['lxml', 'six'],
      keywords='xml',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries',
          'Topic :: Text Processing :: Markup :: XML',
          'License :: OSI Approved :: ISC License (ISCL)',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7'
      ])
