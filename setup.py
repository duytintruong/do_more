from distutils.core import setup
setup(
    name='do_more',
    packages=['do_more'],
    version='0.1.0',
    description='A library enhancing pydoit features.',
    author='Duy Tin Truong',
    author_email='',
    url='https://github.com/duytintruong/do_more',
    download_url='https://github.com/duytintruong/do_more/archive/0.1.0.tar.gz',
    keywords=['pipeline', 'data', 'doit'],
    classifiers=[],
    install_requires=[
        'doit>=0.31.1',
    ],
)
