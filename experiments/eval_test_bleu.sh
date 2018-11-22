#!/bin/bash

source ../../p2-onmt/bin/activate

D=multi30k-dataset/data/task1/tok

reffile=test_2016_flickr.lc.norm.tok

for output in $1/*.txt; do
	tgt=`basename $output | cut -f 2 -d'-' | sed 's/.txt//'`
	bl=$output.bleu
	[[ ! -f $output ]] && continue
	[[ -f $bl ]] && continue
	ref=multi30k-dataset/data/task1/tok/$reffile.$tgt.detok
	[[ ! -f $ref ]] && perl ~/bin/detokenizer.perl -l $tgt < multi30k-dataset/data/task1/tok/$reffile.$tgt > $ref
	echo qsubmit -logdir bleu-logs \""perl ~/bin/detokenizer.perl -l $tgt < $output | tee $output.detok | python3 -m sacrebleu $ref -b > $bl"\"
done
