# Ocarina of Time Angle Finder 

# Usage

## Movement Search Types
Modify `ALLOWED_GROUPS` in `angle_finder.py` to change which movements are allowed for angle finding. 

Valid options are `"basic"`, `"target enabled"`, `"no carry"`, `"sword"`, `"biggoron"`, `"hammer"`, `"shield corners"`.

### Example `ALLOWED_GROUPS`
```py
ALLOWED_GROUPS = ["basic",  "target enabled", "no carry", "biggoron", "hammer"]
```

| Group      | Description |
| ----------- | ----------- |
|`"basic"`| Enables using ess turns to look for angles.
|`"target enabled"`| Assumes the ability to lock the camera via target or c up which enables using ess up and turns (left, right, and 180).
|`"no carry"`| Assumes Link is not carrying anything which enables using rolls and sidehops.
|`"sword"`| Assumes Link is able to use the Master Sword or Kokiri Sword which enables quick spins. 
|`"biggoron"`| Assumes Link is able to use the Biggoron Sword or Giant's Knife which enables slash cancels and quick spins with it.
|`"hammer"`| Assumes Link is able to use the Megaton Hammer which enables using hammer side swing cancels.
|`"shield corners"`| Assumes perfect corner values are available, which is only reasonably possible on N64 with a good controller.

## Starting Angle List
Modify the starting list of angles to choose your starting angles. For example, you might do the cardinals (`0x0000`, `0x4000`, `0x8000`, `0xc000`) and/or some nearby walls (for example, some near Link's house: `0x4d19`, `0xad1c`, `0xe000`).
 ### Example Starting Angles
```py
    # Create a graph starting at the given angles.
    graph = explore([
        0x0000, 0x4000, 0x8000, 0xc000,
        0x4d19, 0xad1c, 0xe000
    ], avoid)
```
## End Angle List
Modify the search list of angles to choose your ending angles. These angles are formatted as a single string so you can easily copy and paste values in from the [SRM doc by Exodus](https://docs.google.com/spreadsheets/d/1SLJzamokLb7wDOaJh5x8DsxmMBy9oIYawyDN3dAWppw/edit#gid=2107229112). 
### Example Ending Angles
```py
    angles = """
1234
3333
acab
9876
0dad
    """```
