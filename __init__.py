bl_info = {
    "name": "Export BBMOD",
    "description": "Export to BBMOD",
    "author": "Bart Teunis",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "File > Export",
    "warning": "", # used for warning icon and text in addons panel
    "doc_url": "",
    "category": "Import-Export"}

import bpy
from mathutils import Matrix
from struct import pack

BBMOD_version = 3

vertex_attributes = [
    'vertices',
    'normals',
    'texcoords',
    'colors',
    'tangentw',
    'bones',
    'ids',
]

def matrix_flatten(matrix):
    val = []
    for row in matrix:
        val.extend(row[:])
    return val

def write_bbmod(context, filepath, use_some_setting, vertex_format):
    object_list = context.selected_objects
    model_list = [object for object in object_list if object.type=='MESH']
    # TODO "if object in 'meshlike' types"

    # Type and version
    header_bytes = bytearray("bbmod\0", 'utf-8')    # BBMOD identifier
    header_bytes.extend(pack('B', BBMOD_version))   # BBMOD version

    # Write vertex format
    format_bools = [attrib in vertex_format for attrib in vertex_attributes]
    vertex_format_bytes = bytearray()
    vertex_format_bytes.extend(pack('?' * len(format_bools), *format_bools))

    # Write meshes
    meshes_bytes = bytearray()
    meshes_bytes.extend(pack('I', len(model_list)))
    for mesh_object in model_list:
        mesh = mesh_object.data
        meshes_bytes.extend(pack('I', len(mesh.polygons) * 3))

        # TODO Write vertex buffer data using the format provided

        meshes_bytes.extend(pack('I', 0))       # Material index

    # Node count and root node
    node_name = bytearray("RootNode" + "\0", 'utf-8')
    node_matrix = Matrix()
    values = matrix_flatten(node_matrix)

    node_bytes = bytearray()
    node_bytes.extend(pack('I', 1))             # NodeCount
    node_bytes.extend(node_name)
    node_bytes.extend(pack('I', 0))             # Node Index
    node_bytes.extend(pack('?', True))          # IsBone
    node_bytes.extend(pack('?', True))          # Visible
    node_bytes.extend(pack('f' * 16, *values))  # Matrix

    node_bytes.extend(pack('I', len(model_list)))# Mesh count

    node_bytes.extend(pack('I', 0))             # Mesh indices

    node_bytes.extend(pack('I', 0))             # Child count

    # Skeleton
    skeleton_bytes = bytearray()
    skeleton_bytes.extend(pack('I', 0))

    # Materials
    material_bytes = bytearray()
    material_bytes.extend(pack('I', 1))         # MaterialCount
    material_bytes.extend(bytearray("DefaultMaterial" + "\0", 'utf-8'))

    # Write everything to file
    with open(filepath, "wb") as file:
        file.write(header_bytes)
        file.write(vertex_format_bytes)
        file.write(meshes_bytes)
        file.write(node_bytes)
        file.write(skeleton_bytes)
        file.write(material_bytes)

    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ExportBBMOD(Operator, ExportHelper):
    """Export a selection of the current scene to BBMOD"""
    bl_idname = "export_scene.bbmod"
    bl_label = "Export BBMOD"

    # ExportHelper mixin class uses this
    filename_ext = ".bbmod"

    filter_glob: StringProperty(
        default="*.bbmod",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    vertex_format: EnumProperty(
        name="Vertex Format",
        description="Choose between two items",
        items=(
            ('vertices', "Vertices", "Whether the vertex format has vertices"),
            ('normals', "Normals", "Whether the vertex format has normals"),
            ('texcoords', "UVs", "Whether the vertex format has uvs"),
            ('colors', "Colors", "Whether the vertex format has vertex colors"),
            ('tangentw', "TangentW", "Whether the vertex format has tangent and bitangent sign"),
            ('bones', "Bones", "Whether the vertex format has vertex weights and bone indices"),
            ('ids', "Ids", "Whether the vertex format has ids for dynamic batching"),
        ),
        default={'vertices', 'normals', 'texcoords', 'colors', 'tangentw'},
        options={'ENUM_FLAG'},
    )

    def execute(self, context):
        return write_bbmod(context, self.filepath, self.use_setting, self.vertex_format)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportBBMOD.bl_idname, text="BBMOD (*.bbmod)")


def register():
    bpy.utils.register_class(ExportBBMOD)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportBBMOD)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
