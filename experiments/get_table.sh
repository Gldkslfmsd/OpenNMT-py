#!/bin/bash

source ../../p2-onmt/bin/activate

D=multi30k-dataset/data/task1/tok
echo -n "step"
for src in en cs de fr; do
	for tgt in en cs de fr; do
		echo -n ";$src-$tgt"
	done
done
echo



for model in $@; do
	step=`echo $model | sed 's/.*step_//' | sed 's/\.pt//'`
	echo -n "$step"
	for src in en cs de fr; do
		for tgt in en cs de fr; do
			output=$model""_$src-$tgt.txt
			bl=$output.bleu
			echo -n ";`cat $bl`"
		done
	done
	echo
done | sed 's/;/	/' | sort -n -k 1 | sed 's/	/;/'
