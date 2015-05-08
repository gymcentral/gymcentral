#!/bin/bash
#if it false swith to true to perform tests
sed -i.backup -e's/DEBUG = False/DEBUG = True/g' cfg.py
if [ "$1" != "FORCE" ]; then
    echo "Running test cases, see 'result.test' file for the results"
    ./run_nosetest.sh > result.test 2>&1
    #swtch to false for the production
    sed -i.backup -e 's/DEBUG = True/DEBUG = False/g' cfg.py
else
    echo "Skipping test"
    echo "OK" > result.test
fi
if grep -q "OK" result.test; then
    echo "Tests: OK"
    echo ""
#    echo "Creating documentation"
#    ./build_doc.sh >> doc_build.temp
#    if grep -q "build succeeded." doc_build.temp; then
        echo "Documentation: OK"
        echo ""
        echo "Updating server"
        appcfg.py update . --oauth2
#    else
#        echo "Error during the building of documentation"
#    fi
else
    echo "Error in test cases, cannot update"
fi
#switch back to true since we are local, so we use tests here.
sed -i.backup -e 's/DEBUG = False/DEBUG = True/g' cfg.py
