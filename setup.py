from setuptools import setup, find_packages
SERVICE_NAME = 'harp-daemon'
SERVICE_NAME_NORMALIZED = SERVICE_NAME.replace('-', '_')

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


tests_require = [],

setup(
    name=SERVICE_NAME,
    version='0.0.1',
    description=SERVICE_NAME,
    url='',
    author='Mykola K.',
    author_email='the.harpia.io@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='',
    packages=find_packages(),
    install_requires=requirements,
    tests_require=tests_require,
    package_data={'schemas': ['*.json']},
    entry_points={
        'console_scripts': [f'{SERVICE_NAME} = {SERVICE_NAME_NORMALIZED}.__main__:main']
    },
    zip_safe=False,
    include_package_data=True,
    cmdclass={},
    data_files=[]
)
