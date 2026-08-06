import bpy
import math
from mathutils import Vector

        if cam_data.type == "PERSP":
            aspect_ratio = (
                context.scene.render.resolution_x / context.scene.render.resolution_y
            )
            print(aspect_ratio)
            # Calculate distance based on horizontal and vertical dimensions
            half_fov_x = cam_data.angle_x / 2.0
            half_fov_y = cam_data.angle_y / 2.0

            dist_x = (
                (obj_width * self.padding / 2.0) / tan(half_fov_x)
                if half_fov_x > 0
                else 0
            )
            dist_y = (
                (obj_height * self.padding / 2.0) / tan(half_fov_y)
                if half_fov_y > 0
                else 0
            )

            # Take the maximum distance to ensure fitting both dimensions
            distance = max(dist_x, dist_y)

            # Position the camera
            camera_obj.location = (
                obj_center
                - camera_obj.matrix_world.to_quaternion() @ Vector((0, 0, distance))
            )

            # Point the camera at the object's center
            look_at_matrix = Matrix.Translation(obj_center) @ Matrix.Rotation(
                pi, 4, "X"
            )  # Adjust for camera direction
            camera_obj.rotation_euler = look_at_matrix.inverted().to_euler()

def fit_ortho_camera_to_object(camera_obj, target_obj, padding=0.1):
    """
    Fits an orthographic camera to a target object with specified padding.

    :param camera_obj: The camera object (bpy.types.Object).
    :param target_obj: The object to fit within the camera view (bpy.types.Object).
    :param padding: The desired padding as a fraction (e.g., 0.1 for 10% padding).
    """
    scene = bpy.context.scene
    cam_data = camera_obj.data

    # Ensure the camera is orthographic
    cam_data.type = "ORTHO"

    # Set the camera position to the object's center (maintain current rotation)
    # The camera should be positioned along its local Z-axis to look at the object
    # For simplicity, we assume the camera is pointing towards the object's center.
    # A common setup is a top, side, or front view. We'll set the camera's location
    # to the object's origin and move it back along its local -Z axis.

    # Calculate object's bounding box dimensions in world space
    # The bounding box corners are in local space, need to transform to world space
    matrix_world = target_obj.matrix_world
    bbox_corners = [matrix_world @ Vector(corner) for corner in target_obj.bound_box]
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
    ortho_scale = max_dim * (1 + padding)

    # Adjust ortho scale based on camera aspect ratio vs object aspect ratio to ensure it fits both dimensions
    render_width = scene.render.resolution_x
    render_height = scene.render.resolution_y
    camera_aspect = render_width / render_height

    # If the object is wider or taller relative to the camera's aspect ratio, adjust the scale
    object_aspect = size.x / size.y if size.y > 0 else 1
    if object_aspect > camera_aspect:
        # Object is wider than camera view, scale by width
        ortho_scale = size.x * (1 + padding)
    else:
        # Object is taller than camera view, scale by height
        ortho_scale = size.y * (1 + padding)

    # Set the camera's orthographic scale
    cam_data.ortho_scale = ortho_scale

    # Position the camera at the center of the object's bounding box and move it back
    camera_obj.location = (bbox_max + bbox_min) / 2.0

    # Move the camera back along its local negative Z axis enough to cover the object depth
    # The distance needs to be at least half the object's depth plus some buffer.
    # You may need to adjust the initial camera rotation if not already set (e.g. looking down an axis)
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

    print(f"Orthographic scale set to: {cam_data.ortho_scale}")


# --- Example Usage ---
# Get the active camera and a target object (e.g., the default cube)
camera_object = bpy.context.scene.camera

# Check if an object is selected to be the target
target_objects = bpy.context.selected_objects
if target_objects:
    target_object = target_objects[0]  # Use the first selected object as target
    fit_ortho_camera_to_object(camera_object, target_object, padding=0.2)  # 20% padding
else:
    print("Please select a target object.")
