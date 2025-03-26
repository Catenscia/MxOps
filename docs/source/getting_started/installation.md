(installation_target)=
# Installation

## MxOps

### Dependencies

MxOps heavily relies on the [multiversx-py-sdk](https://github.com/multiversx/mx-sdk-py) written by the MultiversX team and requires a python version of at least 3.10.
As the MultiversX team has a very high release rate, we strongly recommend to have a dedicated environment for MxOps to avoid any dependencies conflicting with your own projects.


### Recommended installation with UV

We recommend to install MxOps with [uv](https://docs.astral.sh/uv/), and to install it as an independent tool: this will create a dedicated environment for MxOps and MxOps will be callable from anywhere in your system

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install MxOps as a tool

```bash
uv tool install mxops
```

Chech that MxOps was installed successfuly:

```bash
mxops version
```

### Installation with pipx


You can also install MxOps in a dedicated environnement with [pipx](https://github.com/pypa/pipx)

```bash
pipx install mxops
```

### Installation in a conda environnement

If you prefer to create your self an environnement, you can do this with [Anaconda](https://www.anaconda.com/download)

```bash
conda create -n mxops_env python=3.11 -y
conda activate mxops_env
pip install -U mxops
```

### Installation in a virtual environnement

Or in a virtual environnement with uv:

```bash
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -U mxops
```


### Install a development version

If you want to install the latest development version, use directly the github url to the develop branch:

```bash
uv tool install git+https://github.com/Catenscia/MxOps@develop
```

## VSCode Extension

The Visual Studio Code extension [mxopsHelper](https://marketplace.visualstudio.com/items?itemName=Catenscia.mxops-helper) has been created to help users write their scenes by providing templates. We recommend using it as it greatly simplify the process of creating scenes: You won't have to remember the syntax as this extension will offer you auto-completion.

```{figure} ../_images/extension_installation.png
:alt: User flow on MxOps
:align: center
:target: ../_images/extension_installation.png
```

## Docker

If you are planning on using the chain-simulator, you will also need docker. Please refer to the official [installation steps](https://docs.docker.com/engine/install/).

## Next Step

You can now heads up to the {doc}`next chapter <first_scene>` to learn how to write your first scene! 💪