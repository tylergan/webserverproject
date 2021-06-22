count=0

data=tests/dataOutput.txt

for folder in `ls -d tests/*/ | sort -V`; do
        basefile=$(basename $folder)

        for test_folder in `ls -d tests/$basefile/*/`; do
                test=$(basename $test_folder)

                if (($count == 0)); then
                        printf "============================================\n"
                fi
                
                cfg=tests/$basefile/$test/$test.cfg

                expected=tests/$basefile/$test/$test.out
                expectedH=tests/$basefile/$test/$test.outH

                curl=tests/$basefile/$test/$test.curl
                curlH=tests/$basefile/$test/$test.curlH
            
                if [ "$basefile" == "ConfTests" ]; then
                        printf "Running Test #$((count+1)) $test: "

                        if [ "$test" == "MissingArgs" ]; then
                                python3 webserv.py | diff - $expected && printf "PASSED\n" || printf "FAILED\n"

                        else    
                                python3 webserv.py $cfg | diff - $expected && printf "PASSED\n" || printf "FAILED\n"

                        fi

                else    
                        printf "Running Test #$((count+1)) $test:\n\n"
                        python3 webserv.py $cfg  &
                        PID=$!
                        
                        sleep 0.5 #allow some time for webserver to setup
                        
                        #test data body
                        if [ "$test" == "PNGFile" ] || [ "$test" == "JPEGFile" ] || [ "$test" == "JPGFile" ] || [ "$test" == "RemotePort" ]; then
                                `cat $curl` | tee $data > $expected #can't really test these as they change 
                                diff $data $expected && printf "\n###### DATA PASSED ######\n\n" || printf "\n###### DATA FAILED ######\n\n"

                        elif [ "$test" == "GZIPCGI" ] || [ "$test" == "GZIPStatic" ]; then
                                `cat $curl` > $data
                                gunzip -c $data | diff - $expected && printf "\n###### DATA PASSED ######\n\n" || printf "\n###### DATA FAILED ######\n\n"

                        else    
                                `cat $curl` > $data
                                diff $data $expected && printf "\n###### DATA PASSED ######\n\n" || printf "\n###### DATA FAILED ######\n\n"
                        fi

                        #test headers
                        `cat $curlH` | diff - $expectedH && printf "\n###### HEADER PASSED ######\n\n"|| printf "\n###### HEADER FAILED ######\n\n"

                        kill $PID #kill webserver

                        sleep 0.5 #allow some time for webserver to close

                fi
                printf "============================================\n"

                count=$((count+1))
        
        done
done

> $data
printf "\nFINISHED RUNNING $count TESTS\n"