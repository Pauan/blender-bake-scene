# Bake Scene

This add-on bakes your scene to textures. This is useful in many situations:

* Creating trim sheets
* Creating decals
* Creating hair cards
* Creating skyboxes
* Creating terrain

The textures are baked super fast, they are anti-aliased, and they are extremely high quality.


## Installation

1. Go to the [Releases page](https://github.com/Pauan/blender-bake-scene/releases) and download the most recent `Bake.Scene.zip` file.

2. In Blender, go to `Edit -> Preferences...`

3. In the `Add-ons` tab, click the `Install...` button.

4. Select the `Bake.Scene.zip` file and click `Install Add-on`.

5. Enable the checkbox to the left of `Render: Bake Scene`.

6. Save your preferences.


## How to use

1. In the `Output` properties, change the resolution. `2048` or `4096` is most common:

   ![][screenshot1]

2. Change the output folder and image settings to whatever you want, then click the `Bake` button:

   ![][screenshot2]

3. By default it will bake geometry textures (alpha, ambient occlusion, curvature, normal, and height).

   But you can change that inside of the `Textures` panel:

   ![][screenshot3]


## Tips and advice

* The textures created by this add-on can be directly used in DECALmachine.

* I recommend baking with 100% `Compression`. This slows down the baking, but it means much smaller file sizes.

* The origin point `(0x, 0y, 0z)` is always used as the center for the textures.

   The `Size` option specifies how big your scene is, anything outside of `Size` won't be baked.

   By default it bakes a `2m x 2m` box centered on the origin.

* If you want the texture files to have a prefix you can simply add it to the `Output` folder:

   ![][screenshot7]

* You can have multiple different scenes in the same `.blend` file, and each scene can have different options (output folder, textures, size, etc.)

* It will only bake renderable objects, so if you don't want to bake an object you can disable rendering:

   ![][screenshot8]

* If you use a `Principled BSDF` node it will be baked into the textures:

   ![][screenshot9]

   These sockets are supported: `Base Color`, `Metallic`, `Roughness`, `Emission`, `Alpha`, and `Normal`.

   It works with both simple values and also complex procedural node trees.

* If you are baking hair, you should set the `Hair Shape Type` setting to `Strip`:

   ![][screenshot6]

   You should also create your hairs with the highest quality possible. Because they are being baked to a texture, the performance doesn't matter.


## Texture Information

* `Alpha` bakes a black-and-white alpha / opacity / transparency texture.

   This is affected by changing the `Alpha` socket of the `Principled BSDF` node,
   and it is also affected by the `Blend Mode` settings (`Opaque`, `Alpha Clip`, `Alpha Hashed`, and `Alpha Blend`).

* `AO` bakes an ambient occlusion texture. White means no occlusion, and black means full occlusion.

   Ambient occlusion means how close an object is to another object. It is used to add in fake shadows.

* `Curvature` bakes a curvature map. Gray means no curvature, white means curving outwards (convex), and black means curving inwards (concave).

   This is often used to add extra detail to the edges of models (scratches, scuffs, or dirt).

* `Normal` bakes a normal map. This is affected by the `Normal` socket of the `Principled BSDF` node.

* `Height` bakes a height map. Gray means the geometry is at the center `0z`, white means positive `+z`, and black means negative `-z`.

   This can be used to create parallax effects to add extra depth, or to create bump maps.

   By default it calculates the max bounds automatically based on the vertexes in your scene. But you can instead choose `Manual` mode and
   then manually change the max bounds.

* `Color` bakes the `Base Color` socket of the `Principled BSDF` node.

* `Emission` bakes the `Emission` socket of the `Principled BSDF` node.

* `Metallic` bakes the `Metallic` socket of the `Principled BSDF` node.

* `Roughness` bakes the `Roughness` socket of the `Principled BSDF` node.

* `Object Random` bakes a black-and-white texture where every object is given a random grayscale color.

   This can be used for post-processing to mask out specific objects.

* `Object Index` bakes a black-and-white texture which is based on the object's `Pass Index`:

   ![][screenshot4]

   This can be used to mask out specific objects, or groups of objects.

   You must change the `Max` option to be the same as the biggest `Pass Index` that you are using.

* `Material Index` bakes a black-and-white texture which is based on the material's `Pass Index`:

   ![][screenshot5]

   This can be used to mask out specific materials, or groups of materials. This is particularly useful
   for DECALmachine's `Subset` map.

   You must change the `Max` option to be the same as the biggest `Pass Index` that you are using.

* `Hair Random` bakes a black-and-white texture where every particle hair strand is given a random grayscale color.

* `Hair Root` bakes a black-and-white texture where black means the root of the hair, and white means the tip of the hair.


[screenshot1]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%201.png
[screenshot2]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%202.png
[screenshot3]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%203.png
[screenshot4]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%204.png
[screenshot5]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%205.png
[screenshot6]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%206.png
[screenshot7]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%207.png
[screenshot8]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%208.png
[screenshot9]: https://github.com/Pauan/blender-bake-scene/raw/master/Screenshot%209.png


## For programmers

If you want to modify this add-on, follow these steps:

1. `git clone https://github.com/Pauan/blender-bake-scene.git`

2. `cd blender-bake-scene`

3. `blender --background --python install.py`

   This will install the add-on locally.

4. Now you can open Blender normally and the add-on will be installed.

5. When you make changes to the code, close Blender and then run `blender --background --python install.py` again.
