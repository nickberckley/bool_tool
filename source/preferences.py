import bpy
from . import ui


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_sidebar_category(self, context):
    """Change sidebar category of add-ons panel."""

    panel_classes = [
        ui.VIEW3D_PT_boolean,
        ui.VIEW3D_PT_boolean_helpers,
        ui.VIEW3D_PT_boolean_cutters,
    ]

    for cls in panel_classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
        cls.bl_category = self.sidebar_category
        bpy.utils.register_class(cls)



#### ------------------------------ PREFERENCES ------------------------------ ####

class BoolToolPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # UI
    category: bpy.props.EnumProperty(
        name = "Category",
        items = (('ADDON', "Add-on", "General add-on features"),
                 ('SHARED', "Shared", "Features shared by all of add-ons operators and tools"),
                 ('OPERATORS', "Boolean Operators", "Features for brush and auto Boolean operators")),
        default = 'OPERATORS'
    )

    show_in_sidebar: bpy.props.BoolProperty(
        name = "Show Add-on Panel in Sidebar",
        description = "Add a sidebar panel in 3D Viewport with add-ons operators and properties",
        default = True,
    )
    sidebar_category: bpy.props.StringProperty(
        name = "Category Name",
        description = "Sidebar category name. Using the name of the existing category will add the panel there",
        default = "Edit",
        update = update_sidebar_category,
    )

    # Defaults
    solver: bpy.props.EnumProperty(
        name = "Boolean Solver",
        description = "Which solver to use for automatic and brush Boolean operators",
        items = [('FLOAT', "Float", ""),
                 ('EXACT', "Exact", ""),
                 ('MANIFOLD', "Manifold", "")],
        default = 'FLOAT',
    )
    display: bpy.props.EnumProperty(
        name = "Cutter Display",
        items = (('WIRE', "Wire", "Display the cutter object as a wireframe"),
                 ('BOUNDS', "Bounds", "Display only the bounds of the cutter object")),
        default = 'BOUNDS'
    )
    show_in_editmode: bpy.props.BoolProperty(
        name = "Enable 'Show in Edit Mode' by Default",
        description = "Added Boolean modifiers will have 'Show in Edit Mode' enabled by default",
        default = True,
    )

    # Advanced
    use_collection: bpy.props.BoolProperty(
        name = "Put Cutters in Collection",
        description = ("Put all cutters in the same collection, and create one if it doesn't exist.\n"
                       "Useful for scene management, and quickly selecting and removing all clutter when needed"),
        default = True,
    )
    collection_name: bpy.props.StringProperty(
        name = "Collection Name",
        description = "Name of the collection where cutters will be added",
        default = "boolean_cutters",
    )
    parent: bpy.props.BoolProperty(
        name = "Parent Cutters to Object",
        description = ("Cutters will be parented to first canvas they're applied to.\n"
                       "Works best when one cutter is used on one canvas"),
        default = True,
    )
    apply_order: bpy.props.EnumProperty(
        name = "When Applying Cutters...",
        description = ("What happens when boolean cutters are applied on object.\n"
                       "Either when performing auto-boolean, using 'Apply All Cutters' operator.\n"
                       "NOTE: This doesn't apply to Carver tool on 'Destructive' mode; or when applying individual cutters"),
        items = (('ALL', "Apply All Modifiers", "All modifiers on object will be applied (this includes shape keys as well)"),
                 ('BEFORE', "Apply Booleans & Everything Before", "Alongside boolean modifiers all modifiers will be applied that come before the last boolean"),
                 ('BOOLEANS', "Only Apply Booleans", "Only apply boolean modifiers. This method will fail if object has shape keys")),
        default = 'ALL',
    )
    pin: bpy.props.BoolProperty(
        name = "Pin Boolean Modifiers",
        description = ("Place new Boolean modifiers above every other modifier on the object (if there are any).\n"
                       "NOTE: Order of modifiers can drastically affect the final result"),
        default = False,
    )

    # Features
    fast_modifier_apply: bpy.props.BoolProperty(
        name = "Faster Destructive Booleans",
        description = ("Experimental method of applying modifiers that results in 30-50% faster destructive booleans.\n"
                       "Performance improvements also affect add-ons operators that apply cutters.\n"
                       "However, changing modifier properties in the redo panel (like material transfer)\n"
                       "is not available for this method yet."),
        default = False,
    )
    double_click: bpy.props.BoolProperty(
        name = "Double-click Select",
        description = ("Select boolean cutters by double-clicking on the Boolean modifier.\n"
                       "Works in the entire modifier properties area, not just on boolean modifier header,\n"
                       "therefore can result in lot of misclicks and unintended selections."),
        default = False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # UI
        row = layout.row()
        row.prop(self, "category", expand=True)
        layout.separator()

        # Add-on Properties
        if self.category == 'ADDON':
            col = layout.column(align=True, heading="Show in Sidebar")
            row = col.row(align=True)
            sub = row.row(align=True)
            sub.prop(self, "show_in_sidebar", text="")
            sub = sub.row(align=True)
            sub.active = self.show_in_sidebar
            sub.prop(self, "sidebar_category", text="")

            col.separator()
            col = layout.column(align=True, heading="Features")
            col.prop(self, "fast_modifier_apply")
            col.prop(self, "double_click")

        # Shared Properties
        if self.category == 'SHARED':
            col = layout.column()
            col.prop(self, "show_in_editmode")
            col.prop(self, "apply_order")

        # Boolean Operator Properties
        if self.category == 'OPERATORS':
            col = layout.column(align=True, heading="Put Cutters in Collection")
            row = col.row(align=True)
            sub = row.row(align=True)
            sub.prop(self, "use_collection", text="")
            sub = sub.row(align=True)
            sub.active = self.show_in_sidebar
            sub.prop(self, "collection_name", text="", placeholder="boolean_cutters")

            col = layout.column()
            row = col.row(align=True)
            row.prop(self, "solver", text="Solver", expand=True)
            row = col.row(align=True)
            row.prop(self, "display", expand=True)

            col = layout.column()
            col.prop(self, "parent")
            col.prop(self, "pin")



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    BoolToolPreferences,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
