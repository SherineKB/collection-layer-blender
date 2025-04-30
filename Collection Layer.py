bl_info = {
    "name": "Collection Layer",
    "author": "Sherine KACMAZ BELHAINE - For Eddy",
    "version": (1,0),
    "blender": (2, 93, 0),
    "location": "3D View > Sidebar > IDs per Collection",
    "description": "Create a cryptomatte layer per collection",
    "category": "Node",
}

import bpy

# UI - Drop Down Menu for the Cryptomatte Output selection
class DropDown(bpy.types.PropertyGroup): # Calling a specific Blender class related to the drop down
    bl_idname = "drop_down"
    bl_label = "Drop Down Menu"

    outputType: bpy.props.EnumProperty(
        # EnumProperty is a specific Blender class used for Drop Downs. It's used when you have to choose between several options
        name="Output Type",
        description="Select your output image type.",
        items=[
            ("IMAGE", "Image", "Connect Image output"),
            ("MATTE", "Matte", "Connect Matte output"),
            ("PICK", "Pick", "Connect Pick output"),
        ],
        default="IMAGE",
        update=lambda self, context: cryptomattes(self, context)  # Automatically update when dropdown changes
    ) # type: ignore

    # UI - Drop Down Menu for the File Format
    file_format: bpy.props.EnumProperty(
        name="File Format",
        description="Choose the file format for the output. For more details, go to Compositing Workspace and check the File Output node parameters",
        items=[
            ("BMP", "BMP", "Save output in BMP format"),
            ("IRIS", "Iris", "Save output in Iris format"),
            ("PNG", "PNG", "Save output in PNG format"),
            ("JPEG", "JPEG", "Save output in JPEG format"),
            ("JPEG2000", "JPEG 2000", "Save output in JPEG 2000 format"),
            ("TARGA", "Targa", "Save output in Targa format"),
            ("TARGA_RAW", "Targa Raw", "Save output in Targa Raw format"),
            ("CINEON", "Cineon", "Save output in Cineon format"),
            ("DPX", "DPX", "Save output in DPX format"),
            ("OPEN_EXR_MULTILAYER", "OpenEXR MultiLayer", "Save output in OpenEXR MultiLayer format"),
            ("OPEN_EXR", "OpenEXR", "Save output in OpenEXR format"),
            ("HDR", "Radiance HDR", "Save output in Radiance HDR format"),
            ("TIFF", "TIFF", "Save output in TIFF format"),
            ("WEBP", "WebP", "Save output in WebP format")
        ],
        default="OPEN_EXR_MULTILAYER",  
        update=lambda self, context: update_file_format(self, context)  # Update when file format changes
    ) # type: ignore


# Update File Format (connect the UI to the File Output File Format option)
def update_file_format(self, context):
    # Get the current scene
    scene = bpy.context.scene
    tree = scene.node_tree
    # Attribute the file format from my UI to the File Output node.
    tree.nodes["File Output"].format.file_format = self.file_format 

# PANEL
class ToolPanel(bpy.types.Panel):
    bl_category = 'IDs per Collection'
    bl_label = 'IDs Manager'
    bl_idname = 'VIEW3D_PT_ids_manager'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        # Ensure nodes are being used in the current scene
        scene = context.scene
        tree = scene.node_tree
        # Create the first button
        layout.operator("add.collection_layer", text="Add a Collection Layer")

        # Dropdown for Output Type
        layout.prop(context.scene.drop_down_props, "outputType")

        # Display the file slots in the File Output node
        file_output = next((node for node in tree.nodes if node.type == 'OUTPUT_FILE'), None)

        # Display the file slots in the File Output node  
        # index = slot position, starts at 0, slot is the actual slot, like the name - enumerate = assign index to the slot    
        for index, slot in enumerate(file_output.file_slots):
            # Create a row inside a column
            row = layout.column().row(align=True)
            row.label(text=slot.path)

            # Slots position
            moveUP = row.operator("move.slot_up", text="", icon='TRIA_UP', emboss=True)
            moveUP.slot_index = index # assigns the file slot index to the operator so that the script knows which file slot to move when the button is clicked.

            moveDown = row.operator("move.slot_down", text="", icon='TRIA_DOWN', emboss=True)
            moveDown.slot_index = index
            # Delete slot
            if slot.path != "Image":
                delete_op = row.operator("delete.file_slot", text="", icon='X')
                delete_op.slot_index = index
                
        # Dropdown for File Format
        layout.prop(context.scene.drop_down_props, "file_format")
        # Render path
        layout.prop(tree.nodes["File Output"], "base_path", text="Render Path")


