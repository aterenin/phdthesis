import bpy
import bmesh
from functools import partial
import numpy as np
import os
from mathutils import Vector



directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings(num_samples = 2048 if bpy.app.background else 128)
setup_layers()
setup_compositor(mask_center = (0.5,0.425), mask_size = (0.925,0.4), shadow_color_correction_exponent = 2.75)
cam_obj = setup_camera(offset = (0,0,-0.25), distance = 24.75, angle = (-5*np.pi/36, 0, 0), lens = 85, height = 430, crop = (1/12,1,1/12,5/6))
setup_lighting(shifts = (-15,-15,15), sizes = (15,24,9), energies = (3000,625,1000), 
               horizontal_angles = (-np.pi/4, np.pi/3, np.pi/4), vertical_angles = (-np.pi/3, -np.pi/4, np.pi/4))
bm = import_bmesh(os.path.join(directory, "mgp", "t2.obj"))
bd_obj = create_backdrop(location = (0, 0, -1), scale = (8,12,12))
set_object_collections(backdrop = [bd_obj])


if bpy.app.background:
    for color in [(31/255,119/255,1/255,1)]:
        import_color(bm, color = (31/255, 119/255, 180/255, 1))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", "t2.png")
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
    
    
    for file in ["t2_ker.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        sph_obj = create_dot(location = (-np.sqrt(2)*3/2 - 1/2 - 0.01, -np.sqrt(2)*3/2 - 1/2 - 0.01, np.sqrt(2)/2), radius = 0.0625)
        sph_mat = add_vertex_colors(sph_obj)
        set_object_collections(object = [obj, sph_obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj,sph_obj], materials = [mat,sph_mat])
    
    
    for file in ["t2_e15.csv","t2_e125.csv"]:
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        set_resolution(300)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
 