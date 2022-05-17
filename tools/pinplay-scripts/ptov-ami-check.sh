#!/bin/bash
ls $1.ami $1.ptov
for paby4 in `
cat $1.ptov | sed '/^/s//0x/g' |  gawk '
    {printf "%x\n",strtonum($1)/4}
    '
    `
do
   paby=`echo $paby4 | sed '/^/s//0x/' | gawk '{printf "%x\n",strtonum($1)*4}'`
   echo -n " $paby/4 --> $paby4  : "
   ami=`grep origin $1.ami | grep  " $paby4$"`
   if [[ -z $ami ]]
   then
    echo "NOT FOUND"
   else
    echo $ami
   fi
done
exit

echo "================"
for paby in `
cat $1.ami | grep origin | gawk '{printf "0x%s\n",$2}' | gawk '{printf "%x\n",strtonum($1)*4}'`
do
   paby4=`echo $paby | sed '/^/s//0x/' | gawk '{printf "%x\n",strtonum($1)*4}'`
   echo -n " $paby4*4 --> $paby  : "
   ptov=`grep -e "^$paby" $1.ptov`
   if [[ -z $ptov ]]
   then
    echo "NOT FOUND"
   else
    echo $ptov
   fi
done
