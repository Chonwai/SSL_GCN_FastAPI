#coding=utf-8
import torch
from dgl import save_graphs
from joblib import Parallel, delayed, cpu_count


def pmap(pickleable_fn, data, n_jobs=None, verbose=1, **kwargs):
    if n_jobs is None:
        n_jobs = cpu_count() - 1

    return Parallel(n_jobs=n_jobs, verbose=verbose)(
        delayed(pickleable_fn)(d, **kwargs) for d in data
    )

class Dataset(object):
    def __init__(self, df, smiles_to_graph, node_featurizer, edge_featurizer, smiles_column,
                 cache_file_path, log_every=100):
        self.df = df
        self.smiles = self.df[smiles_column].tolist()
        self.task_names = self.df.columns.drop([smiles_column]).tolist()
        self.n_tasks = len(self.task_names)
        self.cache_file_path = cache_file_path
        self._pre_process(smiles_to_graph, node_featurizer, edge_featurizer, log_every)

    def _pre_process(self, smiles_to_graph, node_featurizer,
                     edge_featurizer, log_every):

        self.graphs = []
        for i, s in enumerate(self.smiles):
            if (i + 1) % log_every == 0:
                print('Processing molecule {:d}/{:d}'.format(i+1, len(self)))
            self.graphs.append(smiles_to_graph(s, node_featurizer=node_featurizer, edge_featurizer=edge_featurizer))
        self.valid_ids = []
        graphs = []
        for i, g in enumerate(self.graphs):
            if g is not None:
                self.valid_ids.append(i)
                graphs.append(g)
        self.graphs = graphs
        self.mol_idx = [self.df[self.task_names].values[i] for i in self.valid_ids]
        valid_ids = torch.tensor(self.valid_ids)
        save_graphs(self.cache_file_path, self.graphs, labels={'valid_ids': valid_ids})
        self.smiles = [self.smiles[i] for i in self.valid_ids]

    def __getitem__(self, item):
        return self.smiles[item], self.graphs[item], self.mol_idx[item]

    def __len__(self):
        return len(self.smiles)

