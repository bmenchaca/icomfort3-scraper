from distutils.core import setup
setup(
    name = 'icomfort3',
    packages = ['icomfort3'],
    install_requires=[
        'requests',
        'lxml',
    ],
    version = '0.1',
    description = 'A library to access your Lennox S30, M30, and E30 thermostats by scraping https://lennoxicomfort.com',
    author = 'Ben Menchaca',
    author_email = 'ben.menchaca@gmail.com',
    url = 'https://github.com/bmenchaca/icomfort3-scraper',
    download_url = 'https://github.com/bmenchaca/icomfort3-scraper/archive/0.0.1.tar.gz',
    keywords = [ 'Lennox', 'scraper', 'thermostat' ],
    classifiers = [],
)
