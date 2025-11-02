bl_info = {
    "name": "Toggle Child Of Influence",
    "author": "M.Faruk ISIKER",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Animation",
    "description": "Toggle Child Of constraint influence, snap transforms, and add keyframes",
    "category": "Animation",
}

import bpy


def _find_child_of_constraint(obj):
    for constraint in obj.constraints:
        if constraint.type == 'CHILD_OF':
            return constraint
    return None


def _find_view3d_override(context):
    window = context.window
    screen = context.screen

    if window is None or screen is None:
        return None

    for area in screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type != 'WINDOW':
                continue
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    return {
                        "window": window,
                        "screen": screen,
                        "area": area,
                        "region": region,
                        "space": space,
                        "scene": context.scene,
                        "view_layer": context.view_layer,
                    }
    return None


class OBJECT_OT_toggle_child_of_influence(bpy.types.Operator):
    bl_idname = "object.toggle_child_of_influence"
    bl_label = "Toggle Child Of Influence"
    bl_description = (
        "Aktif objenin Child Of kısıtlamasının etkisini 1 ↔ 0 olarak değiştirir,"
        "objeyi imlece hizalar ve keyframe ekler"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None:
            return False
        return _find_child_of_constraint(obj) is not None

    def execute(self, context):
        obj = context.active_object
        child_of = _find_child_of_constraint(obj)

        if child_of is None:
            self.report({'ERROR'}, "Aktif objede Child Of kısıtlaması yok")
            return {'CANCELLED'}

        override = _find_view3d_override(context)
        if override is None:
            self.report({'ERROR'}, "VIEW_3D alanı bulunamadı. Lütfen 3B Görünüm açıkken deneyin.")
            return {'CANCELLED'}

        scene = context.scene
        cursor_prev = scene.cursor.location.copy()
        frame = scene.frame_current
        old_influence = child_of.influence
        new_influence = 0.0 if old_influence == 1.0 else 1.0

        try:
            with context.temp_override(**override):
                bpy.ops.view3d.snap_cursor_to_selected()

            child_of.keyframe_insert(data_path="influence", frame=frame)
            obj.keyframe_insert(data_path="location", frame=frame)

            child_of.influence = new_influence
            context.view_layer.update()

            with context.temp_override(**override):
                bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

            child_of.keyframe_insert(data_path="influence", frame=frame + 1)
            obj.keyframe_insert(data_path="location", frame=frame + 1)

        finally:
            scene.cursor.location = cursor_prev

        self.report(
            {'INFO'},
            f"Child Of etkisi {old_influence:.1f} → {new_influence:.1f} olarak değiştirildi",
        )
        return {'FINISHED'}


class VIEW3D_PT_child_of_panel(bpy.types.Panel):
    bl_label = "Child Of Etkisi"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animation"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("object.toggle_child_of_influence", icon='CONSTRAINT')


classes = (
    OBJECT_OT_toggle_child_of_influence,
    VIEW3D_PT_child_of_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()