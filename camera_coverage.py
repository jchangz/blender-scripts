import bpy
from bpy.types import Panel, Operator


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

        bpy.ops.view3d.view_camera()

        self.report({"INFO"}, "Camera Initialized")

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

        row = layout.row()
        row.operator("camera.init", text="Initialize")


classes = (
    TOOL_OT_initialize,
    VIEW3D_PT_camera_coverage,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
