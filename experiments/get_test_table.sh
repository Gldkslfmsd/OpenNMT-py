#!/bin/bash

source ../../p2-onmt/bin/activate

D=multi30k-dataset/data/task1/tok
echo -n "source"
for tgt in en cs de fr; do
	echo -n ";$tgt"
done

echo

for trans in $1*; do
	sources=`basename $trans | sed 's/[^.]*\.//;s/-.*//'`
	echo $sources
done | sort -u | while read sources; do
	echo -n "$sources"
	for tgt in en cs de fr; do
		output=$1.$sources-$tgt.txt
		bl=$output.bleu
		if [ -f $bl ]; then
			echo -n ";`cat $bl`"
		else
			echo -n ";-"
		fi
	done
	echo
done #| sed 's/;/	/' | sort -n -k 1 | sed 's/	/;/'
