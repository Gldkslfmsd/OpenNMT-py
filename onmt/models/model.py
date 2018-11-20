""" Onmt NMT Model base class definition """
import torch.nn as nn
import copy
import random

from onmt.attention_bridge import AttentionBridge

class MultiTaskModel(nn.Module):
    """
    Core trainable object in OpenNMT. Implements a trainable interface
    for a simple, generic encoder + decoder model.

    Args:
      encoder (:obj:`EncoderBase`): an encoder object
      decoder (:obj:`RNNDecoderBase`): a decoder object
      multi<gpu (bool): setup for multigpu support
    """

    def __init__(self, encoder, decoder, model_opt, multigpu=False):
        self.multigpu = multigpu
        super(MultiTaskModel, self).__init__()

        # Chris: these fields currently get initialized externally
        self.encoder_ids = None
        self.encoders = None

        self.use_attention_bridge = model_opt.use_attention_bridge
        self.init_decoder = model_opt.init_decoder
        if self.use_attention_bridge:
            self.attention_bridge = AttentionBridge(model_opt.rnn_size, 
                                                    model_opt.attention_heads, 
                                                    model_opt.dec_layers)#, model_opt.dropout)

        self.decoder_ids = None
        self.decoders = None

        # generator ids is linked with decoder_ids
        # self.generators = None

    def forward(self, src, tgt, src_task, tgt_task, lengths, dec_state=None):
        """Forward propagate a `src` and `tgt` pair for training.
        Possible initialized with a beginning decoder state.

        Args:
            src (:obj:`Tensor`):
                a source sequence passed to encoder.
                typically for inputs this will be a padded :obj:`LongTensor`
                of size `[len x batch x features]`. however, may be an
                image or other generic input depending on encoder.
            tgt (:obj:`LongTensor`):
                 a target sequence of size `[tgt_len x batch]`.
            lengths(:obj:`LongTensor`): the src lengths, pre-padding `[batch]`.
            dec_state (:obj:`DecoderState`, optional): initial decoder state
        Returns:
            (:obj:`FloatTensor`, `dict`, :obj:`onmt.Models.DecoderState`):

                 * decoder output `[tgt_len x batch x hidden]`
                 * dictionary attention dists of `[tgt_len x batch x src_len]`
                 * final decoder state
        """
        tgt = tgt[:-1]  # exclude last target from inputs

        encoder = self.encoders[self.encoder_ids[src_task]]
        decoder = self.decoders[self.decoder_ids[tgt_task]]

        enc_final, memory_bank = encoder(src, lengths)
        #import ipdb; ipdb.set_trace()

        # Implement attention bridge/compound attention
        lstm_rnn_type =  str(type(decoder.rnn)).find('LSTM') > -1
        if self.use_attention_bridge:
            if lstm_rnn_type:
                rnn_final, rnn_memory_bank = enc_final, memory_bank
            enc_final, memory_bank = self.attention_bridge(memory_bank)
        
        
        # initialize decoder
        if str(type(encoder)).find('transformer.TransformerEncoder') > -1:
            assert (self.init_decoder == "attention_matrix") , \
               ("""Unsupported decoder initialization '%s'. Use 
                the 'attention matrix' option for the '-init_decoder'
                flag when using a transformer encoder""" % (self.init_decoder))
        if lstm_rnn_type:
            enc_state = \
                decoder.init_decoder_state(src, rnn_memory_bank, rnn_final)
        else:
            if (self.init_decoder == 'attention_matrix'):
                enc_state = \
                    self.attention_bridge.init_decoder_state(src, memory_bank, enc_final)
            else:
                enc_state = \
                    decoder.init_decoder_state(src, memory_bank, enc_final)



        decoder_outputs, dec_state, attns = \
            decoder(tgt, memory_bank,
                    enc_state if dec_state is None
                    else dec_state,
                    memory_lengths=lengths)

        if self.multigpu:
            # Not yet supported on multi-gpu
            dec_state = None
            attns = None
        return decoder_outputs, attns, dec_state


