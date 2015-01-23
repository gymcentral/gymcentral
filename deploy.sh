#!/bin/bash
#if it false swith to true to perform tests
sed -i.backup -e 's/DEBUG = False/DEBUG = True/g' cfg.py
echo "Running test cases, see 'result.test' file for the results"
./run_nosetest.sh > result.test 2>&1
#swtch to false for the production
sed -i.backup -e 's/DEBUG = True/DEBUG = False/g' cfg.py
if grep -q "OK" result.test; then
    echo "Tests: ok"
    echo "Updating server"
#    appcfg.py update .
else
    echo "Error in test cases, cannot update"
fi
#switch back to true since we are local, so we use tests here.
sed -i.backup -e 's/DEBUG = False/DEBUG = True/g' cfg.py
