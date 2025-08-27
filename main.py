#coding=utf-8
import os
import torch
import numpy as np
import pandas as pd
from argparse import ArgumentParser
from torch.utils.data import DataLoader
from utils import init_featurizer,  load_dataset, get_self_configure, mkdir_p, collate_molgraphs, load_model, predict, read_fasta
import shutil

def prediction(args, exp_config, data_set):
    exp_config.update({
        'model': args['model'],
        'n_tasks': args['n_tasks'],
        'atom_featurizer_type': args['atom_featurizer_type'],
        'bond_featurizer_type': args['bond_featurizer_type']})
    test_loader = DataLoader(dataset=data_set, batch_size=len(data_set), collate_fn=collate_molgraphs, num_workers=0)
    model = load_model(exp_config).to(args['device'])
    model.load_state_dict(torch.load(args['model_data_path']+'/model.pth', map_location=args['device'])['model_state_dict'])
    result = {'id': [], 'smiles': [], 'pre': []}
    model.eval()
    with torch.no_grad():
        for batch_id, batch_data in enumerate(test_loader):
            smiles, bg, idx = batch_data
            logits = predict(args, model, bg)
            proba = torch.sigmoid(logits).squeeze(1)
            result['id'].extend(np.array(idx).squeeze(1))
            result['smiles'].extend(smiles)
            result['pre'].extend((proba.detach().cpu().data > exp_config['t1']).int().numpy())
    return result

def model_run(data_file, root_model_folder, task_type, output_data_folder):

    pretrain_folder_path = root_model_folder + task_type + '/'

    args = {'task_names': task_type,
            'smiles_column': 'SMILES',
            'model': 'GCN',
            'result_path': output_data_folder,
            'model_data_path': pretrain_folder_path,
            'atom_featurizer_type': 'canonical',
            'bond_featurizer_type': 'canonical'
            }
    args = init_featurizer(args)
    args['device'] = torch.device('cpu')
    args['task_names'] = [args['task_names']]
    trans_mol, dataset = read_fasta(args, data_file)
    args['n_tasks'] = dataset.n_tasks
    args['valid_mol_ids'] = set(dataset.valid_ids)
    args['invalid_mol_ids'] = list(args['valid_mol_ids'] ^ args['in_mol_ids'])
    exp_config = get_self_configure(args['model_data_path'] + '/configure.json')
    result = prediction(args, exp_config, dataset)
    result['id'].extend(np.array(trans_mol['id'])[args['invalid_mol_ids']])
    result['smiles'].extend(np.array(trans_mol['SMILES'])[args['invalid_mol_ids']])
    result['pre'].extend(['invalid mol']*len(args['invalid_mol_ids']))

    result_df = pd.DataFrame(result)
    result_df.to_csv(output_data_folder+'result.csv', index=False)
    shutil.rmtree(output_data_folder)

    print('###PREDICTION OVER!###\n')


if __name__ == '__main__':
    parser = ArgumentParser('Prediction Script for SSL-GCN models')
    parser.add_argument('-d', '--data-path', type=str, required=True, help='The path to the data folder (with "/" or "\\" at the end)')
    parser.add_argument('-m', '--model-path', type=str, required=True, help='The path to the model folder (with "/" or "\\" at the end)')
    parser.add_argument('-t', '--task_type',
                        choices=['NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase',
                                 'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE',
                                 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'],
                        help='define the 1 of 12 toxicity endpoints.')
    parser.add_argument('-o', '--output-path', default=None, type=str, help='The path to an empty output folder where the experiment results will be stored (with "/" or "\\" at the end)')
    start_args = parser.parse_args().__dict__
    model_run(start_args['data_path'], start_args['model_path'], start_args['task_type'], start_args['output_path'])









