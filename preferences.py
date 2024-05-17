import bpy
from .ui import update_sidebar_category

#### ------------------------------ PREFERENCES ------------------------------ ####

class BoolToolPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    show_in_sidebar: bpy.props.BoolProperty(
        name = "Show Addon Panel in Sidebar",
        description = "Add add-on operators and properties to 3D viewport sidebar category\n"
                        "Most of the features are already available in 3D viewport's Object > Boolean menu, but brush list is only in sidebar panel",
        default = True,
    )
    sidebar_category: bpy.props.StringProperty(
        name = "Category Name",
        description = "Set sidebar category name. You can type in name of the existing category and panel will be added there, instead of creating new category.",
        default = "Edit",
        update = update_sidebar_category,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # sidebar_category
        col = layout.column(align=True, heading='Show in Sidebar')
        row = col.row(align=True)
        sub = row.row(align=True)
        sub.prop(self, "show_in_sidebar", text="")
        sub = sub.row(align=True)
        sub.active = self.show_in_sidebar
        sub.prop(self, "sidebar_category", text="")



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    BoolToolPreferences,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)