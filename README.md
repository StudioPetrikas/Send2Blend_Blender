# "Send2Blend" Autodesk Fusion360 add-in

"Send2Blend" Autodesk Fusion360 add-in was creted to work in tandem with ["Send2Blend" Autodesk Fusion360 Add-In.](https://github.com/StudioPetrikas/Send2Blend_Fusion360)

*Disclaimer: 
The code has been pieced together by a beginner coder. There will be coding mistakes, logic mistakes, naming mistakes and various other problems with the code. Please be patient and feel free to make modifications to the code as you see fit.*

# Attribution
  - Martynas Žiemys has been comissioned to write the base "STL Import / Update" part of the code.

# Installation 
1. Download the [current release of Send2Blend for Blender](https://github.com/StudioPetrikas/Send2Blend_Blender/files/5112198/Send2Blend_Blender_V1.0.zip)
2. Open Blender
3. Navigate to Edit → Preferences
4. Select "Add-Ons" in the left-hand panel
5. Click "Install" (top-right)
6. Select the downloaded *.zip
7. Tick the tickbox next to "import: Send2Blend"
8. Close the Preferences window

# Usage
1. Make sure Autodesk Fusion360 is running
2. Use the "Send2Blend for Fusion360" add-in to export your design files
3. Open Blender and navigate to Tools tab on the "N" panel in "3D Viewport"
4. Click "Import / Update" top import your model into Blender. Alternatively, toggle "Run Live Update" to import models as they are exported from Fusion360.

Full workflow (Including Fusion360) can be found in this Youtube Video

# How it Works
1. Imports all and any .STL files in "S2B_Temp" folder on User/Desktop
2. If objects with the same name already exists in the scene, the plugin only updates the meshes, keeping the rest of the data (such as materials in tact)
3. "Live Update" checks the "S2B_Temp" folder every 4 seconds for changes, and imports all STL files in the folder if changes within the folder are detected

# Shortcomings
- Inability to use per-face materials. All per-face materials on the object will be discarded and only the first material in the list will be used.
- The plug-in does not remove objects in the scene that have been removed from Fusion360 design. This has to be done manually.
- Any per-face smoothing options will be discarded. Smoothing can only be controlled with "Auto-smooth angle"

# Troubleshooting
Avoid any errors by running Fusion360 first. Most errors will contain issues with the S2B_Temp folder, which is created when "Send2Blend" Fusion360 Add-In is first used.


