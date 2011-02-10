from setuptools import setup
setup(
    author="Anthony Long",
    author_email="antlong@gmail.com",
    version="0.1",
    description="Growl notifications for pytest results.",
    name="pytest-growl",
    keywords="pytest, pytest-, growl, py.test",
    packages=['pytest_growl'],
    entry_points={'pytest11': ['pyest_growl = pytest_growl.growl', ]},)
