import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty

# Use a list to make iteration and clearing easier
custom_keymap = []


class ExportOperator(Operator):
    bl_idname = "export.selection_to_gltf"
    bl_label = "Export glTF 2.0"
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")

    filename: StringProperty(subtype="FILE_NAME")

    filter_glob: StringProperty(default="*.glb", options={"HIDDEN"})

    check_existing: BoolProperty(name="Check Existing", default=True)

    export_apply: BoolProperty(name="Apply Modifiers", default=True)

    export_materials: EnumProperty(
        name="Materials",
        items=[
            ("EXPORT", "Export", ""),
            ("PLACEHOLDER", "Placeholder", ""),
            ("NONE", "None", ""),
        ],
        default="PLACEHOLDER",
    )

    @classmethod
    def poll(cls, context):
        return (
            context.selected_objects is not None and len(context.selected_objects) > 0
        )

    def execute(self, context):
        # The 'self.options.is_invoke' check was removed as it's not standard API

        # Ensure filepath is set (crucial if called via shortcut)
        if not self.filepath:
            self.report({"ERROR"}, "No file path specified")
            return {"CANCELLED"}

        bpy.ops.export_scene.gltf(
            filepath=self.filepath,
            use_selection=True,
            export_apply=self.export_apply,
            export_materials=self.export_materials,
            export_animations=False,
            export_morph=False,
        )

        self.report({"INFO"}, "Exported to: " + self.filepath)

        return {"FINISHED"}

    def invoke(self, context, event):
        if bpy.data.filepath:
            self.filepath = os.path.splitext(bpy.data.filepath)[0] + ".glb"
        else:
            self.filepath = "untitled.glb"

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        box = layout.box()
        box.label(text="Export Settings", icon="EXPORT")

        col = box.column()
        col.prop(self, "export_apply")
        col.prop(self, "export_materials")


def register():
    bpy.utils.register_class(ExportOperator)

    global custom_keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new(
            ExportOperator.bl_idname, type="E", value="PRESS", shift=True, ctrl=True
        )
        custom_keymap.append((km, kmi))


def unregister():
    global custom_keymap

    # Properly remove keybinds
    for km, kmi in custom_keymap:
        km.keymap_items.remove(kmi)
    custom_keymap.clear()

    bpy.utils.unregister_class(ExportOperator)


if __name__ == "__main__":
    register()
