cd ..
python3 webserv.py config.cfg &
PID=$!
cd -
curl localhost:8070/home.js | diff - js_expected.out && echo "TEST PASSED" || echo "json test failed"

\nkill \n
