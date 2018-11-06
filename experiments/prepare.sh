#!/bin/bash

if [ ! -z "$1" ]; then
	EXPERIMENT=$1
else
	EXPERIMENT=all_pairs_preprocessed
fi


OUTPUT_DIR=`pwd`/$EXPERIMENT

ONMT=`pwd`/..

DATADIR=`pwd`/multi30k-dataset/data/task1/tok

mkdir -p $OUTPUT_DIR && cd $OUTPUT_DIR

ALL_SAVE_DATA=""
for src_lang in de en fr cs
do
  for trg_lang in de en fr cs
  do
    SAVEDIR=$OUTPUT_DIR/${src_lang}-${trg_lang}
    mkdir -p $SAVEDIR
	SAVEDATA=$SAVEDIR/data
    src_train_file=$DATADIR/train.lc.norm.tok.${src_lang}
    trg_train_file=$DATADIR/train.lc.norm.tok.${trg_lang}
    src_valid_file=$DATADIR/val.lc.norm.tok.${src_lang}
    trg_valid_file=$DATADIR/val.lc.norm.tok.${trg_lang}
    python $ONMT/preprocess.py \
      -train_src $src_train_file \
      -train_tgt $trg_train_file \
      -valid_src $src_valid_file \
      -valid_tgt $trg_valid_file \
      -save_data $SAVEDATA \
      -src_vocab_size 10000 \
      -tgt_vocab_size 10000
	ALL_SAVE_DATA="$SAVEDATA $ALL_SAVE_DATA"
  done
done

python $ONMT/preprocess_build_vocab.py \
	-share_vocab \
	-train_dataset_prefixes $ALL_SAVE_DATA \
    -src_vocab_size 10000 \
    -tgt_vocab_size 10000
