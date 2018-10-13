from setuptools import setup

with open('requirements.txt') as f:
    requires = f.readlines()

with open('README.md') as f:
    readme = f.read()

setup(
    name='bilibiliupload',
    version='0.1.0',
    packages=['bilibiliupload'],
    url='https://github.com/comwrg/bilibiliupload',
    install_requires=requires,
    license='MIT',
    author='comwrg',
    author_email='xcomwrg@gmail.com',
    description='Upload video to bilibili under command-line interface',
    long_description=readme,
    keywords=['bilibili', 'upload'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
