#coding=utf-8
import os
import dgl
import json
import errno
from functools import partial
import numpy as np
import pandas as pd
import torch.nn.functional as F
from dgllife.utils import smiles_to_bigraph
from dataset import Dataset

def init_featurizer(args):
    if args['atom_featurizer_type'] == 'canonical':
        # Atom Featurizer
        from dgllife.utils import CanonicalAtomFeaturizer
        args['node_featurizer'] = CanonicalAtomFeaturizer()
    else:
        return ValueError(
            "Expect node_featurizer to be in ['canonical', 'attentivefp'], "
            "got {}".format(args['atom_featurizer_type']))
    args['edge_featurizer'] = None
    return args

def load_dataset(args, df):
    dataset = Dataset(df=df,
                     smiles_to_graph=partial(smiles_to_bigraph, add_self_loop=True),
                     node_featurizer=args['node_featurizer'],
                     edge_featurizer=args['edge_featurizer'],
                     smiles_column=args['smiles_column'],
                     cache_file_path=args['result_path'] +'/graph.bin')
    return dataset

def get_self_configure(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
        f.close()
    return config

def mkdir_p(path):
    try:
        os.makedirs(path)
        print('Created directory {}'.format(path))
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            print('Directory {} already exists.'.format(path))
        else:
            raise

def collate_molgraphs(data):
    smiles, graphs, idxs = map(list, zip(*data))
    bg = dgl.batch(graphs)
    bg.set_n_initializer(dgl.init.zero_initializer)
    bg.set_e_initializer(dgl.init.zero_initializer)
    return smiles, bg, idxs

def load_model(exp_configure):
    if exp_configure['model'] == 'GCN':
        from dgllife.model import GCNPredictor
        model = GCNPredictor(
            in_feats=exp_configure['in_node_feats'],
            hidden_feats=[exp_configure['gnn_hidden_feats']] * exp_configure['num_gnn_layers'],
            activation=[F.relu] * exp_configure['num_gnn_layers'],
            residual=[exp_configure['residual']] * exp_configure['num_gnn_layers'],
            batchnorm=[exp_configure['batchnorm']] * exp_configure['num_gnn_layers'],
            dropout=[exp_configure['dropout']] * exp_configure['num_gnn_layers'],
            predictor_hidden_feats=exp_configure['predictor_hidden_feats'],
            predictor_dropout=exp_configure['dropout'],
            n_tasks=exp_configure['n_tasks'])
    else:
        return ValueError("Expect model to be from ['GCN'], "
                          "got {}".format(exp_configure['model']))
    return model

def predict(args, model, bg):
    bg = bg.to(args['device'])
    if args['edge_featurizer'] is None:
        node_feats = bg.ndata.pop('h').to(args['device'])
        return model(bg, node_feats)
    elif args['bond_featurizer_type'] == 'pre_train':
        node_feats = [
            bg.ndata.pop('atomic_number').to(args['device']),
            bg.ndata.pop('chirality_type').to(args['device'])
        ]
        edge_feats = [
            bg.edata.pop('bond_type').to(args['device']),
            bg.edata.pop('bond_direction_type').to(args['device'])
        ]
        return model(bg, node_feats, edge_feats)
    else:
        node_feats = bg.ndata.pop('h').to(args['device'])
        edge_feats = bg.edata.pop('e').to(args['device'])
        return model(bg, node_feats, edge_feats)

def read_fasta(args, file_path):
    f = open(file_path, 'r', encoding='utf-8')
    fasta_list = np.array(f.readlines())
    trans_mol = {'id':[], 'SMILES':[]}
    for flag in range(0, len(fasta_list), 2):
        trans_mol['id'].append(fasta_list[flag].strip('\n').strip('>').strip())
        trans_mol['SMILES'].append(fasta_list[flag + 1].strip('\n').strip())
    args['in_mol_ids'] = set([i for i in range(len(trans_mol['id']))])
    return trans_mol, load_dataset(args, pd.DataFrame(trans_mol))
       





