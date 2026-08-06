import bpy
from math import radians, pi, tan
from mathutils import Vector, Matrix
from bpy.types import Panel, Scene, Operator, PropertyGroup, Object
from bpy.props import (
    PointerProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    BoolProperty,
)


class ToolSettings(PropertyGroup):
    camera: PointerProperty(type=Object)
    empty: PointerProperty(type=Object)
    selected_object: PointerProperty(type=Object)
    keyframes_enable: BoolProperty(name="Enable Keyframes", default=False)
    keyframes_position: IntProperty(
        name="Keyframe", min=1, default=10, step=10, max=250
    )
    padding_factor: FloatProperty(name="Camera Padding", min=1, default=1.2, max=5)


class TOOL_OT_fittocam(Operator):
    bl_idname = "camera.fit"
    bl_label = "Fit Selected"
    bl_description = "add camera tracked to empty"
    bl_options = {"REGISTER", "UNDO"}
    padding: FloatProperty(name="Padding")

    def execute(self, context):
        camera_name = "3DCamera"
        empty_name = "3DEmpty"

        # Set the camera position to the object's center (maintain current rotation)
        # The camera should be positioned along its local Z-axis to look at the object
        # For simplicity, we assume the camera is pointing towards the object's center.
        # A common setup is a top, side, or front view. We'll set the camera's location
        # to the object's origin and move it back along its local -Z axis.

        # Calculate object's bounding box dimensions in world space
        # The bounding box corners are in local space, need to transform to world space
        target_obj = context.selected_objects[0]
        matrix_world = target_obj.matrix_world
        bbox_corners = [
            matrix_world @ Vector(corner) for corner in target_obj.bound_box
        ]
        bbox_min = Vector(
            [
                min(c.x for c in bbox_corners),
                min(c.y for c in bbox_corners),
                min(c.z for c in bbox_corners),
            ]
        )
        bbox_max = Vector(
            [
                max(c.x for c in bbox_corners),
                max(c.y for c in bbox_corners),
                max(c.z for c in bbox_corners),
            ]
        )

        # Calculate the size of the bounding box
        size = bbox_max - bbox_min

        # Determine the maximum dimension to fit the object
        max_dim = max(size.x, size.y, size.z)

        # Apply padding
        ortho_scale = max_dim * (1 + self.padding)

        # Adjust ortho scale based on camera aspect ratio vs object aspect ratio to ensure it fits both dimensions
        render_width = context.scene.render.resolution_x
        render_height = context.scene.render.resolution_y
        camera_aspect = render_width / render_height

        min_x = min(v.x for v in bbox_corners)
        max_x = max(v.x for v in bbox_corners)
        min_y = min(v.y for v in bbox_corners)
        max_y = max(v.y for v in bbox_corners)
        min_z = min(v.z for v in bbox_corners)
        max_z = max(v.z for v in bbox_corners)

        obj_center = Vector(
            [(min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2]
        )
        obj_width = max_x - min_x
        obj_height = max_y - min_y  # Assuming Y is up, adjust if Z is up
        camera_obj = bpy.data.objects.get(camera_name)
        cam_data = bpy.data.cameras.get(camera_name)

        if cam_data.type == "ORTHO":
            # If the object is wider or taller relative to the camera's aspect ratio, adjust the scale
            object_aspect = size.x / size.y if size.y > 0 else 1
            if object_aspect > camera_aspect:
                # Object is wider than camera view, scale by width
                ortho_scale = size.x * (1 + self.padding)
            else:
                # Object is taller than camera view, scale by height
                ortho_scale = size.y * (1 + self.padding)

            # Set the camera's orthographic scale
            cam_data.ortho_scale = ortho_scale
            distance = (
                max(size.x, size.y, size.z) * 1.5
            )  # A sufficient distance to avoid clipping
            camera_obj.location -= camera_obj.matrix_world.to_quaternion() @ Vector(
                (0, 0, distance)
            )

            # Adjust clipping end to ensure the entire object is rendered
            cam_data.clip_end = distance + max(
                size.x, size.y, size.z
            )  # Ensure everything is visible
            cam_data.clip_start = 0.1
            #
            # # Position the camera to center the object
            # camera_obj.location = (
            #     obj_center
            #     - camera_obj.matrix_world.to_quaternion() @ Vector((0, 0, 10))
            # )  # Arbitrary distance for ortho
            # camera_obj.rotation_euler = (0, 0, 0)

        self.report({"INFO"}, "Initialized Camera")

        return {"FINISHED"}


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
        if settings.keyframes_enable:
            empty.keyframe_insert(
                data_path="rotation_euler", frame=settings.keyframes_position
            )

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
        if settings.keyframes_enable:
            empty.keyframe_insert(
                data_path="rotation_euler", frame=settings.keyframes_position
            )

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
        row.label(text="Keyframe")
        row = box.row()
        row.prop(settings, "keyframes_enable", text="")
        row.label(text="Enable")
        row = box.row()
        row.prop(settings, "keyframes_position", text="")
        row.enabled = settings.keyframes_enable
        row = box.row()

        box = layout.box()
        row = box.row()
        row.alignment = "CENTER"
        row.label(text="Position", icon="LIGHT_AREA")
        row = box.grid_flow(even_columns=True)
        row.operator("camera.position", text="", icon="ALIGN_TOP").angle = -45.0
        row.operator("camera.position", text="", icon="ALIGN_MIDDLE").angle = 0.0
        row.operator("camera.position", text="", icon="ALIGN_BOTTOM").angle = 45.0

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

        cam = settings.camera.data
        box = layout.box()
        row = box.row()
        row.prop(cam, "ortho_scale")

        box = layout.box()
        row = box.row()
        row.prop(settings, "padding_factor", text="Padding")
        row = box.row()
        row.operator("camera.fit", text="Fit").padding = settings.padding_factor


classes = (
    ToolSettings,
    TOOL_OT_initialize,
    TOOL_OT_set_target,
    TOOL_OT_position_camera,
    TOOL_OT_rotate_camera,
    TOOL_OT_fittocam,
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
