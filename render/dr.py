import bpy
import bmesh
from functools import partial
import numpy as np
import os
from mathutils import Vector


def create_voxel_remesh(bm):
    mesh = bpy.data.meshes.new("Mesh")
    obj = bpy.data.objects.new("Mesh", mesh)
    bpy.context.collection.objects.link(obj)
    bm.to_mesh(mesh)
    
    obj.data.remesh_mode = "VOXEL"
    obj.data.remesh_voxel_size = 0.0005
    
    bpy.ops.object.select_all(action = "DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.voxel_remesh()
    
    vox_bm = bmesh.new()
    vox_bm.from_mesh(mesh)
    
    bpy.data.objects.remove(obj, do_unlink = True)
    bpy.data.meshes.remove(mesh, do_unlink = True)
    
    return vox_bm


def transfer_vertex_colors_to_voxel_remesh(obj, bm):
    temp_mesh = bpy.data.meshes.new("Temp")
    temp_obj = bpy.data.objects.new("Temp", temp_mesh)
    bpy.context.collection.objects.link(temp_obj)
    bm.to_mesh(temp_mesh)
    
    bpy.ops.object.select_all(action = "DESELECT")
    temp_obj.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = temp_obj
    bpy.ops.object.data_transfer(data_type = "VCOL")
    
    bpy.data.objects.remove(temp_obj, do_unlink = True)
    bpy.data.meshes.remove(temp_mesh, do_unlink = True)


def subdivide_near_data_points(obj, points_file, radius=0.003):
    points = np.genfromtxt(points_file, delimiter=",", dtype=int)
    mesh = obj.data
    
    bpy.ops.object.select_all(action = "DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bm.verts.ensure_lookup_table()
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]
            for i in points:
                if (vert.co - bm.verts[i].co).length < radius:
                    vert.select = True
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts = 2)
    bpy.ops.object.editmode_toggle()
    

def import_data_points_color(obj, bm, points_file, radius = 0.002, color = (0,0,0,1)):
    points = np.genfromtxt(points_file, delimiter=",", dtype=int)
    mesh = obj.data
    
    bm.verts.ensure_lookup_table()
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]
            for i in points:
                if (vert.co - bm.verts[i].co).length < radius:
                    mesh.vertex_colors["Col"].data[loop_idx].color = color











directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings(num_samples = 2048 if bpy.app.background else 128)
setup_layers()
setup_compositor(mask_center = (0.5,0.225), mask_size = (0.775,0.175), shadow_color_correction_exponent = 2.75)
setup_camera(offset = (0.005,0,0.12), distance = 0.6875, angle = (-np.pi/16, 0, 0), lens = 85, height = 495, crop = (1/15,13/15,1/20,9/10))
setup_lighting(offset = (0,0,0.11), shifts = (-0.8,-0.8,0.8), sizes = (0.6,1,0.2), energies = (7.5,2.875,3.75), 
               horizontal_angles = (5*np.pi/18, -2*np.pi/9, -2*np.pi/9), vertical_angles = (-5*np.pi/18, -2*np.pi/9, 5*np.pi/18))
bm = import_bmesh(os.path.join(directory, "mgp", "dr.obj"))
r_bm = create_voxel_remesh(bm)
bd_obj = create_backdrop(location = (0.005, -0.015, 0.053), scale = (0.25, 0.25, 0.25))
set_object_collections(backdrop = [bd_obj])


if bpy.app.background:
    for file in ["dr_ker.csv"]:
        import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(r_bm)
        mat = add_vertex_colors(obj)
        transfer_vertex_colors_to_voxel_remesh(obj, bm)
        obj.rotation_euler = (np.pi / 2, 0, 0)
        bm.verts.ensure_lookup_table()
        sph_location = bm.verts[0].co + 0.001 * bm.verts[0].normal
        sph_obj = create_dot(location = (sph_location[0],sph_location[2],sph_location[1]), radius = 0.002, color = (0,0,0,1))
        sph_mat = add_vertex_colors(sph_obj)
        sph_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
        set_object_collections(object = [obj, sph_obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj,sph_obj], materials = [mat,sph_mat])
        
        
    for file in ["dr_gt.csv", "dr_m.csv", "dr_fn.csv"]:
        import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "col", "plasma.csv"), bounds = (-2,2))
        obj = add_mesh(r_bm)
        mat = add_vertex_colors(obj)
        transfer_vertex_colors_to_voxel_remesh(obj, bm)
        subdivide_near_data_points(obj, os.path.join(directory, "mgp", "dr_loc.csv"))
        import_data_points_color(obj, bm, os.path.join(directory, "mgp", "dr_loc.csv"))
        obj.rotation_euler = (np.pi / 2, 0, 0)
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
    
    
    for file in ["dr_std.csv"]:
        import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(r_bm)
        mat = add_vertex_colors(obj)
        transfer_vertex_colors_to_voxel_remesh(obj, bm)
        subdivide_near_data_points(obj, os.path.join(directory, "mgp", "dr_loc.csv"))
        import_data_points_color(obj, bm, os.path.join(directory, "mgp", "dr_loc.csv"), color = (0.8,0.8,0.8,1))
        obj.rotation_euler = (np.pi / 2, 0, 0)
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
    
    
    for file in ["dr_e3.csv","dr_e100.csv"]:
        import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "col", "viridis.csv"))
        obj = add_mesh(r_bm)
        mat = add_vertex_colors(obj)
        transfer_vertex_colors_to_voxel_remesh(obj, bm)
        obj.rotation_euler = (np.pi / 2, 0, 0)
        set_object_collections(object = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        set_resolution(330)
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])