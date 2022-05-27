import os
from typing import List, Tuple
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms as T
import numpy as np
from torch.utils.data import DataLoader
from torch import Tensor
from argparse import Namespace
from Utilities.utils import GenericDataloader


def get_files(config: Namespace,
              train: bool = True) -> List or Tuple[List, List]:
    """
    Return a list of all the paths of normal files.

    Args:
        config (Namespace): configuration object
        train (bool): True for train images, False for test images and labels
    Returns:
        images (List): List of paths of normal files.
        masks (List): (If train == True) List of paths of segmentations.

    config should include "datasets_dir"
    """

    if train:
        pathfile = open(os.path.join(config.datasets_dir,
                                     'Colonoscopy',
                                     'labeled-images',
                                     'lower-gi-tract',
                                     'normal_image_paths.csv'))

        paths = pathfile.read().splitlines()

        for idx, path in enumerate(paths):
            paths[idx] = os.path.join(config.datasets_dir, path)

        return paths[300:]

    else:

        pathfile = open(os.path.join(config.datasets_dir,
                                     'Colonoscopy',
                                     'labeled-images',
                                     'lower-gi-tract',
                                     'normal_image_paths.csv'))

        paths = pathfile.read().splitlines()

        for idx, path in enumerate(paths):
            paths[idx] = os.path.join(config.datasets_dir, path)

        imgs = open(os.path.join(config.datasets_dir,
                                 'Colonoscopy',
                                 'segmented-images',
                                 'polyp_image_paths.csv')).read().splitlines()

        masks = open(os.path.join(config.datasets_dir,
                                  'Colonoscopy',
                                  'segmented-images',
                                  'polyp_mask_paths.csv')).read().splitlines()

        return imgs, paths[:300], masks


class NormalDataset(Dataset):
    """
    Dataset class for the Healthy Colonoscopy images
    from Hyper-Kvasir Dataset.
    """

    def __init__(self, files: List, config: Namespace):
        """
        param files: list of img paths for healthy colonoscopy images
        param config: Namespace() config object

        config should include "image_size"
        """

        self.stadardize = config.stadardize

        self.files = files

        # mean and std of normal samples
        # HK_mean = np.array([0.4403, 0.2277, 0.1469]) # with trick
        # HK_std = np.array([0.3186, 0.2006, 0.1544])

        HK_mean = np.array([0.5256, 0.2889, 0.1939])
        HK_std = np.array([0.3186, 0.2006, 0.1544])

        self.transforms = T.Compose([
            T.Resize((config.image_size, config.image_size),
                     T.InterpolationMode.LANCZOS),
            T.CenterCrop(config.image_size),
            hide_blue_box(config),
            T.ToTensor(),
        ])

        self.norm = T.Normalize(HK_mean, HK_std)

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx) -> Tensor:
        """
        :param idx: Index of the file to load.
        :return: The loaded img.
        """

        img = Image.open(self.files[idx])
        img = self.transforms(img)

        # # silly trick

        # mask = (img[2] > np.percentile(img[2], 90)).repeat(3, 1, 1)
        # img[mask] = 0

        # if we are not training fanogan, stadardize imgs to N(0,1)
        if self.stadardize:
            img = self.norm(img)

        return img


