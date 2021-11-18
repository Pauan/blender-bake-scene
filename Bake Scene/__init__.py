# Copyright © 2021 Pauan
#
# This file is part of Bake Scene.
#
# Bake Scene is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bake Scene is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bake Scene.  If not, see <https://www.gnu.org/licenses/>.

# <pep8 compliant>

bl_info = {
    "name": "Bake Scene",
    "author": "Pauan",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Output Settings > Bake Scene",
    "description": "Bakes your entire scene into textures",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}

DEBUG = True

import bpy

from . import properties
from . import ui
from . import operators
from . import gizmos

classes = (
    properties.Scene,
    operators.CalculateMaxHeight,
    operators.ShowSize,
    operators.HideSize,
    operators.Bake,
    ui.BakePanel,
    ui.TexturesPanel,
    ui.TexturesGeometryPanel,
    ui.TexturesMaterialPanel,
    ui.TexturesMaskingPanel,
    ui.TexturesHairPanel,
    gizmos.BoxGizmo,
    gizmos.PlaneGizmo,
    gizmos.Gizmos,
)

def register():
    if DEBUG:
        import faulthandler
        faulthandler.enable()

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
