#!/bin/bash
ERROR()
{
  echo "Usage : $0 trace-basename virtual-address-in-hex"
  exit
}

if  [ $# -ne 2 ];  then
    echo "args " $#
    ERROR
fi

if [ ! -f $1.ami ]; then
    echo "Input file ($1.ami) does not exist!" 
    ERROR
fi

if [ ! -f $1.ptov ]; then
    echo "Input file ($1.ptov) does not exist!" 
    ERROR
fi


va=`echo $2 | gawk '{printf "%x\n", lshift(rshift(strtonum($1),12),12) }'`
echo "va_raw = $2"
echo "va-page = $va"


ls $1.ami 
for paby4 in `
cat $1.ptov | sed '/^/s//0x/g' |  gawk -v VA=$va '
    {if($2==VA) printf "%x\n",strtonum($1)/4}
    '
    `
do
   paby=`echo $paby4 | sed '/^/s//0x/' | gawk '{printf "%x\n",strtonum($1)*4}'`
   echo -n "(VA)$va --> (PA)$paby/4 --> $paby4  : "
   ami=`grep origin $1.ami | grep  " $paby4"`
   if [[ -z $ami ]]
   then
    echo "NOT FOUND"
   else
    echo $ami
    cat $1.ami | gawk -v ADDR=$paby4 '
        BEGIN {flag=0; line=0; col=0}
        /origin/ {if ($2==ADDR) 
                    flag=1;
                  else 
                    flag = 0;}
       /0x/      {if(flag==1)
                    {
                        word[line] = $0;
                        byte0[line] = and(strtonum($0),0xff);
                        byte1[line] = and(strtonum($0),0xff00);
                        byte2[line] = and(strtonum($0),0xff0000);
                        byte3[line] = and(strtonum($0),0xff000000);
                        #printf "%s %x %x %x %x\n",$0,byte0[line],rshift(byte1[line],8),rshift(byte2[line],16),rshift(byte3[line],24);
                        byte[col++]=byte0[line];
                        byte[col++]=rshift(byte1[line],8);
                        byte[col++]=rshift(byte2[line],16);
                        byte[col++]=rshift(byte3[line],24);
                        line++;
                    }
                 }
        END { 
            #print "line =" line;
            #print "col =" col;
            for (i=0; i<col; i++)
                printf "byte %d %x\n",i,byte[i]
        }
    '
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
