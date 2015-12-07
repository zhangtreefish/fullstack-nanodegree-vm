#!/usr/bin/python
from wsgiref.handlers import CGIHandler
from finalProject import app

CGIHandler().run(app)