# Function to gather all objects from a collection, including its sub-collections
def get_objects(collection):
    objects = list(collection.objects)
    for child_collection in collection.children:
        objects.extend(get_objects(child_collection))  # Get objects from sub-collections. Extend allows to add the child objects to the list
    return objects

# Function to generate or update the cryptomattes, and connect based on dropdown selection
def cryptomattes(self, context):
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree

    # Get the dropdown selection value
    dropdown_value = scene.drop_down_props.outputType

    # Ensure a Render Layers node exists
    render_layer = next((node for node in tree.nodes if node.type == 'R_LAYERS'), None)
    if not render_layer:
        render_layer = tree.nodes.new(type='CompositorNodeRLayers')
        render_layer.location = (0, 0)

    # Check if a File Output node exists
    file_output = next((node for node in tree.nodes if node.type == 'OUTPUT_FILE'), None)
    if not file_output:
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.location = (600, 0)
        file_output.format.file_format = 'OPEN_EXR'  # Default to OpenEXR
        
        # Connect Render Layer Image output to File Output Image input
        tree.links.new(render_layer.outputs['Image'], file_output.inputs[0])

    # Get all the cryptomattes
    cryptomatte_nodes = [node for node in tree.nodes if node.type == 'CRYPTOMATTE_V2']
    for cryptomatte in cryptomatte_nodes:
        # Extract the name of the collections from the cryptomattes. 
        # Get text "Cryptomatte" and replace it by "" -> nothing, so it remains only the collection label
        collection_name = cryptomatte.label.replace("Cryptomatte ", "")

        # Add a new file slot for the collection if it doesn't already exist
        existing_slot = next((slot for slot in file_output.file_slots if slot.path == collection_name), None)
        if not existing_slot:
            file_output.file_slots.new(collection_name)

        # Prepare the output socket name based on the dropdown value
        output_socket_name = "Image"  # Default to Image
        if dropdown_value == "MATTE":
            output_socket_name = "Matte"
        elif dropdown_value == "PICK":
            output_socket_name = "Pick"

        # Disconnect existing links to the File Output node for this specific Cryptomatte
        for link in [link for link in tree.links if link.from_node == cryptomatte and link.to_node == file_output]:
            tree.links.remove(link)

        # Connect the appropriate output to the File Output node
        if output_socket_name in cryptomatte.outputs:
            cryptomatte_output = cryptomatte.outputs[output_socket_name]
            collection_slot = next((slot for slot in file_output.file_slots if slot.path == collection_name), None)

            if cryptomatte_output and collection_slot:
                slot_index = file_output.file_slots.find(collection_name)
                tree.links.new(cryptomatte_output, file_output.inputs[slot_index])

    # Always reconnect the Render Layers 'Image' output to each Cryptomatte 'Image' input
    for cryptomatte in cryptomatte_nodes:
        if cryptomatte.inputs['Image'].is_linked is False:
            tree.links.new(render_layer.outputs['Image'], cryptomatte.inputs['Image'])


########## ADD COLLECTION LAYER ########### +  update cryptomatte nodes position
class AddCollLayerOperator(bpy.types.Operator):
    bl_idname = "add.collection_layer"
    bl_label = "Add Collection Layer"

    def execute(self, context):
        ### Create the Cryptomatte node for the active collection
        scene = context.scene       
        bpy.data.scenes["Scene"].use_nodes = True
        view_layer = bpy.data.scenes["Scene"].view_layers["ViewLayer"]
        view_layer.use_pass_cryptomatte_object = True
        view_layer.use_pass_cryptomatte_material = True
        view_layer.use_pass_cryptomatte_asset = True

        # Activate Cryptomatte passes when the script is loaded 
        tree = scene.node_tree
        # Get the name of the active collection
        active_collection = bpy.context.view_layer.active_layer_collection
        collection_name = active_collection.name if active_collection else None

        # Step 1: Search for a CryptomatteV2 node with the same label as the collection
        node = None
        node_position = None  # We'll store the old node position if it exists

        for node in tree.nodes:
            if node.type == 'CRYPTOMATTE_V2' and node.label == f"Cryptomatte {collection_name}":
                node_position = node.location.copy()  # Store the position of the existing node
                break # stop searching for the node

        # Step 2: If found, delete the existing CryptomatteV2 node
        if node:
            tree.nodes.remove(node)

        # Step 3: Calculate the vertical position for the new Cryptomatte node
        y_offset = 0

        if node_position:
            # If there was an existing node, use its position
            y_offset = node_position[1] #[0] is for horizontal position and [1] for vertical
        else:
            # Find the lowest existing CryptomatteV2 node to space vertically
            for node in tree.nodes:
                if node.type == 'CRYPTOMATTE_V2':
                    y_offset = min(y_offset, node.location[1] - 250)  # Spacing of 250 units below the lowest node

        # Step 4: Create a new CryptomatteV2 node at the determined position
        cryptomatte = tree.nodes.new(type='CompositorNodeCryptomatteV2')
        cryptomatte.location = (300, y_offset)  # Position the node
        cryptomatte.label = f"Cryptomatte {collection_name}"

        # Add objects in the collection and sub-collections to the Matte ID of the Cryptomatte node
        all_objects = get_objects(active_collection.collection)
        cryptomatte.matte_id = ", ".join(obj.name for obj in all_objects)

        # Connect the Render Layer's Image output to the Cryptomatte's Image input
        render_layer = next((node for node in tree.nodes if node.type == 'R_LAYERS'), None)
        if render_layer:
            tree.links.new(render_layer.outputs['Image'], cryptomatte.inputs['Image'])

        # Call the function to update all connections
        cryptomattes(self, context)

        return {'FINISHED'}