class MultiSourceModel(MultiTaskModel):

    def __init__(self, multitask_model):
        self.multigpu = multitask_model.multigpu
        super(MultiTaskModel, self).__init__()

        # Chris: these fields currently get initialized externally
        self.encoder_ids = multitask_model.encoder_ids
        self.encoders = multitask_model.encoders

        self.use_attention_bridge = multitask_model.use_attention_bridge
        self.init_decoder = multitask_model.init_decoder
        if self.use_attention_bridge:
            self.attention_bridge = multitask_model.use_attention_bridge

        self.decoder_ids = multitask_model.decoder_ids
        self.decoders = multitask_model.decoders

    def forward(self, src, tgt, src_tasks, tgt_task, lengths, dec_state=None):
        """Forward propagate a `src` and `tgt` pair for training.
        Possible initialized with a beginning decoder state.

        Args:
            src (:obj:`Tensor`):
                a source sequence passed to encoder.
                typically for inputs this will be a padded :obj:`LongTensor`
                of size `[len x batch x features]`. however, may be an
                image or other generic input depending on encoder.
            tgt (:obj:`LongTensor`):
                 a target sequence of size `[tgt_len x batch]`.
            lengths(:obj:`LongTensor`): the src lengths, pre-padding `[batch]`.
            dec_state (:obj:`DecoderState`, optional): initial decoder state
        Returns:
            (:obj:`FloatTensor`, `dict`, :obj:`onmt.Models.DecoderState`):

                 * decoder output `[tgt_len x batch x hidden]`
                 * dictionary attention dists of `[tgt_len x batch x src_len]`
                 * final decoder state
        """
        tgt = tgt[:-1]  # exclude last target from inputs

        encoders = [ self.encoders[self.encoder_ids[s]] for s in src_tasks ]
        decoder = self.decoders[self.decoder_ids[tgt_task]]

        enc_finals = []
        memory_banks = []
        for encoder in encoders:
            enc_final, memory_bank = encoder(src, lengths)
            #import ipdb; ipdb.set_trace()

            # Implement attention bridge/compound attention
            lstm_rnn_type =  str(type(decoder.rnn)).find('LSTM') > -1
            if self.use_attention_bridge:
                if lstm_rnn_type:
                    rnn_final, rnn_memory_bank = enc_final, memory_bank
                enc_final, memory_bank = self.attention_bridge(memory_bank)
            enc_finals.append(enc_final)
            memory_banks.append(memory_bank)

#        memory_bank = average(memory_banks)


        # initialize decoder
        if str(type(encoder)).find('transformer.TransformerEncoder') > -1:
            assert (self.init_decoder == "attention_matrix") , \
               ("""Unsupported decoder initialization '%s'. Use 
                the 'attention matrix' option for the '-init_decoder'
                flag when using a transformer encoder""" % (self.init_decoder))
        if lstm_rnn_type:
            enc_state = \
                decoder.init_decoder_state(src, rnn_memory_bank, rnn_final)
        else:
            if (self.init_decoder == 'attention_matrix'):
                enc_state = \
                    self.attention_bridge.init_decoder_state(src, memory_bank, enc_final)
            else:
                enc_state = \
                    decoder.init_decoder_state(src, memory_bank, enc_final)



        decoder_outputs, dec_state, attns = \
            decoder(tgt, memory_bank,
                    enc_state if dec_state is None
                    else dec_state,
                    memory_lengths=lengths)

        if self.multigpu:
            # Not yet supported on multi-gpu
            dec_state = None
            attns = None
        return decoder_outputs, attns, dec_state


class NMTModel(nn.Module):
    """
    Core trainable object in OpenNMT. Implements a trainable interface
    for a simple, generic encoder + decoder model.

    Args:
      encoder (:obj:`EncoderBase`): an encoder object
      decoder (:obj:`RNNDecoderBase`): a decoder object
      multi<gpu (bool): setup for multigpu support
    """

    def __init__(self, encoder, decoder, model_opt, multigpu=False):
        self.multigpu = multigpu
        super(NMTModel, self).__init__()
        self.encoder = encoder
        self.use_attention_bridge = model_opt.use_attention_bridge
        self.attention_bridge = AttentionBridge(model_opt.rnn_size, 
                                                    model_opt.attention_heads, 
                                                    model_opt.dec_layers) #, model_opt.dropout)
        self.decoder = decoder

    def forward(self, src, tgt, lengths, dec_state=None):
        """Forward propagate a `src` and `tgt` pair for training.
        Possible initialized with a beginning decoder state.

        Args:
            src (:obj:`Tensor`):
                a source sequence passed to encoder.
                typically for inputs this will be a padded :obj:`LongTensor`
                of size `[len x batch x features]`. however, may be an
                image or other generic input depending on encoder.
            tgt (:obj:`LongTensor`):
                 a target sequence of size `[tgt_len x batch]`.
            lengths(:obj:`LongTensor`): the src lengths, pre-padding `[batch]`.
            dec_state (:obj:`DecoderState`, optional): initial decoder state
        Returns:
            (:obj:`FloatTensor`, `dict`, :obj:`onmt.Models.DecoderState`):

                 * decoder output `[tgt_len x batch x hidden]`
                 * dictionary attention dists of `[tgt_len x batch x src_len]`
                 * final decoder state
        """
        tgt = tgt[:-1]  # exclude last target from inputs

        enc_final, memory_bank = self.encoder(src, lengths)
        enc_state = \
            self.decoder.init_decoder_state(src, memory_bank, enc_final)
        # Implement attention bridge/compound attention
        if self.use_attention_bridge:
            enc_final, memory_bank = self.attention_bridge(memory_bank)

        decoder_outputs, dec_state, attns = \
            self.decoder(tgt, memory_bank,
                         enc_state if dec_state is None
                         else dec_state,
                         memory_lengths=lengths)
        if self.multigpu:
            # Not yet supported on multi-gpu
            dec_state = None
            attns = None
        return decoder_outputs, attns, dec_state
