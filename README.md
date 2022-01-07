# Blender To BBMOD
This Blender add-on allows a very basic export of a static Blender model
to a BBMOD file. The generated .bbmod file can be loaded directly using [`BBMOD_Model.from_file`](https://github.com/blueburn-cz/BBMOD/blob/40a0fe0ad18752a672f8287b90fb89a42d6bc3d2/BBMOD_GML/scripts/BBMOD_Model/BBMOD_Model.gml#L159).

## Basic use
* Select all meshlike objects that you want to export. Meshlike objects are objects
of a [type](https://docs.blender.org/manual/en/latest/scene_layout/object/types.html) that can be converted to a mesh: Mesh, Curve, Surface, Font and Metaball.
* Go to `File` > `Export` > `BBMOD (*.bbmod)`
* Select the attributes that you want to include in the vertex format. Note that
`Bones` and `Ids` are currently not supported.
* Export the model using `Export BBMOD`
* Load the model by calling `var mymodel = BBMOD_Model.from_file("mymodel.bbmod");`
