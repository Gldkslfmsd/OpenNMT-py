#!/bin/bash

# example usage:
# schedule validation translation jobs for all enc-dec combinations for all saved models for given experiment:
# ./translate_all.sh experiment-dir/MULTILINGUAL*.pt

source ../../p2-onmt/bin/activate

D=multi30k-dataset/data/task1/tok

for src in en cs de fr; do
	for tgt in en cs de fr; do
		for model in $@; do
#			echo $model
			output=$model""_$src-$tgt.txt
			[[ -f $output ]] && continue
#			echo $output
			qsubmit -q gpu-ms.q -priority=-101 -logdir=logs-translate "../../p2-onmt/bin/python ../translate_multimodel.py -model $model \
				-src $D/val.lc.norm.tok.$src \
				-output $output \
				-replace_unk -verbose \
				-src_lang $src \
				-tgt_lang $tgt \
				-gpu 0 \
				-use_attention_bridge"

		done
	done
done
