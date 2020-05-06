"""
Search
"""
import csv

import numpy as np
from torch.utils.data import DataLoader, Subset, random_split
from .utils import compute_loss

def fit(net, optimizer, loss_function, dataloader_train, dataloader_val, epochs=10, pbar=None, device='cpu'):
    val_loss_best = np.inf

    # Prepare loss history
    for _ in range(epochs):
        for _, (x, y) in enumerate(dataloader_train):
            optimizer.zero_grad()

            # Propagate input
            netout = net(x.to(device))

            # Comupte loss
            loss = loss_function(y.to(device), netout)

            # Backpropage loss
            loss.backward()

            # Update weights
            optimizer.step()

        val_loss = compute_loss(net, dataloader_val,
                                loss_function, device).item()

        if val_loss < val_loss_best:
            val_loss_best = val_loss

        if pbar is not None:
            pbar.update()

    return val_loss_best


def kfold(dataset, n_chunk, batch_size, num_workers):
    """
    kfold method
    """
    indexes = np.arange(len(dataset))
    chunks_idx = np.array_split(indexes, n_chunk)

    for idx_val, chunk_val in enumerate(chunks_idx):
        chunk_train = np.concatenate([chunk_train for idx_train, chunk_train in enumerate(
            chunks_idx) if idx_train != idx_val])

        subset_train = Subset(dataset, chunk_train)
        subset_val = Subset(dataset, chunk_val)

        dataloader_train = DataLoader(subset_train,
                                      batch_size=batch_size,
                                      shuffle=True,
                                      num_workers=num_workers
                                      )
        dataloader_val = DataLoader(subset_val,
                                    batch_size=batch_size,
                                    shuffle=True,
                                    num_workers=num_workers
                                    )

        yield dataloader_train, dataloader_val


def learning_curve(dataset, n_part, validation_split, batch_size, num_workers):
    """
    learning_curve method
    """
    # Split train and val
    val_split = int(len(dataset) * validation_split)
    subset_train, subset_val = random_split(
        dataset, [len(dataset) - val_split, val_split])

    dataloader_val = DataLoader(subset_val,
                                batch_size=batch_size,
                                shuffle=True,
                                num_workers=num_workers
                                )

    for idx in np.linspace(0, len(subset_train), n_part+1).astype(int)[1:]:
        subset_learning = Subset(dataset, subset_train.indices[:idx])
        dataloader_train = DataLoader(subset_learning,
                                      batch_size=batch_size,
                                      shuffle=True,
                                      num_workers=num_workers
                                      )

        yield dataloader_train, dataloader_val


class Logger:
    """
    Logger class
    """

    # NOTE Dangerous default value [] as argumentpylint(dangerous-default-value)
    def __init__(self, csv_path, search_params=[]):
        self.csv_file = open(csv_path, 'w')
        self.writer = csv.DictWriter(self.csv_file, search_params + ['loss'])
        self.writer.writeheader()

    # NOTE Dangerous default value {} as argumentpylint(dangerous-default-value)
    def log(self, params={}, **kwargs):
        """
        log method
        """
        params.update(kwargs)
        self.writer.writerow(params)
        self.csv_file.flush()

    def __del__(self):
        self.csv_file.close()
