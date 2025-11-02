#set page(margin: 1in)
#set text(font: "New Computer Modern", size: 12pt)

= b3_drp

python library that implements the assignment of composite material plies to elements in (fea) models

say a two plies are defined as follows

```pseudocode
datums:
  te_offset:
    base: r
    values: [[0,0],[20,0.1],[40,0.2]]

plies:
  - mat: carbon
    angle: 45
    thickness: 0.45e-3
    parent: sparcap
    conditions:
      - field: r
        operator: in_range
        operand: [10, 20]
      - field: distance_from_te
        operator: >
        operand: 0.1
      - field: distance_from_le
        operator: >
        operand: 1
    key: 100
  - mat: glass
    angle: 0
    thickness: 1.2e-3
    parent: allover
    conditions:
      - field: r
        operator: in_range
        operand: [15, 25]
      - field: distance_from_te
        operator: >
        operand: te_offset
      - field: distance_from_le
        operator: >
        operand: 0.5
      - field: distance_from_web0
        operator: <
        operand: 0.6
    key: 102
```

the code then loads a pyvista/vtk grid and a material database
- in the matdb it checks that all used materials (carbon and glass) are present
- in the grid r, distance_from_le, distance_from_te and distance_from_web0 need to be present, if not as cell array, then translate point to cell
- use vectorization, whereby you create mask array defining condition1 && condition2 && condition...
- sort the plies by key, and if same key, by definition order
- as output, add ply arrays to the mesh, where each is named
  - ply\_000001\_{parentname}\_ {key}\_material
  - ply\_000001\_{parentname}\_ {key}\_angle
  - ply\_000001\_{parentname}\_ {key}\_thickness

= tech
- numpy, prioritize vectorization of operations
- pytest, use --cov
- uv
- multiprocessing
- matplotlib for plotting
- pyvista for mesh handling


= cli update

- drape 
    --lamplan
    --grid
    --matdb
- plot
    --scalar




