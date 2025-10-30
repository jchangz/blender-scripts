import bpy
import bmesh
import os
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty

custom_keymap = None


class ExportOperator(Operator):
    bl_idname = "export.selection_to_gltf"
    bl_label = "Export glTF 2.0"

    filepath: StringProperty(subtype="FILE_PATH")

    filename: StringProperty(subtype="FILE_NAME")

    filter_glob: StringProperty(default="*.glb")

    check_existing: BoolProperty(name="Check Existing", default=True)

    apply_modifiers: BoolProperty(name="Apply Modifiers")

    export_materials: EnumProperty(
        name="Materials",
        items=[
            ("EXPORT", "Export", ""),
            ("PLACEHOLDER", "Placeholder", ""),
            ("NONE", "None", ""),
        ],
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        if self.options.is_invoke:
            if not self.poll(context):
                self.report({"ERROR"}, "Invalid context")

                return {"CANCELLED"}

        bpy.ops.export_scene.gltf(
            filepath=self.filepath,
            use_selection=True,
            export_apply=self.apply_modifiers,
            export_materials=self.export_materials,
            export_animations=False,
            export_morph=False,
        )

        self.report({"INFO"}, "Exported to: " + self.filepath)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)

        blend_file_path = bpy.data.filepath
        if blend_file_path:
            basename = os.path.basename(blend_file_path)
            self.filename = os.path.splitext(basename)[0] + ".glb"
        else:
            self.filename = "untitled.glb"

        return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Export Settings")

        row = col.row()
        row.prop(self, "apply_modifiers")

        row = col.row()
        row.prop(self, "export_materials")


def register():
    bpy.utils.register_class(ExportOperator)

    key_config = bpy.context.window_manager.keyconfigs.addon
    if key_config:
        key_map = key_config.keymaps.new(name="3D View", space_type="VIEW_3D")
        key_entry = key_map.keymap_items.new(
            "export.selection_to_gltf",
            type="Q",
            value="PRESS",
            shift=True,
        )
        custom_keymap = (key_map, key_entry)


def unregister():
    for key_map, key_entry in custom_keymap:
        key_map.keymap_items.remove(key_entry)
    custom_keymap.clear()

    bpy.utils.unregister_class(ExportOperator)


if __name__ == "__main__":
    register()
