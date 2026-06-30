const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..");
const configPath = path.join(projectRoot, "frontend", "avatar_motion_clips.json");
const data = JSON.parse(fs.readFileSync(configPath, "utf8"));

const requiredClips = ["idle", "small_nod", "wave", "present_left", "point_screen", "checklist"];
const requiredDefaults = ["walkSpeedThreshold", "walkCycleSpeed", "breathSpeed"];
const requiredWalk = ["spineBase", "chestBase", "bodySwing", "armSwing", "legSwing", "kneeLift", "footLift", "bounce"];
const vectorFields = new Set([
  "chest", "head", "leftUpperArm", "rightUpperArm", "leftLowerArm", "rightLowerArm",
  "leftHand", "rightHand", "leftUpperLeg", "rightUpperLeg", "leftLowerLeg", "rightLowerLeg",
  "leftFoot", "rightFoot"
]);

const errors = [];
if (!data.version) errors.push("Missing version");
for (const key of requiredDefaults) {
  if (typeof data.defaults?.[key] !== "number") errors.push(`Missing numeric defaults.${key}`);
}
for (const key of requiredWalk) {
  if (typeof data.walk?.[key] !== "number") errors.push(`Missing numeric walk.${key}`);
}
for (const clipName of requiredClips) {
  const clip = data.clips?.[clipName];
  if (!clip) {
    errors.push(`Missing clip ${clipName}`);
    continue;
  }
  for (const [field, value] of Object.entries(clip)) {
    if (!vectorFields.has(field)) continue;
    if (!Array.isArray(value) || value.length !== 3 || value.some((item) => typeof item !== "number")) {
      errors.push(`Clip ${clipName}.${field} must be a 3-number array`);
    }
  }
}

if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}
console.log(`Motion config OK: ${data.version}, ${Object.keys(data.clips || {}).length} clips`);
