import bpy
import bmesh
from functools import partial
import numpy as np
import os
from mathutils import Vector


def normal_density(x, mean = 0, std = 1):
    normalizing_constant = 1 / (std * np.sqrt(2 * np.pi))
    unnormalized_density = np.exp(-((x - mean) / std)**2)
    return normalizing_constant * unnormalized_density


def mvn_density(x, y, correlation = 0):
    normalizing_constant = 1 / (2 * np.pi * np.sqrt(1 - correlation**2))
    unnormalized_density = np.exp(-(x**2 - 2 * correlation * x * y + y**2) / (2 * (1 - correlation**2)))
    return normalizing_constant * unnormalized_density


def add_vertex_alphas(bm, unnormalized_alpha, alpha_scaling = 1, color = (31/255,119/255,180/255)):
    color_layer = bm.loops.layers.color.new("color")
    for face in bm.faces:
        for loop in face.loops:
            vert_alpha = np.minimum(1,unnormalized_alpha(loop.vert.co) * alpha_scaling)
            loop[color_layer] = (color[0],color[1],color[2],vert_alpha)
            
    
def create_mvn(correlation, num_contours = 64, num_points_per_contour = 48, alpha_scaling = 10):
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
    
    def density(v):
        x = v[0]
        y = v[1]
        return mvn_density(x,y,correlation)
    
    L = np.linalg.cholesky([[1.,correlation],[correlation,1.]])
    for vert in bm.verts:
        vert.co[:2] = L @ np.array((vert.co[0],vert.co[1]))
        vert.co[2] = density(vert.co)
        
    add_vertex_alphas(bm, density, alpha_scaling / density((0,0)))

    return bm

            
def create_joint(cutoff, grid_size = 250, grid_scale = 2.75, width_scale = 1.375, alpha_scaling = 5):
    bm = bmesh.new()
    
    bmesh.ops.create_grid(bm, x_segments = grid_size, y_segments = grid_size, size = grid_scale)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(width_scale,1,1))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cutoff*width_scale,grid_scale+cutoff,0))
    
    extruded_geom = bmesh.ops.extrude_face_region(bm, geom = bm.faces)
    extruded_verts = [v for v in extruded_geom["geom"] if isinstance(v, bmesh.types.BMVert)]
    
    def density(v):
        x = v[0]
        y = v[1]
        return normal_density(x, std = 1) * normal_density(y, mean = -x, std = 1)
    
    for vert in extruded_verts:
        vert.co[2] = density(vert.co)
            
    bm.normal_update()
    add_vertex_alphas(bm, density, alpha_scaling / density((0,0)))
    
    wf_bm = bmesh.new()
    wf_x = np.linspace(-1.75,1.75,100)
    for x in wf_x:
        wf_bm.verts.new((x,cutoff,density((x,cutoff))))
        
    for x in np.flip(wf_x):
        wf_bm.verts.new((x,cutoff,0))
        
    wf_bm.faces.new(wf_bm.verts)
        
    def wf_density(v):
        x = v[0]
        y = v[1]
        z = v[2]
        if z > 0:
            return density((x,y))
        else:
            return 0
    
    add_vertex_alphas(wf_bm, wf_density, alpha_scaling / density((0,0)), color=(31/510,119/510,180/510))
    
    return (bm, wf_bm)
    

def setup_box_mask(mask_center = (0.5,0.5), mask_size = (1,1), mask_blur_size = 32):
    scene = bpy.context.scene
    scene.use_nodes = True
    
    scene.node_tree.nodes.clear()
    
    view_layer = scene.node_tree.nodes.new("CompositorNodeRLayers")
    view_layer.layer = "View Layer"
    
    set_alpha_node = scene.node_tree.nodes.new("CompositorNodeSetAlpha")
    
    composite_node = scene.node_tree.nodes.new("CompositorNodeComposite")
    viewer_node = scene.node_tree.nodes.new("CompositorNodeViewer")
    
    box_mask_node = scene.node_tree.nodes.new("CompositorNodeBoxMask")
    box_mask_node.width = mask_size[0]
    box_mask_node.height = mask_size[1]
    box_mask_node.x = mask_center[0]
    box_mask_node.y = mask_center[1]
    
    blur_node = scene.node_tree.nodes.new("CompositorNodeBlur")
    blur_node.size_x = mask_blur_size
    blur_node.size_y = mask_blur_size
    
    scene.node_tree.links.new(view_layer.outputs["Image"], set_alpha_node.inputs["Image"])
    scene.node_tree.links.new(box_mask_node.outputs["Mask"], blur_node.inputs["Image"])
    scene.node_tree.links.new(blur_node.outputs["Image"], set_alpha_node.inputs["Alpha"])
    scene.node_tree.links.new(set_alpha_node.outputs["Image"], viewer_node.inputs["Image"])
    scene.node_tree.links.new(set_alpha_node.outputs["Image"], composite_node.inputs["Image"])


directory = os.getcwd()
with open(os.path.join(directory,"render.py")) as file:
    exec(file.read())

