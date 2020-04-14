from setuptools import setup, find_packages

setup(
    name='is_orchestrator',
    version='0.0.1',
    description='',
    url='http://github.com/wagnercotta/is-orchestrator',
    author='labviros',
    license='MIT',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': ['is-orchestrator=is_orchestrator.service:main',],
    },
    zip_safe=False,
    install_requires=[
        'is-wire==1.2.0',
        'is-msgs==1.1.11',
        'kubernetes==11.0.0'
    ],
)
