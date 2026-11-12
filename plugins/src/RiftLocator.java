package fr.citadelle.messages;

import org.bukkit.HeightMap;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Tag;
import org.bukkit.World;
import org.bukkit.block.Block;

import java.util.Random;

/** Picks a dry, unclaimed surface spot in a ring around the spawn (0,0). */
final class RiftLocator {

    private static final int ATTEMPTS = 60;
    private static final int GENERATED_ONLY_ATTEMPTS = 40;   // prefer already generated chunks (no lag spike)
    private static final int CLAIM_CHUNK_RADIUS = 2;

    private RiftLocator() { }

    static Location find(World world, RiftConfig cfg, FactionBridge factions, Random rnd) {
        for (int i = 0; i < ATTEMPTS; i++) {
            double angle = rnd.nextDouble() * Math.PI * 2;
            double dist = cfg.minDistance() + rnd.nextDouble() * (cfg.maxDistance() - cfg.minDistance());
            int x = (int) Math.round(Math.cos(angle) * dist);
            int z = (int) Math.round(Math.sin(angle) * dist);
            if (i < GENERATED_ONLY_ATTEMPTS && !world.isChunkGenerated(x >> 4, z >> 4)) continue;
            Location candidate = surface(world, x, z);
            if (candidate == null) continue;
            if (!world.getWorldBorder().isInside(candidate)) continue;
            if (factions.isClaimedAround(candidate, CLAIM_CHUNK_RADIUS)) continue;
            return candidate;
        }
        return null;
    }

    /** standing spot above the highest solid, non-liquid block, or null. */
    static Location surface(World world, int x, int z) {
        Block ground = world.getHighestBlockAt(x, z, HeightMap.MOTION_BLOCKING_NO_LEAVES);
        Material m = ground.getType();
        if (ground.isLiquid() || m == Material.ICE || m == Material.PACKED_ICE || m == Material.BLUE_ICE
                || m == Material.LAVA || m == Material.POWDER_SNOW || m == Material.CACTUS || m == Material.MAGMA_BLOCK) {
            return null;
        }
        if (Tag.LOGS.isTagged(m) || Tag.LEAVES.isTagged(m) || m == Material.BAMBOO
                || m == Material.BROWN_MUSHROOM_BLOCK || m == Material.RED_MUSHROOM_BLOCK || m == Material.MUSHROOM_STEM) {
            return null;                                  // tree tops are not ground
        }
        if (ground.getY() <= world.getMinHeight() + 1) return null;
        return ground.getLocation().add(0.5, 1, 0.5);
    }

    /** "au nord-est" style direction of (x,z) as seen from the spawn. */
    static String direction(double x, double z) {
        String[] names = {"à l'est", "au sud-est", "au sud", "au sud-ouest", "à l'ouest", "au nord-ouest", "au nord", "au nord-est"};
        double deg = Math.toDegrees(Math.atan2(z, x));           // Minecraft: +x east, +z south
        int idx = (int) Math.round(((deg + 360) % 360) / 45.0) % 8;
        return names[idx];
    }
}
