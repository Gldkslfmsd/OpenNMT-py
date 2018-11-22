#!/bin/bash

# python virtual environment
VENV=$1
source $VENV/bin/activate

SAVE_PATH=zero-shot-cs-en_10heads
DATA=all_pairs_preprocessed

mkdir -p $SAVE_PATH $SAVE_PATH/tb

python ../train.py -data $DATA/de-cs/data \
                   $DATA/fr-cs/data \
                   $DATA/de-en/data \
                   $DATA/fr-en/data \
                   $DATA/cs-de/data \
                   $DATA/en-de/data \
                   $DATA/fr-de/data \
                   $DATA/cs-fr/data \
                   $DATA/de-fr/data \
                   $DATA/en-fr/data \
             -src_tgt de-cs fr-cs de-en fr-en cs-de en-de fr-de cs-fr de-fr en-fr \
             -save_model ${SAVE_PATH}/MULTILINGUAL          \
             -use_attention_bridge \
             -attention_heads 10 \
             -rnn_size 512 \
             -rnn_type GRU \
             -encoder_type brnn \
             -decoder_type rnn \
             -enc_layers 2 \
             -dec_layers 2 \
             -word_vec_size 512 \
             -global_attention mlp \
             -train_steps 30000 \
             -valid_steps 1000 \
             -optim adam \
             -learning_rate 0.0002 \
             -batch_size 256 \
             -gpuid 0 \
             -save_checkpoint_steps 1000 \
	-init_decoder attention_matrix \
	-tensorboard -tensorboard_log_dir ${SAVE_PATH}/tb
