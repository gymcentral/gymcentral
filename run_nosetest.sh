#!/bin/bash
#add to cover_package the file to check the coverage
nosetests --with-gae --without-sandbox --no-path-adjustment --gae-application=. --with-coverage --cover-package=models,api_db_utils,gymcentral


