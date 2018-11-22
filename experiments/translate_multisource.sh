#!/bin/bash

source ../../p2-onmt/bin/activate

D=multi30k-dataset/data/task1/tok

model=$1/best_model.pt

[ ! -f $model ] && echo $model missing && exit 1

sourceset=$2
if [ $sourceset = test ]; then
	OUTDIR=$1/test
	src_pref=$D/test_2016_flickr.lc.norm.tok
else if [ $sourceset = dev ]; then
	OUTDIR=$1/dev
	src_pref=$D/val.lc.norm.tok
else
	OUTDIR=$1/train
	src_pref=$D/train.1000
fi; fi

mkdir -p $OUTDIR

shift
shift

SRC_COMBINATIONS="en cs de fr
en cs de
en de fr
de fr cs
fr en cs
en cs
en de
en fr
cs de
cs fr
de fr
en
cs
fr
de"

output_pref=$OUTDIR/$sourceset.
IFS='
'
for sources in $SRC_COMBINATIONS; do
	sources_files=""
	output_sources=$output_pref
	IFS=' ';
	i=""
	for lan in $sources; do
		sources_files="$sources_files $src_pref.$lan"
		output_sources="$output_sources$i$lan"
		i="+"
	done
	multisource=$OUTDIR/multisource.`echo $sources | sed 's/ /+/g'`
	paste $sources_files > $multisource

	for tgt in en cs de fr; do
		#echo "$sources -> $tgt"
		output=$output_sources-$tgt.txt
		#echo $output
		[[ -f $output ]] && continue
		qsubmit -q gpu-ms.q  -logdir=logs-translate "../../p2-onmt/bin/python ../translate_multisource.py -model $model \
			-src $multisource \
			-output $output \
			-verbose \
			-tgt_lang $tgt \
			-src_lang $sources \
			-gpu 0  \
			-use_attention_bridge
		"
	done
IFS='
'
done

