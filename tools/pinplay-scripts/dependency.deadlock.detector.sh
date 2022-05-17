#!/bin/bash
ERROR()
{
  echo "Usage : $0 trace-basename" 
  exit
}

if [ ! -f $1.race.0 ]; then
    echo "Input file ($1.race.0) does not exist!" 
    ERROR
fi

count=`ls $1.race.* | wc -l`
echo "$count threads"

nfields=`head -1 $1.race.0 | awk '{print NF}'`
let t=0
for f in `ls $1.race.*`
do 
    echo $t $f
    let tn=t+1
    while [ $tn -lt $count ]
    do
        echo "  checking $t and $tn"
        if  [ $nfields -eq 3 ];  then
            grep " $tn " $1.race.$t | awk -v t1=$t -v t2=$tn '{print t1 " " $1 " " $2 " " $3}' | sort > dep.$t.$tn
            grep " $t " $1.race.$tn | awk -v t1=$t -v t2=$tn '{print t1 " " $3 " " t2 " " $1}'| sort  > dep.$tn.$t
        else
# This is for logs created with -pinplay:debug_race
            grep " $tn " $1.race.$t | awk -v t1=$t -v t2=$tn '{print t1 " " $4 " " $5 " " $6}' | sort > dep.$t.$tn
            grep " $t " $1.race.$tn | awk -v t1=$t -v t2=$tn '{print t1 " " $6 " " t2 " " $4}'| sort  > dep.$tn.$t
        fi
        comm -1 -2 dep.$t.$tn dep.$tn.$t | awk '{print "      deadlock "$0}'
        rm dep.$t.$tn dep.$tn.$t
        let tn=tn+1
    done
    let t=t+1
done
