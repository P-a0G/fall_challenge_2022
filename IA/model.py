import torch
import torch.nn as nn


class Model(nn.Module):
    def __init__(self, input_channels, output_channels, n_channels=128):
        super(Model, self).__init__()
        self.blocks = nn.Sequential(
            nn.Linear(input_channels, n_channels),
            nn.Linear(n_channels, n_channels),
            nn.Linear(n_channels, n_channels),
            nn.Linear(n_channels, output_channels),

        )

    @staticmethod
    def convert_as_input(cells):
        x = torch.zeros(12 * 24 * 4, dtype=int)

        for i, j in cells:
            x[i, j, 0] = cells[i, j].scrap
            x[i, j, 1] = cells[i, j].units
            x[i, j, 2] = cells[i, j].recycler
            x[i, j, 3] = cells[i, j].owner

        return x

    def forward(self, x):
        x = self.convert_as_input(x)
        y = self.blocks(x)
        y = y.detach().numpy()
        y = y.reshape(12, 24, 2)
        return y


def decode(model_output, cells):
    return 'WAIT'


if __name__ == '__main__':
    h = 12
    w = 24
    c = 4  # scrap, owner, recycler and units

    output_c = 2  # units, recyclers

    input_dim = h * w * c

    output_dim = h * w * 2

    model = Model(input_dim, output_dim)

    x = torch.ones(input_dim)

    print(model(x).shape)
