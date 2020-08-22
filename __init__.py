#MIT License

#Copyright (c) 2020 Mindaugas Petrikas

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# Add-on metadata
bl_info = {
    "name": "Send2Blend",
    "author": "Martynas Žiemys & Mindaugas Petrikas (Studio Petrikas)",
    "version": (2, 1),
    "blender": (2, 80, 0),
    "location": "Side(n) panel",
    "description": "Imports STLs from a folder. Updates the meshes of objects previously imported.",
    "warning": "",
    "wiki_url": "",
    "category": "import",
}

import bpy
import os
import time
import array
import logging
import sys
from stat import *
import threading
from itertools import chain
from io_mesh_stl import stl_utils, blender_utils
from bpy_extras.io_utils import (
        ImportHelper,
        axis_conversion,
        )
from mathutils import Matrix

def just_link_stl_data(object, faces, face_nors, points, global_matrix):
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')
    mesh = bpy.data.meshes.new(object.name)
    mesh.from_pydata(points, [], faces)
    if face_nors:
        mesh.create_normals_split()
        lnors = tuple(chain(*chain(*zip(face_nors, face_nors, face_nors))))
        mesh.loops.foreach_set("normal", lnors)
    mesh.transform(global_matrix)
    mesh.validate(clean_customdata=False)
    if face_nors:
        clnors = array.array('f', [0.0] * (len(mesh.loops) * 3))
        mesh.loops.foreach_get("normal", clnors)
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))
        mesh.use_auto_smooth = True
        mesh.free_normals_split()
    mesh.use_auto_smooth = True
    mesh.materials.append(None)
    object.data = mesh
    mesh.update()
    
def insert_sense(name):
    name = name.replace('.stl','')
    return name


class SCENE_OT_materials_to_objects(bpy.types.Operator):
    """Link all materials to objects instead of data"""
    bl_idname = "scene.mat_to_obj"
    bl_label = "Link Materials To Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        for o in context.scene.objects:
            for s in o.material_slots:
                if s.link == 'DATA':
                    m = s.material
                    s.link = 'OBJECT'
                    s.material = m
        return {'FINISHED'}

class OBJECT_OT_stl_copy_transforms(bpy.types.Operator):
    """STL Copy Transforms from active to selected"""
    bl_idname = "object.stl_copy_transforms"
    bl_label = "STL Copy Transforms from active"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None and len(context.selected_objects)>1

    def execute(self, context):
        for o in context.selected_objects:
            if o != context.object:
                o.matrix_world = context.object.matrix_world.copy()
        return {'FINISHED'}

class SCENE_OT_stl_update(bpy.types.Operator):
    """STL Update"""
    bl_idname = "scene.stl_update"
    bl_label = "STL Update"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        bpy.ops.scene.mat_to_obj()
        global_matrix = axis_conversion(from_forward=context.scene.STL_forward,
                                        from_up=context.scene.STL_up,
                                        ).to_4x4()@ Matrix.Scale(context.scene.STL_scale, 4)
        d = os.path.expanduser('~/Desktop/S2B_Temp') + '/'
        up = 0
        new = 0
        for f in os.listdir(d):
            if f[-4:] == '.stl':
                fp = os.path.join(d, f)
                tris, tri_nors, pts = stl_utils.read_stl(fp)
                name = insert_sense(f)
                if name in context.scene.objects:
                    just_link_stl_data(bpy.data.objects[name], tris, [], pts, global_matrix)
                    bpy.ops.object.select_all(action='SELECT')
                    bpy.ops.object.shade_smooth()
                    bpy.ops.object.select_all(action='DESELECT')
                    self.report({'INFO'}, name+" updated")
                    up += 1

                else:
                    blender_utils.create_and_link_mesh(name, tris, [], pts, global_matrix)
                    if len(bpy.data.objects[name].material_slots) < 1:
                        bpy.data.objects[name].data.materials.append(None)
                    bpy.data.objects[name].data.use_auto_smooth = True
                    bpy.ops.object.shade_smooth()
                    self.report({'INFO'}, name+" created")
                    new += 1
        self.report({'INFO'}, str(up) +' updated, ' + str(new) + ' created.')
        return {'FINISHED'}

