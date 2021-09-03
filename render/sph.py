import bpy
import bmesh
import numpy as np
import os
from mathutils import Vector


directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings()
setup_layers()
setup_compositor()
cam_obj = setup_camera(location = (0,-9.5,1.85), angle = (np.pi/2 - np.pi/16, 0, 0), lens = 85, x = 1408//2, y = 792//2)
light_obj = setup_lighting(angle = (np.pi/6, -np.pi/6, 0), energy = 5)
setup_background(energy = 5)
bm = import_bmesh(os.path.join(directory, "mgp", "sph.obj"))
gnd_obj = create_ground_plane(location = (0, 1, -1), scale = (10, 30, 1))
arr_obj = create_vector_arrow()
set_object_collections(ground = [gnd_obj], instancing = [arr_obj])




for file in ("sph_ev.csv","sph_pr.csv","sph_xy.csv"):
    import_color(bm, color = (31/255, 119/255, 180/255, 1))
    obj = add_mesh(bm)
    mat = add_vertex_colors(obj)
    vf_bm = import_vector_field(os.path.join(directory, "mgp", file))
    vf_obj = add_vector_field(vf_bm, arr_obj, scale = 3.5)
    set_object_collections(primary = [obj], secondary = [vf_obj])
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [obj,vf_obj], materials = [mat], modifiers = vf_obj.modifiers)
    if not bpy.app.background:
        break


if bpy.app.background:
    for file in ("sph_ker.csv",):
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "mgp", "col_viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        obj.rotation_euler[0] = np.pi / 6
        sph_obj = create_dot(location = (0,-1.01 * np.sin(obj.rotation_euler[0]),1.01 * np.cos(obj.rotation_euler[0])), radius = 0.025, color = (214/255,39/255,40/255,1))
        sph_mat = add_vertex_colors(sph_obj)
        sph_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
        set_object_collections(primary = [obj], secondary = [sph_obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj,sph_obj], materials = [mat,sph_mat])
    
    
    for file in ("sph_a.csv","sph_b.csv","sph_ex.csv","sph_ey.csv","sph_ez.csv"):
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "mgp", "col_viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(primary = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.data.scenes["Scene"].render.resolution_x = 1408//4
        bpy.data.scenes["Scene"].render.resolution_y = 792//4
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
     
    
    for file in ("sph_x.csv","sph_y.csv"):
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "mgp", "col_plasma.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        set_object_collections(primary = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.data.scenes["Scene"].render.resolution_x = 1408//4
        bpy.data.scenes["Scene"].render.resolution_y = 792//4
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
    
    
    for file in ("sph_e11.csv","sph_e109.csv",):
        import_color(bm, data_file = os.path.join(directory, "mgp", file), palette_file = os.path.join(directory, "mgp", "col_viridis.csv"))
        obj = add_mesh(bm)
        mat = add_vertex_colors(obj)
        obj.rotation_euler[0] = -np.pi / 4
        set_object_collections(primary = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.data.scenes["Scene"].render.resolution_x = 1024//2
        bpy.data.scenes["Scene"].render.resolution_y = 576//2
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
