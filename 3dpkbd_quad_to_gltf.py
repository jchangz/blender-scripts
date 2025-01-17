import bpy
import os
import bmesh
import mathutils
from bpy.types import Panel, Scene, Operator, PropertyGroup
from bpy.props import StringProperty, IntProperty, PointerProperty
from math import radians


class ToolSettings(PropertyGroup):
    export_path: StringProperty(name="File", subtype="FILE_PATH")


class TOOL_OT_3dp_subdivision(Operator):
    bl_idname = "3dp.subd"
    bl_label = "subd"
    bl_description = "transform, rotate and separate loose parts"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object.mode == "OBJECT"
            and len(context.selected_objects) == 1
            and len([m for m in context.active_object.modifiers if m.type == "SUBSURF"])
            < 1
        )

    def execute(self, context):

        obj = context.active_object
        mod = obj.modifiers.new("Subdivision", "SUBSURF")
        mod.levels = 1
        mod.render_levels = 1

        return {"FINISHED"}


class TOOL_OT_3dp_rename(Operator):
    bl_idname = "3dp.rename"
    bl_label = "rename"
    bl_description = "set name of object data"
    bl_options = {"REGISTER", "UNDO"}
    foo: StringProperty(name="Name")

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        selected = context.selected_objects
        for obj in selected:
            obj.name = self.foo
            obj.data.name = self.foo

        self.report({"INFO"}, "Object renamed: %r" % self.foo)

        return {"FINISHED"}


class TOOL_OT_3dp_unwrap(Operator):
    bl_idname = "3dp.unwrap"
    bl_label = "unwrap uv"
    bl_description = "project uv from view"
    bl_options = {"REGISTER", "UNDO"}
    foo: StringProperty(name="Direction")

    @classmethod
    def poll(cls, context):
        return context.active_object.mode == "EDIT"

    def execute(self, context):
        camera_data = bpy.data.cameras.get("3DPCamera")

        if camera_data is None:
            camera_data = bpy.data.cameras.new(name="3DPCamera")
            my_camera = bpy.data.objects.new("3DPCamera", camera_data)

            context.scene.collection.objects.link(my_camera)
        else:
            my_camera = bpy.data.objects["3DPCamera"]

        if context.active_object.data.total_face_sel == 0:
            self.report({"ERROR"}, "No Faces Selected")
            return {"CANCELLED"}

        camera_data.type = "ORTHO"

        cam_rot = mathutils.Euler((radians(90), 0.0, radians(-90)), "XYZ")
        cam_loc = (-9.4902, 0.0000, 0.0000)
        camera_data.ortho_scale = 2

        if self.foo == "top":
            cam_rot = mathutils.Euler((radians(6), 0.0, 0.0), "XYZ")
            cam_loc = (0.000, 0.6666, 5.0786)
            camera_data.ortho_scale = 5
        if self.foo == "bottom":
            cam_rot = mathutils.Euler((radians(180), 0.0, 0.0), "XYZ")
            cam_loc = (0.0000, -1.1414, -6.0376)
            camera_data.ortho_scale = 5

        my_camera.location = cam_loc
        my_camera.rotation_euler = cam_rot
        context.scene.camera = my_camera

        bpy.ops.view3d.view_camera()

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.update()

        bpy.ops.uv.project_from_view(
            camera_bounds=True, correct_aspect=False, scale_to_bounds=False
        )

        bpy.ops.view3d.view_camera()

        self.report({"INFO"}, "UV projected from %r view" % self.foo)

        return {"FINISHED"}


class TOOL_OT_3dp_export(Operator):
    bl_idname = "3dp.export"
    bl_label = "export gltf"
    filename_ext = ".glb"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0 and context.scene.settings.export_path

    def execute(self, context):
        bpy.ops.export_scene.gltf(
            filepath=bpy.path.abspath(context.scene.settings.export_path),
            use_selection=True,
            export_materials="PLACEHOLDER",
            export_animations=False,
            export_morph=False,
        )

        self.report({"INFO"}, "Exported to: " + context.scene.settings.export_path)

        return {"FINISHED"}


class VIEW3D_PT_3dpkbd_uv_panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "3DPKBD"
    bl_label = "3DPKBD Tool"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("3dp.subd", text="Add Subdivision")


class VIEW3D_PT_3dpkbd_uv(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3DPKBD"
    bl_label = "UV Project From View"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        row.operator("3dp.unwrap", text="Side").foo = "side"
        row.operator("3dp.unwrap", text="Top").foo = "top"
        row.operator("3dp.unwrap", text="Bottom").foo = "bottom"


class VIEW3D_PT_3dpkbd_rename(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3DPKBD"
    bl_label = "Rename"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        col = row.column()
        col.operator("3dp.rename", text="Top").foo = "top"
        col.operator("3dp.rename", text="Standard").foo = "standard"
        col.operator("3dp.rename", text="Vented").foo = "vented"
        col = row.column()
        col.operator("3dp.rename", text="Blocker").foo = "blocker"
        col.operator("3dp.rename", text="Blocker-1").foo = "blocker-1"
        col.operator("3dp.rename", text="Blocker-2").foo = "blocker-2"


class VIEW3D_PT_3dpkbd_export(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3DPKBD"
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout

        settings = context.scene.settings
        layout.row().prop(settings, "export_path", text="")
        layout.row().operator("3dp.export", text="Export GLTF")


classes = (
    ToolSettings,
    TOOL_OT_3dp_subdivision,
    TOOL_OT_3dp_unwrap,
    TOOL_OT_3dp_rename,
    TOOL_OT_3dp_export,
    VIEW3D_PT_3dpkbd_uv_panel,
    VIEW3D_PT_3dpkbd_uv,
    VIEW3D_PT_3dpkbd_rename,
    VIEW3D_PT_3dpkbd_export,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    Scene.settings = PointerProperty(type=ToolSettings)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    del Scene.settings


if __name__ == "__main__":
    register()