########## DELETE FILE SLOT BUTTON ##########
class DeleteFileSlotOperator(bpy.types.Operator):
    bl_idname = "delete.file_slot"
    bl_label = "Delete File Slot"

    slot_index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.use_nodes = True

        tree = scene.node_tree
        file_output_node = next((node for node in tree.nodes if node.type == 'OUTPUT_FILE'), None)

        if 0 <= self.slot_index < len(file_output_node.file_slots): # make sure that the index is >= 0 and < of the nb of slots
            file_output_node.active_input_index = self.slot_index

            slot_name = file_output_node.file_slots[self.slot_index].path # get slot name

            file_output_node.file_slots.remove(file_output_node.inputs[self.slot_index]) # delete slot

            cryptomatte_node = next((node for node in tree.nodes if node.type == 'CRYPTOMATTE_V2' and node.label == f"Cryptomatte {slot_name}"), None)
            if cryptomatte_node:
                tree.nodes.remove(cryptomatte_node) # delete cryptomatte

            context.area.tag_redraw() # update UI
            return {'FINISHED'} # This tells Blender that the operator successfully executed all its operations and that everything is done as expected.


########## MOVE FILE SLOT UP BUTTON ##########
class MoveFileSlotUpOperator(bpy.types.Operator):
    bl_idname = "move.slot_up"
    bl_label = "Move File Slot Up"

    slot_index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.use_nodes = True

        tree = scene.node_tree
        file_output_node = next((node for node in tree.nodes if node.type == 'OUTPUT_FILE'), None)

        if not file_output_node:
            return {'CANCELLED'}

        # Ensure the slot index is within valid range
        if 0 < self.slot_index < len(file_output_node.file_slots):
            # Move the file slot up by swapping with the one above it
            file_output_node.file_slots.move(self.slot_index, self.slot_index - 1)

            # Refresh the UI to show the updated slot positions
            context.area.tag_redraw()

        return {'FINISHED'}


########## MOVE FILE SLOT DOWN BUTTON ##########
class MoveFileSlotDownOperator(bpy.types.Operator):
    bl_idname = "move.slot_down"
    bl_label = "Move File Slot Down"

    slot_index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.use_nodes = True

        tree = scene.node_tree
        file_output_node = next((node for node in tree.nodes if node.type == 'OUTPUT_FILE'), None)

        if not file_output_node:
            return {'CANCELLED'}

        # Ensure the slot index is within valid range
        if 0 <= self.slot_index < len(file_output_node.file_slots) - 1:
            # Move the file slot down by swapping with the one below it
            file_output_node.file_slots.move(self.slot_index, self.slot_index + 1)

            # Refresh the UI to show the updated slot positions
            context.area.tag_redraw()
        return {'FINISHED'}


# Register the necessary classes and properties
classes = [
    DropDown,
    ToolPanel,
    AddCollLayerOperator,
    DeleteFileSlotOperator,
    MoveFileSlotUpOperator,
    MoveFileSlotDownOperator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.drop_down_props = bpy.props.PointerProperty(type=DropDown)

def unregister():
    for cls in reversed(classes): # reversed is used to go through the classes starting from the last one to avoid dependencies issues
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.drop_down_props # deletes the custom property

if __name__ == "__main__":
    register()
