import bpy
from math import radians
from bpy.types import Panel, Scene, Operator, PropertyGroup, Object
from bpy.props import PointerProperty, FloatProperty


class ToolSettings(PropertyGroup):
    camera: PointerProperty(type=Object)
    empty: PointerProperty(type=Object)
    selected_object: PointerProperty(type=Object)


class TOOL_OT_initialize(Operator):
    bl_idname = "camera.init"
    bl_label = "Initialize camera"
    bl_description = "Add camera tracked to empty"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        camera_name = "3DCamera"
        empty_name = "3DEmpty"

        # Create empty
        empty_data = bpy.data.objects.get(empty_name)
        if empty_data is None:
            new_empty_object = bpy.data.objects.new(empty_name, empty_data)
            context.scene.collection.objects.link(new_empty_object)

        # Create camera
        camera_data = bpy.data.cameras.get(camera_name)
        if camera_data is None:
            camera_data = bpy.data.cameras.new(name=camera_name)
            camera_data.type = "ORTHO"

        # Track camera to empty
        empty_object = bpy.data.objects.get(empty_name)
        camera_object = bpy.data.objects.get(camera_name)
        if camera_object is None:
            camera_object = bpy.data.objects.new(camera_name, camera_data)
            camera_object.parent = empty_object
            constraint = camera_object.constraints.new(type="TRACK_TO")
            constraint.target = empty_object
            context.scene.collection.objects.link(camera_object)

        context.scene.camera = camera_object

        # Set tool settings camera and empty
        context.scene.settings.camera = camera_object
        context.scene.settings.empty = empty_object

        bpy.ops.view3d.view_camera()

        self.report({"INFO"}, "Camera Initialized")

        return {"FINISHED"}


class TOOL_OT_set_target(Operator):
    bl_idname = "camera.target"
    bl_label = "Set camera target"
    bl_description = "Set empty to selected object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.settings
        return (
            settings.selected_object is not None
            and settings.camera is not None
            and settings.empty is not None
            and settings.selected_object.location != settings.empty.location
        )

    def execute(self, context):
        settings = context.scene.settings

        selected_obj = settings.selected_object
        obj_location = selected_obj.location

        empty = settings.empty
        empty.location = obj_location

        self.report({"INFO"}, "Empty set to %r" % obj_location)

        return {"FINISHED"}


class TOOL_OT_position_camera(Operator):
    bl_idname = "camera.position"
    bl_label = "Set camera position"
    bl_description = "Set empty x rotation"
    bl_options = {"REGISTER", "UNDO"}
    angle: FloatProperty(name="Angle")

    @classmethod
    def poll(cls, context):
        settings = context.scene.settings
        return settings.camera is not None and settings.empty is not None

    def execute(self, context):
        settings = context.scene.settings

        empty = settings.empty
        empty.rotation_euler[0] = radians(self.angle)

        self.report({"INFO"}, "Empty x rotation set to %r" % self.angle)

        return {"FINISHED"}


class TOOL_OT_rotate_camera(Operator):
    bl_idname = "camera.rotate"
    bl_label = "Rotate camera"
    bl_description = "Set empty z rotation"
    bl_options = {"REGISTER", "UNDO"}
    angle: FloatProperty(name="Angle")

    @classmethod
    def poll(cls, context):
        settings = context.scene.settings
        return settings.camera is not None and settings.empty is not None

    def execute(self, context):
        settings = context.scene.settings

        empty = settings.empty
        empty.rotation_euler[2] = radians(self.angle)

        self.report({"INFO"}, "Empty z rotation set to %r" % self.angle)

        return {"FINISHED"}


class VIEW3D_PT_camera_coverage(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Camera Coverage"
    bl_label = "Camera Coverage"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        settings = context.scene.settings

        box = layout.box()
        row = box.row()
        row.prop(settings, "camera", text="Camera")
        row.enabled = False
        row = box.row()
        row.prop(settings, "empty", text="Empty")
        row.enabled = False
        row = box.row()
        row.operator("camera.init", text="Initialize")

        box = layout.box()
        row = box.row()
        row.prop(settings, "selected_object", text="Object")
        row = box.row()
        row.operator("camera.target", text="Set Target")

        box = layout.box()
        row = box.row()
        row.alignment = "CENTER"
        row.label(text="Position", icon="LIGHT_AREA")
        row = box.grid_flow(even_columns=True)
        row.operator("camera.position", text="", icon="ALIGN_TOP").angle = 45.0
        row.operator("camera.position", text="", icon="ALIGN_MIDDLE").angle = 0.0
        row.operator("camera.position", text="", icon="ALIGN_BOTTOM").angle = -45.0

        box = layout.box()
        row = box.row()
        row.alignment = "CENTER"
        row.label(text="Rotation")
        row = box.grid_flow(row_major=True, columns=3, even_columns=True)
        row.operator("camera.rotate", text="").angle = 225.0
        row.operator("camera.rotate", text="", icon="TRIA_UP").angle = 180.0
        row.operator("camera.rotate", text="").angle = 135.0
        row.operator("camera.rotate", text="", icon="TRIA_LEFT").angle = 270.0
        row.label(text="")
        row.operator("camera.rotate", text="", icon="TRIA_RIGHT").angle = 90.0
        row.operator("camera.rotate", text="").angle = 315.0
        row.operator("camera.rotate", text="", icon="TRIA_DOWN").angle = 0.0
        row.operator("camera.rotate", text="").angle = 45.0


classes = (
    ToolSettings,
    TOOL_OT_initialize,
    TOOL_OT_set_target,
    TOOL_OT_position_camera,
    TOOL_OT_rotate_camera,
    VIEW3D_PT_camera_coverage,
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
