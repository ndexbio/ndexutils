"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
import os
import re


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open(os.path.join('ndexutil', '__init__.py')) as ver_file:
    for line in ver_file:
        if line.startswith('__version__'):
            version=re.sub("'", "", line[line.index("'"):])


setup(
    name='ndexutil',
    version=version,
    description='Unsupported NDEx utilities',
    long_description=readme + '\n\n' + history,

    # The project's main homepage.
    url='https://github.com/ndexbio/ndexutils',

    # Author details
    author='The NDEx Project',
    author_email='contact@ndexbio.org',

    # Choose your license
    license='BSD',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Natural Language :: English',
        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6'
    ],

    # What does your project relate to?
    keywords='network analysis biology',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=[]),
    data_files=[('schema', ['ndexutil/tsv/loading_plan_schema.json'])],
    install_requires = [
        'ndex2>=3.1.0a1,<=4.0.0',
        'requests',
        'requests_toolbelt',
        'networkx',
        'urllib3>=1.16',
        'pandas',
        'mygene',
        'enum34',
        'pandas',
        'enum; python_version == "2.6" or python_version=="2.7"',
        'jsonschema',
        'biothings_client'
    ],
    test_suite='tests',
    test_requires=[
        'requests-mock',
        'mock'
    ],
    include_package_data=True
)



