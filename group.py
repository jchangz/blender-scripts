import bpy


class WM_OT_myop(bpy.types.Operator):
    """Tooltip"""

    bl_idname = "wm.myop"
    bl_label = "Simple Object Operator"

    name: bpy.props.StringProperty(name="Name", default="")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Custom_MT_Menu(bpy.types.Menu):
    bl_label = "Custom Menu"
    bl_idname = "OBJECT_MT_custom_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("wm.myop")


def register():
    bpy.utils.register_class(Custom_MT_Menu)
    bpy.utils.register_class(WM_OT_myop)


def unregister():
    bpy.utils.unregister_class(Custom_MT_Menu)
    bpy.utils.unregister_class(WM_OT_myop)


if __name__ == "__main__":
    register()

    # The menu can also be called from scripts
    bpy.ops.wm.call_menu(name=Custom_MT_Menu.bl_idname)
