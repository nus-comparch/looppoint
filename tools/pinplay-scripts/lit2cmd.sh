#!/bin/sh
# purpose convert a lit-file to cmd-file for Archsim
ERROR()
{
  echo "Usage : $0 trace-basename"
  exit
}

if  [ $# -ne 1 ];  then
    echo "args " $#
    ERROR
fi

if [ ! -f $1.lit ]; then
    echo "Input file ($1.lit) does not exist!" 
    ERROR
fi

if [ ! -f $1.ptov ]; then
    echo "Input file ($1.ptov) does not exist!" 
    ERROR
fi

cat $1.lit | grep -v 'total' | gawk -v PTOVFILE=$1.ptov '
 BEGIN {
   first=1
   while ((getline line < PTOVFILE) > 0)
    {
        split(line, arr, " ");
        arr[1]="0x" arr[1];
        arr[2]="0x" arr[2];
        ptov[strtonum(arr[1])]= strtonum(arr[2])
    }
   close(PTOVFILE)
 }
 /^step/  {
            litcount=strtonum($4)+1
        }
 /^reg/  {
            dest=$2
            value=$4
            v=strtonum("0x" value)
            v1=rshift(v,32);
            v2=and(v,0xffffffff)
        # What we would like is this:
        # schedule at 7, reg fs = 0 93 ffff 2aaacfc8e6d0
        # However, what we need to actually provide is this:
        # schedule at 7, reg fs = 2aaa 0 93 ffff cfc8e6d0
        # "This is an unfortunate artifact of how the segment value 
        # is stored in Archsim.": Brandon Hales
            if(dest=="gs.base")
               printf "%s%s%s%x%s%x\n","schedule at ",litcount," reg gs = ",v1," 0x0 0x93 0xffffffff ",v2;
            else if(dest=="fs.base")
               printf "%s%s%s%x%s%x\n","schedule at ",litcount," reg fs = ",v1," 0x0 0x93 0xffffffff ",v2;
            else
               printf "%s%s%s%s%s%s\n","schedule at ",litcount,", inject ",dest," with ",value;
         }
 /^memory/  { 
            len=$2
            dest=$4
            destpg=and(strtonum("0x" dest),compl(0xfff));
            destoff=and(strtonum("0x" dest),0xfff);
            destv=ptov[destpg]+destoff;
            printf "%s%s%s%s%s%x%s","schedule at ",litcount,", mem ",len, " l ",destv," = ";
            for (i=6; i<=NF; i++)
            {
                printf " %s",$i;
            }
            printf "\n";
 }
 '
