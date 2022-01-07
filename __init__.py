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

# Mesh-like object types (the ones that can be converted to mesh)
meshlike_types = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}

def matrix_flatten(matrix):
    val = []
    for row in matrix:
        val.extend(row[:])
    return val

def write_bbmod(context, filepath, vertex_format):
    object_list = context.selected_objects
    model_list = [object for object in object_list if object.type in meshlike_types]

    # Type and version
    header_bytes = bytearray("bbmod\0", 'utf-8')    # BBMOD identifier
    header_bytes.extend(pack('B', BBMOD_version))   # BBMOD version

    # Write vertex format
    vertex_format_bytes = bytearray()
    format_bools = [attrib in vertex_format for attrib in vertex_attributes]
    vertex_format_bytes.extend(pack('B' * len(format_bools), *format_bools))

    # Write meshes
    meshes_bytes = bytearray()
    meshes_bytes.extend(pack('I', len(model_list)))
    for mesh_object in model_list:
        # Create a triangulated copy of the mesh with modifiers applied
        mod_tri = mesh_object.modifiers.new('triangulate', 'TRIANGULATE')
        depsgraph = bpy.context.evaluated_depsgraph_get()
        # TODO isn't this context just the context argument?
        obj_eval = mesh_object.evaluated_get(depsgraph)
        mesh_eval = bpy.data.meshes.new_from_object(obj_eval)
        del obj_eval
        mesh_object.modifiers.remove(mod_tri)

        mesh_bytes = bytearray()

        # Per-mesh data (see BBMOD_Mesh.from_buffer)
        mesh_bytes.extend(pack('I', 0))       # Material index
        mesh_bytes.extend(pack('I', len(mesh_eval.polygons) * 3))

        for poly in mesh_eval.polygons:
            for li in poly.loop_indices:
                loop = mesh_eval.loops[li]
                vi = loop.vertex_index
                vertex = mesh_eval.vertices[vi]

                if 'vertices' in vertex_format:
                    mesh_bytes.extend(pack('fff', *vertex.co[:]))
                if 'normals' in vertex_format:
                    mesh_bytes.extend(pack('fff', *vertex.normal[:]))
                if 'texcoords' in vertex_format:
                    mesh_bytes.extend(pack('ff', *[0, 0]))
                if 'colors' in vertex_format:
                    mesh_bytes.extend(pack('BBBB', *([255, 255, 255, 255])))  # white
                if 'tangentw' in vertex_format:
                    mesh_bytes.extend(pack('fff', *loop.tangent[:]))
                    mesh_bytes.extend(pack('f', loop.bitangent_sign))
                if 'bones' in vertex_format:
                    pass
                if 'ids' in vertex_format:
                    pass

        meshes_bytes.extend(mesh_bytes)

        bpy.data.meshes.remove(mesh_eval)

    # Node count and root node
    node_name = bytearray("RootNode" + "\0", 'utf-8')
    #node_matrix = Matrix()
    #values = matrix_flatten(node_matrix)
    node_dq = [0, 0, 0, 1, 0, 0, 0, 0]

    node_bytes = bytearray()
    node_bytes.extend(pack('I', 1))             # NodeCount
    node_bytes.extend(node_name)
    node_bytes.extend(pack('I', 0))             # Node Index
    node_bytes.extend(pack('?', True))          # IsBone
    #node_bytes.extend(pack('?', True))          # Visible
    node_bytes.extend(pack('f' * 8, *node_dq))  # Node DQ

    node_bytes.extend(pack('I', len(model_list)))# Mesh count

    for mesh_index in range(len(model_list)):
        node_bytes.extend(pack('I', mesh_index))# Mesh indices

    node_bytes.extend(pack('I', 0))             # Child count

    # Skeleton
    skeleton_bytes = bytearray()
    skeleton_bytes.extend(pack('I', 0))         # Bone count

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

    vertex_format: EnumProperty(
        name="Vertex Format",
        description="Choose between two items",
        items=(
            ('vertices', "Vertices", "Whether the vertex format has vertices"),
            ('normals', "Normals", "Whether the vertex format has normals"),
            ('texcoords', "UVs", "Whether the vertex format has uvs"),
            ('colors', "Colors", "Whether the vertex format has vertex colors"),
            ('tangentw', "TangentW", "Whether the vertex format has tangent and bitangent sign"),
            #('bones', "Bones", "Whether the vertex format has vertex weights and bone indices"),
            #('ids', "Ids", "Whether the vertex format has ids for dynamic batching"),
        ),
        default={'vertices', 'normals', 'texcoords', 'colors', 'tangentw'},
        options={'ENUM_FLAG'},
    )

    def execute(self, context):
        return write_bbmod(context, self.filepath, self.vertex_format)


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
