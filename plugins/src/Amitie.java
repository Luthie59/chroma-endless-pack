package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.GameRule;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.World;
import org.bukkit.WorldCreator;
import org.bukkit.block.Biome;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerTeleportEvent;
import org.bukkit.generator.BiomeProvider;
import org.bukkit.generator.ChunkGenerator;
import org.bukkit.generator.WorldInfo;

import java.util.List;

/**
 * "L'Instant Éternel": a private void world frozen at sunset, holding the floating island built in tribute to the
 * friendship of Luthie59 & Margot59. Only holders of citadelle.amitie (granted per player) may enter, by /amitie.
 */
final class Amitie implements Listener, TabExecutor {

    static final String WORLD = "amitie";
    private static final String PERM = "citadelle.amitie";
    private static final long SUNSET = 12350L;
    private static final double VOID_RESCUE_Y = 40;
    private static final String P = "§d✿ §7";

    /** empty chunks: the island is placed as a structure. */
    private static final class VoidGenerator extends ChunkGenerator {
        @Override public boolean shouldGenerateNoise() { return false; }
        @Override public boolean shouldGenerateSurface() { return false; }
        @Override public boolean shouldGenerateCaves() { return false; }
        @Override public boolean shouldGenerateDecorations() { return false; }
        @Override public boolean shouldGenerateMobs() { return false; }
        @Override public boolean shouldGenerateStructures() { return false; }
        @Override public boolean shouldGenerateBedrock() { return false; }
    }

    private static final class CherrySky extends BiomeProvider {
        @Override public Biome getBiome(WorldInfo info, int x, int y, int z) { return Biome.CHERRY_GROVE; }
        @Override public List<Biome> getBiomes(WorldInfo info) { return List.of(Biome.CHERRY_GROVE); }
    }

    private final CitadelleMessages plugin;
    private World world;
    private float clockYaw;

    Amitie(CitadelleMessages plugin) {
        this.plugin = plugin;
        world = Bukkit.getWorld(WORLD);
        if (world == null) {
            world = new WorldCreator(WORLD).generator(new VoidGenerator()).biomeProvider(new CherrySky())
                    .generateStructures(false).keepSpawnInMemory(false).createWorld();
        }
        if (world == null) {
            plugin.getLogger().warning("Monde « " + WORLD + " » impossible à créer.");
            return;
        }
        world.setGameRule(GameRule.ADVANCE_TIME, false);
        world.setGameRule(GameRule.ADVANCE_WEATHER, false);
        world.setGameRule(GameRule.SPAWN_MOBS, false);
        world.setGameRule(GameRule.SPAWN_MONSTERS, false);
        world.setGameRule(GameRule.SPAWN_PHANTOMS, false);
        world.setGameRule(GameRule.SPAWN_PATROLS, false);
        world.setGameRule(GameRule.SPAWN_WANDERING_TRADERS, false);
        world.setTime(SUNSET);
        world.setStorm(false);
        world.setThundering(false);
        world.setSpawnLocation(arrival());
        Bukkit.getScheduler().runTaskTimer(plugin, this::ambience, 40L, 2L);
    }

    private Location arrival() {
        return new Location(world, plugin.getConfig().getDouble("amitie.arrivee.x", 22.5), plugin.getConfig().getDouble("amitie.arrivee.y", 121),
                plugin.getConfig().getDouble("amitie.arrivee.z", 0.5), (float) plugin.getConfig().getDouble("amitie.arrivee.yaw", 90), 0f);
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!(sender instanceof Player p)) { sender.sendMessage(P + "Commande en jeu uniquement."); return true; }
        if (!p.hasPermission(PERM) || world == null) { p.sendMessage(P + "Ce lieu n'existe que pour ceux qu'il attend."); return true; }
        if (args.length > 0 && args[0].equalsIgnoreCase("definir")) {
            if (p.getWorld() != world) { p.sendMessage(P + "Place-toi sur l'île pour choisir l'arrivée."); return true; }
            Location l = p.getLocation();
            plugin.getConfig().set("amitie.arrivee.x", l.getX());
            plugin.getConfig().set("amitie.arrivee.y", l.getY());
            plugin.getConfig().set("amitie.arrivee.z", l.getZ());
            plugin.getConfig().set("amitie.arrivee.yaw", (double) l.getYaw());
            plugin.saveConfig();
            world.setSpawnLocation(l);
            p.sendMessage(P + "Point d'arrivée enregistré.");
            return true;
        }
        p.teleport(arrival());
        p.sendTitle("§6§l✿ L'Instant Éternel ✿", "§dLuthie59 §7& §dMargot59", 20, 80, 30);
        p.playSound(p.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_RESONATE, 0.8f, 0.7f);
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        return sender.hasPermission(PERM) && args.length == 1 ? List.of("definir") : List.of();
    }

    /** nobody else gets in: any teleport into the world without the permission is refused. */
    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void onTeleport(PlayerTeleportEvent event) {
        if (world == null || event.getTo() == null || event.getTo().getWorld() != world) return;
        if (!event.getPlayer().hasPermission(PERM)) {
            event.setCancelled(true);
            event.getPlayer().sendMessage(P + "Ce lieu n'existe que pour ceux qu'il attend.");
        }
    }

    /** falling off the island never kills: back to the arrival point. */
    @EventHandler(ignoreCancelled = true)
    public void onFall(PlayerMoveEvent event) {
        if (world == null || event.getTo() == null || event.getTo().getWorld() != world || event.getTo().getY() > VOID_RESCUE_Y) return;
        Player p = event.getPlayer();
        p.setFallDistance(0f);
        Bukkit.getScheduler().runTask(plugin, () -> p.teleport(arrival()));
    }

    /** falling petals, sparkling stars, and the clock slowly turning on its pedestal. */
    private void ambience() {
        if (world == null || world.getPlayers().isEmpty()) return;
        clockYaw = (clockYaw + 2f) % 360f;
        for (Entity e : world.getEntities()) {
            if (e.getScoreboardTags().contains("amitie_horloge")) e.setRotation(clockYaw, 0f);
            else if (e.getScoreboardTags().contains("amitie_etoile")) {
                e.setRotation(-clockYaw, 0f);
                if (Math.random() < .25) world.spawnParticle(Particle.END_ROD, e.getLocation(), 1, .3, .3, .3, .01);
            }
        }
        Location arch = new Location(world, 0.5, 129, 0.5);
        world.spawnParticle(Particle.CHERRY_LEAVES, arch, 2, 4, 2, 7, 0);
        if (Math.random() < .08) world.spawnParticle(Particle.HEART, new Location(world, 1.5, 122.6, 0.5), 1, .4, .2, .6, 0);
    }
}
