# Installation

## Dependencies

MxOps heavily relies on the [multiversx-py-sdk](https://github.com/multiversx/mx-sdk-py) written by the MultiversX team and requires a python version of at least 3.10.
As the MultiversX team has a very high release rate, we strongly recommend to have a dedicated environment for MxOps to avoid any dependencies conflicts with your own projects.

We recommend to install it with [pipx](https://github.com/pypa/pipx), which will create a dedicated environment for MxOps:

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

or the awesome [uv](https://docs.astral.sh/uv/) tool:

```bash
uv venv mxops_env --python 3.11
source mxops_env/bin/activate
uv pip install -U mxops
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
