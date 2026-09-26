// Run with: wpscript.exe build-world.js <directory containing the map assets>
var File = Java.type('java.io.File');
var Point = Java.type('java.awt.Point');
var root = arguments.length ? String(arguments[0]) : '.';
function file(name) { return String(new File(root, name).getAbsolutePath()); }

var format = wp.getMapFormat().withId('org.pepsoft.anvil.1.20.5').go();
var heightMap = wp.getHeightMap().fromFile(file('heightmap.png')).go();
var testWorld = wp.createWorld().fromHeightMap(heightMap)
    .fromLevels(0, 65535).toLevels(0, 255)
    .withWaterLevel(62).withMapFormat(format)
    .withLowerBuildLimit(-64).withUpperBuildLimit(320).go();
testWorld.setName('Dwie gory i rzeka');
testWorld.setSpawnPoint(new Point(210, 425));

var terrainMask = wp.getHeightMap().fromFile(file('terrain-mask.png')).go();
wp.applyHeightMap(terrainMask).toWorld(testWorld).applyToTerrain()
    .fromLevel(0).toTerrain(0)
    .fromLevel(1).toTerrain(29)
    .fromLevel(2).toTerrain(36).go();

var frost = wp.getLayer().withName('Frost').go();
var frostMask = wp.getHeightMap().fromFile(file('frost-mask.png')).go();
wp.applyHeightMap(frostMask).toWorld(testWorld).applyToLayer(frost)
    .fromLevel(0).toLevel(0).fromLevel(255).toLevel(1).go();

var output = file('dwie-gory-rzeka.world');
wp.saveWorld(testWorld).toFile(output).go();
var loaded = wp.getWorld().fromFile(output).go();
print('Saved and reopened: ' + loaded.getName());
print('Dimensions: ' + loaded.getDimensions().size());
print('File: ' + output);
