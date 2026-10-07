# Architecture

C4 model of MxOps, written with [LikeC4](https://likec4.dev). The source is [mxops.c4](./mxops.c4).

| View | Level | Rendered |
|------|-------|----------|
| `index` | System context | [index.mmd](./mermaid/index.mmd) |
| `containers` | Containers | [containers.mmd](./mermaid/containers.mmd) |
| `components` | Components of the MxOps CLI | [components.mmd](./mermaid/components.mmd) |

## Browse

- VSCode: install the [LikeC4 extension](https://marketplace.visualstudio.com/items?itemName=likec4.likec4-vscode), open `mxops.c4` and click `Open preview` above a view. Click an element to drill down.
- Browser: `npx likec4 start docs/architecture`
- GitHub: open the Mermaid files listed above.

## Update

Edit `mxops.c4`, then validate it and regenerate the Mermaid files:

```bash
npx likec4 validate docs/architecture
npx likec4 gen mermaid docs/architecture -o docs/architecture/mermaid
```
