#!/bin/bash
#add to cover_package the file to check the coverage
nosetests --with-gae --with-coverage --cover-erase --cover-package=models,api_db_utils,main
nosetests --with-gae --with-coverage --cover-erase --cover-package=gymcentral
