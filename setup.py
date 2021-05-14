from setuptools import setup

setup(name='pipeline',
      version='0.1',
      description='Toolchain to clean time series data',
      url='https://github.com/JakobSpahn/time_series_pipeline',
      author='Jakob Spahn, ',
      author_email='jakob@craalse.de',
      license='GPL-3.0',
      packages=['pipeline'],
      install_requires=[
          'pandas',
          'numpy',
          'matplotlib',
          'python-dateutil',
          'scipy',
          'sklearn',
      ],
      zip_safe=False)