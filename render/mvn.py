import bpy
import bmesh
import numpy as np
import os
from mathutils import Vector


def mvn_density(x, y, correlation = 0):
    normalizing_constant = 1 / (2 * np.pi * np.sqrt(1 - correlation**2))
    unnormalized_density = np.exp(-(x**2 - 2 * correlation * x * y + y**2) / (2 * (1 - correlation**2)))
    return normalizing_constant * unnormalized_density


def create_mvn(correlation, num_contours = 64, num_points_per_contour = 48):
    radii = np.append(np.linspace(4/num_contours,4,num_contours),100)
    bm = bmesh.new()
    
    inner_verts = bmesh.ops.create_circle(bm, radius=radii[0]/2, segments=256)["verts"]
    prev_edges = set()
    for vert in inner_verts:
        for edge in vert.link_edges:
            prev_edges.add(edge)
            
    for radius in radii:
        curr_verts = bmesh.ops.create_circle(bm, radius=radius, segments=256)["verts"]
        curr_edges = set()
        for vert in curr_verts:
            for edge in vert.link_edges:
                curr_edges.add(edge)
        bmesh.ops.bridge_loops(bm, edges=list(curr_edges) + list(prev_edges))
        prev_edges = curr_edges
    
    bmesh.ops.pointmerge(bm, verts=inner_verts, merge_co=(0,0,0))
    
    L = np.linalg.cholesky([[1.,correlation],[correlation,1.]])
    for vert in bm.verts:
        vert.co[:2] = L @ np.array((vert.co[0],vert.co[1]))
    
    color_layer = bm.loops.layers.color.new("color")
    alpha_layer = bm.loops.layers.color.new("alpha")
    density_max = mvn_density(0,0,correlation)
    for face in bm.faces:
        for loop in face.loops:
            density = mvn_density(loop.vert.co[0], loop.vert.co[1], correlation)
            loop.vert.co[2] = density
            intensity = density / density_max
            loop[color_layer] = (31/255,119/255,180/255,np.minimum(1,10 * intensity))
            loop[alpha_layer] = (np.minimum(1,10 * intensity),np.minimum(1,10 * intensity),np.minimum(1,10 * intensity),1)

    return bm


directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings()
setup_camera(location = (0,-17,3.875), angle = (np.pi/2 - np.pi/16, 0, 0), lens = 85, x = 2520//4, y = 1080//4)
light_obj = setup_lighting(angle = (np.pi/6, np.pi/6, 0), energy = 5)
setup_background(energy = 5)

mvn_pos_bm = create_mvn(0.6)
mvn_pos_obj = add_mesh(mvn_pos_bm)
mvn_pos_obj.scale = (0.8,0.8,5)
mvn_pos_mat = add_vertex_colors(mvn_pos_obj)
bpy.context.scene.render.filepath = os.path.join(directory, "output", "mvn_pos.png")
bpy.ops.render.render(use_viewport = True, write_still = True)
cleanup(objects = [mvn_pos_obj], materials = [mvn_pos_mat], force = True)

mvn_neg_bm = create_mvn(-0.9)
mvn_neg_obj = add_mesh(mvn_neg_bm)
mvn_neg_obj.scale = (0.8,0.8,5)
mvn_neg_mat = add_vertex_colors(mvn_neg_obj)
light_obj.rotation_euler[1] = -np.pi/6
bpy.context.scene.render.filepath = os.path.join(directory, "output", "mvn_neg.png")
bpy.ops.render.render(use_viewport = True, write_still = True)
cleanup(objects = [mvn_neg_obj], materials = [mvn_neg_mat])