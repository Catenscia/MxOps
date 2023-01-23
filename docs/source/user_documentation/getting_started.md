# Getting Started

## Installation

Mxops is available on [PyPI](https://pypi.org/project/mxops/). Install it simply with pip:

```bash
pip install mxops
```

## Structure

We propose a folder structure template to organise your files. This is not mandatory but should make using MxOps much easier.
The structure is layed out as below:

```bash
.
└── mxops_files/
    ├── accounts/
    │   ├── local.yaml
    │   ├── test.yaml
    │   ├── dev.yaml
    │   └── main.yaml
    ├── use_case_1/
    │   ├── 01_first_scene.yaml
    │   ├── 02_second_scene.yaml
    │   └── 03_third_scene.yaml
    ├── use_case_2/
    │   ├── 01_first_scene.yaml
    │   ├── 02_second_scene.yaml
    │   ├── 03_third_scene.yaml
    │   └── 04_fourth_scene.yaml
    └── common_scene/
        ├── common_scene_1.yaml
        └── common_scene_2.yaml
```

### Accounts

Accounts are grouped in separate `scenes` to make sure you don't mix up your networks (there are other security measures in place to avoid that but we can never be to cautious).

### Scene Names

When you have a complexe usecase and you want to organise the `steps` in several `scenes` to keep things clean, you should write them in a specific folder and prefix the files names with a number to make sure they will get executed in the correct order.

## Next Step

You are now ready to learn how to write `scenes`!
Heads up to the {doc}`scenes` section
