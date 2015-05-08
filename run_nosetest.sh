#!/bin/bash
#add to cover_package the file to check the coverage
#nosetests tests/test.py --with-gae --with-coverage --cover-erase --cover-branches --cover-inclusive --cover-package=../ --cover-html
nosetests tests/test.py --with-gae --gae-application=app.yaml --cover-branches --with-coverage  --cover-package=.
rm # --cover-package=models,api_db_utils,api
#nosetests --with-gae --with-coverage --cover-erase --cover-package=gymcentral
