# ?? 3D ?????

## ??????

- `backend/data/avatar_3d_profile.json`
- `backend/data/virtual_space.json`
- `backend/app/avatar_3d_builder.py`
- `demos/YYYY-MM-DD/avatar_3d.json`

## ?????

1. `avatar_profile`
2. `virtual_space`
3. `runtime_state`
4. `animation_plan`
5. `navigation_points`
6. `space_storyboard`
7. `asset_requirements`

## ?????? 3D ??

1. ????????????
2. ????????????? blendshape?
3. ?? `idle_stand`?`wave`?`open_palm`?`checklist`?`point_screen`?`walk_to_owner`?
4. ? Unreal/Unity ???????????????????
5. ?? `avatar_3d.json`?? `space_storyboard` ?????? `animation_plan` ????????


## Browser 3D preview

The frontend now includes a local Three.js preview:

- `frontend/avatar3d_scene.js`
- `frontend/index.html` canvas: `#avatar3dCanvas`
- Three.js dependency: `three@0.165.0`

The preview reads the generated `avatar_3d` package from `output_bundle.json`, builds a small room, places navigation markers, and moves a low-poly full-body Sunguo placeholder along `space_storyboard`. This is not the final human model yet; it is the runtime proof that the model, route, and scene data can drive a 3D character.
