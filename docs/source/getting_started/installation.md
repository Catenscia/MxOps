# Installation

## Dependencies

MxOps heavily relies on the [python sdks](https://github.com/multiversx?q=sdk-py&type=all&language=&sort=) written by the MultiversX team and requires a python version of at least 3.10.
As the MultiversX team has a very high release rate, we strongly recommend to have a dedicated environment for MxOps to avoid any dependencies conflicts with your own projects.

If you only to use Mxops only as a command line, we recommend to install it with [pipx](https://github.com/pypa/pipx):

```bash
pipx install mxops
```

You can also upgrade an already installed version with pipx:

```bash
pipx upgrade mxops
```

Otherwise, you can use [Anaconda](https://www.anaconda.com/download) for example:

```bash
conda create -n mxops_env python=3.11 -y
conda activate mxops_env
pip install -U mxops
```


## From PyPI

MxOps is available on [PyPI](https://pypi.org/project/mxops/). Install it simply with pip:

```bash
pip install -U mxops
```

## From Github

If you want the latest developments of MxOps, you can install the package directly from the develop branch:

```bash
pip install -U git+https://github.com/Catenscia/MxOps@develop
```

If you want another branch or version, just replace "develop" by the branch or tag you want.

## Extension

The Visual Studio Code extension [mxopsHelper](https://marketplace.visualstudio.com/items?itemName=Catenscia.mxops-helper) has been created to help users write their `Scenes` by providing templates. We recommend using it as it greatly simplify the process of creating `Scenes`.


You can now heads up to the {doc}`next section <first_scene>` to learn how to write your first scene! 💪
