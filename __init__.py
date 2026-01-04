import bpy
import subprocess
import os
import sys
import time
from bpy.types import Operator, AddonPreferences
from bpy.props import EnumProperty

ADDON_ID_NAME = __name__

def _do_restart(reopen_current_file=True):
    if reopen_current_file:
        current_blend_path = bpy.data.filepath
        relaunch_command = [sys.argv[0]] + ([current_blend_path] if current_blend_path else [])
    else:
        relaunch_command = [sys.argv[0]]
    try:
        # Delay the restart to ensure current instance fully closes first
        # This prevents race conditions with GPU cache files and other resources
        if os.name == 'nt':
            # Windows: Properly quote paths with spaces
            quoted_command = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in relaunch_command)
            delay_command = f'timeout /t 1 /nobreak >nul && start "" {quoted_command}'
            subprocess.Popen(delay_command, shell=True)
        else:
            # Linux/Mac: Use sleep command
            delay_command = ['sh', '-c', f'sleep 1 && {" ".join(relaunch_command)}']
            subprocess.Popen(delay_command)
        bpy.ops.wm.quit_blender()
    except Exception as error_instance:
        print(f"Failed to restart Blender: {error_instance}")

class RestartAddonPreferences(AddonPreferences):
    bl_idname = ADDON_ID_NAME
    save_prompt_behavior: EnumProperty(
        name="Restart Behavior",
        description="How to handle unsaved changes when restarting",
        items=[
            ('PROMPT', "Prompt before Restarting", "Show a confirmation dialog with options"),
            ('SAVE', "Save and Restart", "Save changes without prompting and then restart"),
            ('DISCARD', "Discard and Restart", "Discard changes without prompting and then restart"),
        ],
        default='PROMPT',
    )
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "save_prompt_behavior")

class WM_OT_restart_action(Operator):
    bl_idname = "wm.restart_action"
    bl_label = "Restart Action"
    bl_options = {'INTERNAL'}
    action: EnumProperty(
        items=[
            ('SAVE', "Save", ""), 
            ('DONT_SAVE', "Don't Save", ""), 
        ]
    )
    def modal(self, context, event):
        if context.blend_data.filepath:  # Wait until file is saved
            _do_restart(reopen_current_file=True)
            return {'FINISHED'}
        return {'PASS_THROUGH'}
    def execute(self, context):
        if self.action == 'SAVE':
            if not context.blend_data.filepath:
                bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                bpy.ops.wm.save_mainfile()
                _do_restart(reopen_current_file=True)
                return {'FINISHED'}
        elif self.action == 'DONT_SAVE':
            # Just restart - if there's a saved file, Blender will load the last saved version
            # If unsaved, Blender will start fresh
            # We pass the filepath so saved files reopen at their last saved state
            _do_restart(reopen_current_file=bool(bpy.data.filepath))
            return {'FINISHED'}
        return {'CANCELLED'}

class WM_OT_confirm_restart_dialog(Operator):
    bl_idname = "wm.confirm_restart_dialog"
    bl_label = "Save changes before restarting?"
    bl_options = {'INTERNAL'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        if not context.blend_data.filepath:
            box = col.box()
            box.alert = True
            box.label(text="Untitled.blend")
        else:
            filename = os.path.basename(context.blend_data.filepath)
            col.label(text=filename)
        col.separator()
        master_row = col.row()
        split = master_row.split(factor=0.78)
        left_row = split.row()
        left_row.operator("wm.restart_action", text="Save").action = 'SAVE'
        left_row.operator("wm.restart_action", text="Don't Save").action = 'DONT_SAVE'
        right_row = split.row()
        right_row.template_popup_confirm("wm.doc_view", text="", cancel_text="Cancel")
    def execute(self, context):
        return {'CANCELLED'}

class WM_OT_restart_blender(Operator):
    bl_idname = "wm.restart_blender"
    bl_label = "Restart"
    bl_description = "Restarts Blender"
    def execute(self, context):
        # Get preferences safely, default to PROMPT if addon not installed
        try:
            prefs = context.preferences.addons[ADDON_ID_NAME].preferences
            behavior = prefs.save_prompt_behavior
        except KeyError:
            behavior = 'PROMPT'
        is_dirty = bpy.data.is_dirty
        if not is_dirty:
            _do_restart(reopen_current_file=True)
            return {'FINISHED'}
        if behavior == 'PROMPT':
            bpy.ops.wm.confirm_restart_dialog('INVOKE_DEFAULT')
            return {'FINISHED'}
        if behavior == 'SAVE':
            if not context.blend_data.filepath:
                bpy.ops.wm.confirm_restart_dialog('INVOKE_DEFAULT')
            else:
                bpy.ops.wm.save_mainfile()
                _do_restart(reopen_current_file=True)
        elif behavior == 'DISCARD':
            # Just restart - if there's a saved file, it will load at last saved state
            # If unsaved, it will start fresh
            _do_restart(reopen_current_file=bool(bpy.data.filepath))
        return {'FINISHED'}

def draw_restart_menu_item(self, context):
    self.layout.separator()
    self.layout.operator(WM_OT_restart_blender.bl_idname, text="Restart", icon='FILE_REFRESH')

classes_to_register = (
    RestartAddonPreferences,
    WM_OT_restart_action,
    WM_OT_confirm_restart_dialog,
    WM_OT_restart_blender,
)

def register():
    for cls in classes_to_register:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file.append(draw_restart_menu_item)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        km.keymap_items.new(WM_OT_restart_blender.bl_idname, 'R', 'PRESS', ctrl=True, alt=True, shift=True)

def unregister():
    for cls in reversed(classes_to_register):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
    try:
        bpy.types.TOPBAR_MT_file.remove(draw_restart_menu_item)
    except (ValueError, AttributeError):
        pass
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km in kc.keymaps:
            items_to_remove = [kmi for kmi in km.keymap_items if kmi.idname == WM_OT_restart_blender.bl_idname]
            for kmi in items_to_remove:
                km.keymap_items.remove(kmi)