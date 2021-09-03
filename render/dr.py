import bpy
import bmesh
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
    

def import_data_points_color(obj, bm, points_file, radius = 0.002):
    points = np.genfromtxt(points_file, delimiter=",", dtype=int)
    mesh = obj.data
    
    bm.verts.ensure_lookup_table()
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]
            for i in points:
                if (vert.co - bm.verts[i].co).length < radius:
                    mesh.vertex_colors["Col"].data[loop_idx].color = (0,0,0,1)











directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings()
setup_layers()
setup_compositor()
setup_camera(location = (0.005,-0.7,0.26), angle = (np.pi/2 - np.pi/16, 0, 0), lens = 85, x = 1408//2, y = 792//2)
setup_lighting(angle = (np.pi/6, -np.pi/6, 0), energy = 5)
setup_background(energy = 5)
bm = import_bmesh(os.path.join(directory, "mgp", "dr.obj"))
r_bm = create_voxel_remesh(bm)
gnd_obj = create_ground_plane(location = (0.005, 0.15, 0.053), scale = (163, 200, 1))
set_object_collections(ground = [gnd_obj])




for file in ("dr_ker.csv",):
    import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
    obj = add_mesh(r_bm)
    mat = add_vertex_colors(obj)
    transfer_vertex_colors_to_voxel_remesh(obj, bm)
    obj.rotation_euler = (np.pi / 2, 0, 0)
    bm.verts.ensure_lookup_table()
    sph_location = bm.verts[0].co + 0.001 * bm.verts[0].normal
    sph_obj = create_dot(location = (sph_location[0],sph_location[2],sph_location[1]), radius = 0.002, color = (214/255,39/255,40/255,1))
    sph_mat = add_vertex_colors(sph_obj)
    sph_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
    set_object_collections(primary = [obj], secondary = [sph_obj])
    bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [obj,sph_obj], materials = [mat,sph_mat])


if bpy.app.background:
    for file in ("dr_gt.csv","dr_m.csv","dr_fn.csv"):
        index = 0 if file == "dr_fn.csv" else None
        import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_plasma.csv"), index = index, bounds = (-2,2))
        obj = add_mesh(r_bm)
        mat = add_vertex_colors(obj)
        transfer_vertex_colors_to_voxel_remesh(obj, bm)
        subdivide_near_data_points(obj, os.path.join(directory, "mgp", "dr_loc.csv"))
        import_data_points_color(obj, bm, os.path.join(directory, "mgp", "dr_loc.csv"))
        obj.rotation_euler = (np.pi / 2, 0, 0)
        set_object_collections(primary = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
    
    
    for file in ("dr_std.csv",):
        import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
        obj = add_mesh(r_bm)
        mat = add_vertex_colors(obj)
        transfer_vertex_colors_to_voxel_remesh(obj, bm)
        subdivide_near_data_points(obj, os.path.join(directory, "mgp", "dr_loc.csv"))
        import_data_points_color(obj, bm, os.path.join(directory, "mgp", "dr_loc.csv"))
        obj.rotation_euler = (np.pi / 2, 0, 0)
        set_object_collections(primary = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])
    
    
    for file in ("dr_e3.csv","dr_e100.csv"):
        import_color(bm, os.path.join(directory, "mgp", file), os.path.join(directory, "mgp", "col_viridis.csv"))
        obj = add_mesh(r_bm)
        mat = add_vertex_colors(obj)
        transfer_vertex_colors_to_voxel_remesh(obj, bm)
        obj.rotation_euler = (np.pi / 2, 0, 0)
        set_object_collections(primary = [obj])
        bpy.context.scene.render.filepath = os.path.join(directory, "output", file.replace(".csv",".png"))
        bpy.data.scenes["Scene"].render.resolution_x = 1024//2
        bpy.data.scenes["Scene"].render.resolution_y = 576//2
        bpy.ops.render.render(use_viewport = True, write_still = True)
        cleanup(objects = [obj], materials = [mat])