# Official Repository of: "TBD"
This repository contains the code to reproduce the experiments from the paper.

Abstract: Deep unsupervised approaches are gathering increased attention in the field of medical pathology detection and segmentation since they promise to alleviate labeled data bottlenecks and be more generalizable than their supervised counterparts in detecting any kind of rare pathology. As Unsupervised Anomaly Detection (UAD) literature continuously grows and new paradigms emerge, it is vital to continuously evaluate and benchmark new methods in a common context, in order to reassess the state-of-the-art (SOTA) and identify promising research directions. To this end, we evaluate a diverse selection of cutting-edge UAD methods on multiple medical datasets, pitting them against the established SOTA in brain MR. Our experiments demonstrate that newly developed Feature-space methods from the industrial and medical literature demonstrate increased performance compared to previous work and set the new SOTA in a variety of modalities and datasets. Additionally, we show that such methods are in principle capable of benefiting from recently developed self-supervised pre-training algorithms, further increasing their performance. Finally, we perform a series of experiments in order to gain further insights into some unique characteristics of selected models and datasets.

# Usage

Download this repository by running

```bash
git clone https://github.com/iolag/UPD_study/
```

in your terminal.

## Environment

Create and activate the Anaconda environment:

```bash
conda env create -f environment.yml
conda activate upd
```

Additionally, you need to install the repository as a package:

```bash
python3 -m pip install --editable .
```

To be able to use [Weights & Biases](https://wandb.ai) for logging follow the instructions at https://docs.wandb.ai/quickstart.


## Data

# CheXpert 

To download CheXpert you must first register at https://stanfordmlgroup.github.io/competitions/chexpert/. After you receive the subscription confirmation e-mail, download the downsampled version (~11G) and extract it in data/datasets/CXR. No other steps are required and all splits are provided.

# DDR 

To download and prepare the DDR dataset, run:

```bash
bash data/data_preprocessing/ddr.sh
```

# MRI: CamCAN, ATLAS, BraTS 

To download and prepare the MRI datasets, run:

```bash
bash data/data_preprocessing/mri.sh
```

