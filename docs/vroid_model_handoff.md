# VRoid to Sunguo model handoff

## Goal

Create the first full-body Sunguo prototype in VRoid Studio and export it as:

`frontend/assets/avatar/sunguo.vrm`

Once this file exists, the web dashboard will try to load it automatically in the Three.js scene.

## Suggested appearance

- Young warm female butler, around 18-year-old visual style
- Gentle, sunny, intelligent expression
- Dark brown long soft-layer hair with light bangs
- Light warm skin tone
- Mint / soft green home-assistant outfit
- Avoid highly exaggerated anime proportions for this prototype

## Export steps

1. Open VRoid Studio.
2. Create a new character.
3. Set body proportion close to natural full-body proportion.
4. Adjust face, eyes, hair, and outfit using the suggested appearance above.
5. Export as VRM.
6. Name the file exactly `sunguo.vrm`.
7. Put it in `frontend/assets/avatar/`.
8. Refresh `http://localhost:8765/frontend/`.

## Expected dashboard behavior

- Before `sunguo.vrm` exists: the dashboard shows the low-poly placeholder.
- After `sunguo.vrm` exists: the dashboard loads the VRM model and keeps the same route movement.

## Next engineering steps after first VRM loads

- Tune scale and ground contact.
- Add idle breathing animation.
- Add simple head/look-at behavior.
- Connect speech timeline to mouth expression.
- Prepare Blender cleanup pass for hair, outfit, and material quality.