class AnomalDataset(Dataset):
    """
    Dataset class for the Segmented Colonoscopy
    images from the Hyper-Kvasir Dataset.
    """

    def __init__(self, images: List, normals: List, masks: List, config: Namespace):
        """
        param images: list of img paths for segmented colonoscopy images
        param masks: list of img paths for corresponding segmentations
        param config: Namespace() config object

        config should include "image_size"
        """

        self.stadardize = config.stadardize
        self.images = images
        self.normals = normals
        self.norm_anom = images + normals
        self.masks = masks
        self.img_size = config.image_size

        # mean and std of normal samples
        # HK_mean = np.array([0.4403, 0.2277, 0.1469]) # with trick
        # HK_std = np.array([0.3186, 0.2006, 0.1544])

        HK_mean = np.array([0.5256, 0.2889, 0.1939])
        HK_std = np.array([0.3186, 0.2006, 0.1544])

        self.image_transforms = T.Compose([
            T.Resize((config.image_size, config.image_size),
                     T.InterpolationMode.LANCZOS),
            hide_blue_box(config),
            T.ToTensor(),

        ])

        self.norm = T.Normalize(HK_mean, HK_std)

        self.mask_transforms = T.Compose([
            T.Resize((config.image_size, config.image_size),
                     T.InterpolationMode.NEAREST),
            hide_blue_box(config),
            T.ToTensor(),
        ])

    def __len__(self):
        return len(self.images + self.normals)

    def __getitem__(self, idx) -> Tuple[Tensor, Tensor]:
        """
        :param idx: Index of the file to load.
        :return: The loaded img and the binary segmentation mask.
        """

        img = Image.open(self.norm_anom[idx])
        if idx > len(self.masks) - 1:
            mask = torch.zeros(size=(1, self.img_size, self.img_size)).int()
        else:
            mask = Image.open(self.masks[idx])
            mask = self.mask_transforms(mask)

        img = self.image_transforms(img)

        # silly trick
        # msk = (img[2] > np.percentile(img[2], 90)).repeat(3, 1, 1)
        # img[msk] = 0

        # if we are not training fanogan, stadardize imgs to N(0,1)
        if self.stadardize:
            img = self.norm(img)

        return img, mask.int()[0].unsqueeze(0)  # make the mask shape [1,h,w]


def get_dataloaders(config: Namespace,
                    train=True) -> DataLoader or Tuple[DataLoader, DataLoader]:
    """
    Return pytorch Dataloader instances.

    config should include "normal_split", "anomal_split", "num_workers", "batch_size"

    Args:
        config (Namespace): Config object.
        train (bool): True for trainloaders, False for testloader with masks.
    Returns:
        train_dl (DataLoader) if train == True and config.spli_idx = 1
        train_dl, val_dl  (Tuple[DataLoader,DataLoader]) if train == True and
        config.spli_idx != 1
        test_dl (DataLoader) if train == False

    """

    if train:

        # get list of img paths
        trainfiles = get_files(config, train)

        # calculate dataset split index
        split_idx = int(len(trainfiles) * config.normal_split)

        if split_idx != len(trainfiles):

            trainset = NormalDataset(trainfiles[:split_idx], config)
            valset = NormalDataset(trainfiles[split_idx:], config)

            train_dl = GenericDataloader(trainset, config)
            val_dl = GenericDataloader(valset, config)

            return train_dl, val_dl

        else:

            trainset = NormalDataset(trainfiles, config)
            train_dl = GenericDataloader(trainset, config)

            return train_dl

    elif not train:
        # get list of img and mask paths
        images, normals, masks = get_files(config, train)

        split_idx = int(len(images) * config.anomal_split)
        split_idx_norm = int(len(normals) * config.anomal_split)
        if split_idx != len(images):

            big = AnomalDataset(images[:split_idx], normals[:split_idx_norm],
                                masks[:split_idx], config)
            small = AnomalDataset(images[split_idx:], normals[split_idx_norm:],
                                  masks[split_idx:], config)

            big_testloader = GenericDataloader(big, config, shuffle=True)
            small_testloader = GenericDataloader(small, config, shuffle=True)

            return big_testloader, small_testloader
        else:
            testset = AnomalDataset(images, normals, masks, config)

            test_dl = GenericDataloader(testset, config, shuffle=True)

            return test_dl


class hide_blue_box(torch.nn.Module):

    """
    Crop the bluebox appearing in most Colonoscopy images.
    Return cropped img.

    The indexes to hide the blue boxes are a rough estimate
    after img inspection.
    """

    def __init__(self, config: Namespace):
        super().__init__()

        self.config = config
        self.h_idx = 166 * config.image_size // 256
        self.w_idx = 90 * config.image_size // 256

    def forward(self, img: Tensor) -> Tensor:

        mask = np.ones((self.config.image_size, self.config.image_size, 3))
        # self.h_idx
        mask[self.h_idx:, 0: self.w_idx, :] = 0
        cropped_image = Image.fromarray(np.uint8(np.asarray(img) * mask))

        return cropped_image