reset_scene()
set_renderer_settings(num_samples = 16384 if bpy.app.background else 128)
(cam_axis, cam_obj) = setup_camera(offset = (0,0,0.375), distance = 16.25, angle = (-np.pi/16,0,0), height = 450, crop = (0,1,0.2,0.85))


if bpy.app.background:
    ((key_axis,key_obj),(fill_axis,fill_obj),(rim_axis,rim_obj)) = setup_lighting(
        offset = (0,0,0.5), shifts = (-5,-5,5), sizes = (1,5,5), energies = (300,50,300), 
        horizontal_angles = (np.pi/12, -np.pi/3, -np.pi/12), vertical_angles = (-np.pi/6, -np.pi/4, np.pi/3))
    mvn_pos_bm = create_mvn(0.9)
    mvn_pos_obj = add_mesh(mvn_pos_bm)
    mvn_pos_obj.scale = (0.8,0.8,5)
    mvn_pos_mat = add_vertex_colors(mvn_pos_obj)
    setup_box_mask(mask_center = (0.5,0.5125), mask_size = (0.85, 0.4),  mask_blur_size = 16)
    set_resolution(height = 450, crop = (0,9/10,1/5,17/20))
    bpy.context.scene.render.filepath = os.path.join(directory, "output", "mvn_pos.png")
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [mvn_pos_obj,key_axis,key_obj,fill_axis,fill_obj,rim_axis,rim_obj], materials = [mvn_pos_mat])


    ((key_axis,key_obj),(fill_axis,fill_obj),(rim_axis,rim_obj)) = setup_lighting(
        offset = (0,0,0.5), shifts = (-5,-5,5), sizes = (1,5,5), energies = (300,50,300), 
        horizontal_angles = (-np.pi/4, np.pi/4, np.pi/4), vertical_angles = (-np.pi/4, -np.pi/6, np.pi/4))
    mvn_neg_bm = create_mvn(-0.6)
    mvn_neg_obj = add_mesh(mvn_neg_bm)
    mvn_neg_obj.scale = (0.8,0.8,5)
    mvn_neg_mat = add_vertex_colors(mvn_neg_obj)
    setup_box_mask(mask_center = (0.5,0.5125), mask_size = (0.8, 0.4),  mask_blur_size = 16)
    set_resolution(height = 450, crop = (1/10,19/20,1/5,17/20))
    bpy.context.scene.render.filepath = os.path.join(directory, "output", "mvn_neg.png")
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [mvn_neg_obj,key_axis,key_obj,fill_axis,fill_obj,rim_axis,rim_obj], materials = [mvn_neg_mat])


    cam_axis.rotation_euler = (-np.pi/8, 0, 2*np.pi/9 - 0.02)
    cam_axis.location = (0,0,0)
    cam_obj.location = (0,-7.5,0)
    ((key_axis,key_obj),(fill_axis,fill_obj),(second_fill_axis,second_fill_obj),(rim_axis,rim_obj)) = setup_lighting(
        offset = (0.25,-0.375,0.25), shifts = (-5,-5,-5,5), sizes = (1,2,2,2.5), energies = (260,300,300,500), 
        horizontal_angles = (np.pi/8, 13*np.pi/18, -5*np.pi/12, 2*np.pi/9), vertical_angles = (np.pi/6, -7*np.pi/36, -np.pi/8, np.pi/4),
        names = ("Key","Fill","Second Fill","Rim"),
        types = ("AREA","AREA","AREA","POINT"))
    key_obj.data.color = (0.11,0.77,1.0)
    (bayes_bm, bayes_wf_bm) = create_joint(cutoff = -0.5)
    bayes_obj = add_mesh(bayes_bm)
    bayes_mat = add_vertex_colors(bayes_obj)
    bayes_wf_obj = add_mesh(bayes_wf_bm, name="Wireframe")
    bayes_wf_mat = add_vertex_colors(bayes_wf_obj)
    bayes_wf_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
    bayes_wf_mod = bayes_wf_obj.modifiers.new("Wireframe", "WIREFRAME")
    bayes_wf_mod.thickness = 0.01125
    hsv_node = bayes_mat.node_tree.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Hue"].default_value = 0.505
    hsv_node.inputs["Saturation"].default_value = 0.895
    hsv_node.inputs["Value"].default_value = 0.995
    bayes_mat.node_tree.links.new(bayes_mat.node_tree.nodes["Vertex Color"].outputs["Color"], hsv_node.inputs["Color"])
    bayes_mat.node_tree.links.new(hsv_node.outputs["Color"], bayes_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    bayes_mod = bayes_obj.modifiers.new("Edge Split", "EDGE_SPLIT")
    bayes_obj.scale = (0.5,0.5,2.75)
    bayes_wf_obj.scale = (0.5,0.5,2.75)
    setup_box_mask(mask_size = (0.475, 0.28125), mask_blur_size = 16)
    set_resolution(height = 680, crop = (1/4,3/4,1/3,4/5))
    bpy.context.scene.render.filepath = os.path.join(directory, "output", "bayes.png")
    bpy.ops.render.render(use_viewport = True, write_still = True)
    cleanup(objects = [bayes_obj,key_axis,key_obj,fill_axis,fill_obj,rim_axis,rim_obj], materials = [bayes_mat], modifiers = [bayes_mod])

