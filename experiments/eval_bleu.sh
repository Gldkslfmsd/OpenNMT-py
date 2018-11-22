#!/bin/bash

source ../../p2-onmt/bin/activate

D=multi30k-dataset/data/task1/tok

for src in en cs de fr; do
	for tgt in en cs de fr; do
		for model in $@; do
#			echo $model
			output=$model""_$src-$tgt.txt
			bl=$output.bleu
			[[ ! -f $output ]] && continue
			ref=multi30k-dataset/data/task1/tok/val.lc.norm.tok.$tgt.detok
			[[ ! -f $ref ]] && perl ~/bin/detokenizer.perl -l $tgt < multi30k-dataset/data/task1/tok/val.lc.norm.tok.$tgt > $ref
			echo qsubmit -logdir bleu-logs \""perl ~/bin/detokenizer.perl -l $tgt < $output | tee $output.detok | python3 -m sacrebleu $ref -b > $bl"\"
		done
	done
done
