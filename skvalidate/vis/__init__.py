import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def draw_diff(name, values, out_dir, bins=100, logy=False):
    orig, ref, diff = values
    bins = 100

    fig, (a0, a1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [5, 1]}, sharex=True)
    name = name.replace(';1', '')
    output_file = os.path.join(out_dir, name + '.png')

    a0.hist(orig, label='this code', color='red', histtype='step', bins=bins, linewidth=2, alpha=0.6)
    a0.hist(ref, label='reference', color='black', histtype='step', bins=bins)
    a0.set_ylabel('a.u.')
    if logy:
        a0.set_yscale('log', nonposy='clip')
    a0.legend()
    a0.set_title('Validation plot: Work in Progress - handle with grain of salt')

    a1.hist(diff, label='diff', histtype='step', bins=bins)
    a1.set_xlabel(name)
    a1.minorticks_on()
    a1.legend()

    fig.tight_layout()
    plt.savefig(output_file)
    plt.close()
    return output_file