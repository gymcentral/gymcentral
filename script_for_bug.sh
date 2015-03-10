#!/bin/bash
git clone https://github.com/gymcentral/gymcentral.git
cd gymcentral
mkvirtualenv gymcentraltest
workon gymcentraltest
pip install -r requirements.txt
git submodule init
git submodule update
curl https://gist.githubusercontent.com/esseti/7f3287166b662bbc470e/raw/9983b38df6bfece0362df1172e4700b3791f3fb1/gistfile1.txt -o cfg.py
# this is unitest, and all the test passes

#this is nose and the first passes
nosetests --with-gae tests/test.py:APITestCases.test_that_pass
#this fails
nosetests --with-gae tests/test.py:APITestCases.test_that_fails
