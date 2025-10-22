import bpy
import bmesh
from bpy.types import Operator

custom_keymap = None


class OriginOperator(Operator):
    bl_idname = "object.vertex_to_origin"
    bl_label = "Origin to Selected Vertex"

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and len(context.selected_objects) == 1

    def execute(self, context):
        active_object = context.active_object
        mesh = active_object.data
        bm = bmesh.from_edit_mesh(mesh)

        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) == 0:
            self.report({"ERROR"}, "No Vertex Selected")
            return {"CANCELLED"}

        vert_position = selected_verts[0].co

        # Get the object's world matrix
        world_matrix = active_object.matrix_world

        # Calculate the global coordinates by multiplying the world matrix by the local coordinates
        world_vert_position = world_matrix @ vert_position

        # Set cursor location to new vertex position
        context.scene.cursor.location = world_vert_position

        # Switch to object mode to set origin
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        bpy.ops.object.mode_set(mode="EDIT")

        self.report({"INFO"}, "Object Origin Updated")

        return {"FINISHED"}


def register():
    bpy.utils.register_class(OriginOperator)

    key_config = bpy.context.window_manager.keyconfigs.addon
    if key_config:
        key_map = key_config.keymaps.new(name="3D View", space_type="VIEW_3D")
        key_entry = key_map.keymap_items.new(
            "object.vertex_to_origin",
            type="Q",
            value="PRESS",
            shift=True,
        )
        custom_keymap = (key_map, key_entry)


def unregister():
    for key_map, key_entry in custom_keymap:
        key_map.keymap_items.remove(key_entry)
    custom_keymap.clear()

    bpy.utils.unregister_class(OriginOperator)


if __name__ == "__main__":
    register()