class S2B_STLPanel(bpy.types.Panel):
    """Creates a Panel for automated STL import or update from a folder"""
    bl_label = "Send2Blend"
    bl_idname = "SCENE_PT_stl_import_or_update_layout"
    #bl_space_type = 'PROPERTIES'
    #bl_region_type = 'WINDOW'
    #bl_context = "scene"
    bl_space_type = 'VIEW_3D' #n panel
    bl_region_type = 'UI' #n panel
    bl_category = "Tools" #n panel

    directions = [
    ("X", "X", "", 1),
    ("Y", "Y", "", 2),
    ("Z", "Z", "", 3),
    ("-X", "-X", "", 4),
    ("-Y", "-Y", "", 5),
    ("-Z", "-Z", "", 6),
    ]


    bpy.types.Scene.STL_update_path = bpy.props.StringProperty(name="STL Folder", default=os.path.expanduser('~/Desktop/S2B_Temp') + '/')
    bpy.types.Scene.STL_up = bpy.props.EnumProperty(items=directions, default = 'Y')
    bpy.types.Scene.STL_forward = bpy.props.EnumProperty(items=directions, default = 'Z')
    bpy.types.Scene.STL_scale = bpy.props.FloatProperty(name = "Scale", precision = 4, default = 0.001)
    bpy.types.WindowManager.S2B_toggle = bpy.props.BoolProperty()

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.label(text="Import:")
        col = layout.column()
        col.scale_y = 2

        col.operator("scene.stl_update", text = "Import / Update")
        wm = context.window_manager
        label = "Live Update Running..." if wm.S2B_toggle else "Run Live Update"
        layout.prop(wm, 'S2B_toggle', text=label, toggle=True)
        row = layout.row(align=True)
        layout.prop(scene, "STL_up", text="Up")
        layout.prop(scene, "STL_forward", text="Forward")
        layout.prop(scene, "STL_scale", text="Scale")
        layout.separator()
        layout.label(text="Useful operators:")
        layout.operator("scene.mat_to_obj", text = "Link Materials to Objects")
        layout.operator("object.stl_copy_transforms", text = "Transforms from active")

#Checks S2B_Temp folder created by Fusion360 for any / updated files, writes them into a set and checks if the set has changed every 4s
class S2B_LiveUpdate(bpy.types.Operator):
    bl_idname = "s2b.live"
    bl_label = "S2B Live"
    
    savedFiles=set()
    mypath = os.path.expanduser('~/Desktop/S2B_Temp')
    def modal(self, context, event):
        _timer_count = 0
        if event.type == 'TIMER':
            print("Checking")

            nameFiles=set()
            for file in os.listdir(self.mypath):
                fullpath=os.path.join(self.mypath, file)
                if os.path.isfile(fullpath):
                    nameFiles.add(file)
       
            retrievedFiles=set()
            for name in nameFiles:
                stat=os.stat(os.path.join(self.mypath, name))
                time=stat.st_ctime
                mtime=stat.st_mtime
                retrievedFiles.add((name,time,mtime))

            if event.type == 'TIMER' and self.savedFiles != retrievedFiles:
                print("CHANGED!")
                print("Updating Scene")
                bpy.ops.scene.stl_update()
                self.savedFiles=retrievedFiles

        if not context.window_manager.S2B_toggle:
            context.window_manager.event_timer_remove(self._timer)
            print("Send2Blend Monitor Stopped")
            return {'FINISHED'}
        return {"PASS_THROUGH"}
    
    def invoke(self, context, event):
        print("Send2Blend Monitor Start") 
        self._timer = context.window_manager.event_timer_add(4, window=context.window) 
        context.window_manager.modal_handler_add(self)  
        return {'RUNNING_MODAL'}


def update_function(self, context):
    if self.S2B_toggle:
        bpy.ops.s2b.live('INVOKE_DEFAULT')
    return

bpy.types.WindowManager.S2B_toggle = bpy.props.BoolProperty(default = False, update = update_function)

def register():
    bpy.utils.register_class(SCENE_OT_stl_update)
    bpy.utils.register_class(OBJECT_OT_stl_copy_transforms)
    bpy.utils.register_class(SCENE_OT_materials_to_objects)
    bpy.utils.register_class(S2B_STLPanel)
    bpy.utils.register_class(S2B_LiveUpdate)


def unregister():
    bpy.utils.unregister_class(S2B_STLPanel)
    bpy.utils.unregister_class(SCENE_OT_stl_update)
    bpy.utils.unregister_class(SCENE_OT_materials_to_objects)
    bpy.utils.unregister_class(OBJECT_OT_stl_copy_transforms)
    bpy.utils.unregister_class(S2B_LiveUpdate)


if __name__ == "__main__":
    register()
