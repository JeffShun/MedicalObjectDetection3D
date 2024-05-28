
import random
import torch

"""
数据预处理工具
1、所有数据预处理函数都包含两个输入: img 、label
2、img、label的输入维度为3维[C,H,W]，第一个维度是通道数
"""

class TransformCompose(object):

    """Composes several transforms together.
    Args:
        transforms (list of ``Transform`` objects): list of transforms to compose.
    """
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, img, label):
        for t in self.transforms:
            img, label = t(img, label)
        return img, label

    def __repr__(self):
        format_string = self.__class__.__name__ + '('
        for t in self.transforms:
            format_string += '\n'
            format_string += '    {0}'.format(t)
        format_string += '\n)'
        return format_string


class to_tensor(object):
    def __call__(self, img, label):
        img_o = torch.from_numpy(img)
        label_o = torch.from_numpy(label)
        return img_o, label_o


class label_alignment(object):
    def __init__(self, max_box_num, pad_val=-1):
        self.max_box_num = max_box_num
        self.pad_val = pad_val

    def __call__(self, img, label):
        img_o, label_o = img, label
        pad_size = self.max_box_num - label.size(0)
        if pad_size > 0:
            pad_shape = (0, 0, 0, pad_size)
            label_o = torch.nn.functional.pad(label, pad_shape, value=self.pad_val)
        return img_o, label_o


class resize(object):
    def __init__(self, size):
        self.size = size

    def __call__(self, img, label):
        img_o, label_o = img, label
        _, ori_z, ori_y, ori_x = img.shape
        scale_z = self.size[0] / ori_z
        scale_y = self.size[1] / ori_y
        scale_x = self.size[2] / ori_x
        img_o = torch.nn.functional.interpolate(img[None], size=self.size, mode="trilinear")[0]

        label_o[:, 0] *= scale_z
        label_o[:, 1] *= scale_y
        label_o[:, 2] *= scale_x
        label_o[:, 3] *= scale_z
        label_o[:, 4] *= scale_y
        label_o[:, 5] *= scale_x
    
        return img_o, label_o


class normlize(object):
    def __init__(self, win_clip=None):
        self.win_clip = win_clip

    def __call__(self, img, label): 
        img_o, label_o = img, label 
        if self.win_clip is not None:
            img = torch.clip(img, self.win_clip[0], self.win_clip[1])
        img_o = self._norm(img)
        return img_o, label_o
    
    def _norm(self, img):
        ori_shape = img.shape
        img_flatten = img.reshape(ori_shape[0], -1)
        img_min = img_flatten.min(dim=-1,keepdim=True)[0]
        img_max = img_flatten.max(dim=-1,keepdim=True)[0]
        img_norm = (img_flatten - img_min)/(img_max - img_min)
        img_norm = img_norm.reshape(ori_shape)
        return img_norm


class random_flip(object):
    def __init__(self, axis=1, prob=0.5):
        assert isinstance(axis, int) and axis in [1, 2, 3]
        self.axis = axis
        self.prob = prob

    def __call__(self, img, label):
        img_o, label_o = img, label
        if random.random() < self.prob:
            _, z, y, x = img.shape
            img_o = torch.flip(img, [self.axis])
            if self.axis == 1:  
                z1 = label[:, 0].clone()
                z2 = label[:, 3].clone()
                    
                label_o[:, 0] = z - 1 - z2
                label_o[:, 3] = z - 1 - z1

            if self.axis == 2:  
                y1 = label[:, 1].clone()
                y2 = label[:, 4].clone()

                label_o[:, 1] = y - 1 - y2
                label_o[:, 4] = y - 1 - y1

            if self.axis == 3:  
                x1 = label[:, 2].clone()
                x2 = label[:, 5].clone()

                label_o[:, 2] = x - 1 - x2
                label_o[:, 5] = x - 1 - x1

        return img_o, label_o


class random_gamma_transform(object):
    """
    input must be normlized before gamma transform
    """
    def __init__(self, gamma_range=[0.8, 1.2], prob=0.5):
        self.gamma_range = gamma_range
        self.prob = prob
    def __call__(self, img, label):
        img_o, label_o = img, label
        if random.random() < self.prob:
            gamma = random.uniform(self.gamma_range[0], self.gamma_range[1])
            img_o = img**gamma
        return img_o, label_o
    

class random_add_noise(object):
    def __init__(self, sigma_range=[0.1, 0.3], prob=0.5):
        self.sigma_range = sigma_range
        self.prob = prob

    def __call__(self, img, label):
        img_o, label_o = img, label 
        if random.random() < self.prob:
            sigma = random.uniform(self.sigma_range[0], self.sigma_range[1])
            noise = torch.randn_like(img) * sigma
            noisy_image = img + noise
            img_o = torch.clip(noisy_image, 0, 1)
        return img_o, label_o










