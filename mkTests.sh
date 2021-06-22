while true; do
        echo "Which test folder (ConfTests or ServerTest) would you like to input your tests in: "
        read foldername 

        if [[ $foldername != "ConfTests" ]] && [[ $foldername != "ServerTest" ]]; then
                echo Goodbye!
                break
        fi
        
        printf "\nWhat is the name of the test folder you would like to create?\n"

        while true; do
                read testfolder

                if [[ "$testfolder" == "" ]]; then
                        break

                else    
                        clear

                        folder=tests/$foldername/$testfolder
                        mkdir $folder

                        path=$folder/$testfolder

                        touch $testfolder.cfg $testfolder.out 
                        mv $testfolder.cfg $path.cfg && mv $testfolder.out $path.out

                        if [[ $foldername == "ServerTest" ]]; then
                                touch $testfolder.outH $testfolder.curl $testfolder.curlH
                                mv $testfolder.outH $path.outH && mv $testfolder.curl $path.curl && mv $testfolder.curlH $path.curlH
                        fi

                        printf "\nSuccessfully created test $testfolder in $foldername\n\n"

                fi
        done

done
